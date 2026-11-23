"""Training loop shared by the neural models: full batch, class-weighted loss, early
stopping on the validation AUC.

A model maps its inputs to one logit per row. Only the training rows enter the loss;
the validation rows are only used to choose the epoch that is kept.
"""

import copy
import time
from dataclasses import dataclass

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from torch import nn


@dataclass
class Fit:
    best_epoch: int
    best_val_auc: float
    epochs: int
    seconds: float


def positive_weight(labels: torch.Tensor) -> torch.Tensor:
    """Weight of the positive class that gives both classes the same total weight."""
    positives = labels.sum()
    return (len(labels) - positives) / positives


def fit(model: nn.Module, inputs: tuple, labels: torch.Tensor, train_rows: torch.Tensor, val_rows: torch.Tensor,
        lr: float, weight_decay: float, max_epochs: int, patience: int) -> Fit:
    """Train `model` in place and leave it at its best validation epoch."""
    start = time.time()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_function = nn.BCEWithLogitsLoss(pos_weight=positive_weight(labels[train_rows]))
    val_labels = labels[val_rows].cpu().numpy()
    best_auc, best_epoch, best_state, epoch = -1.0, 0, None, 0
    for epoch in range(1, max_epochs + 1):
        model.train()
        optimiser.zero_grad()
        loss = loss_function(model(*inputs)[train_rows], labels[train_rows])
        loss.backward()
        optimiser.step()
        auc = roc_auc_score(val_labels, predict(model, inputs)[val_rows.cpu().numpy()])
        if auc > best_auc:
            best_auc, best_epoch, best_state = auc, epoch, copy.deepcopy(model.state_dict())
        elif epoch - best_epoch >= patience:
            break
    model.load_state_dict(best_state)
    return Fit(best_epoch, float(best_auc), epoch, time.time() - start)


@torch.no_grad()
def predict(model: nn.Module, inputs: tuple) -> np.ndarray:
    """Probability of acceptance of each row."""
    model.eval()
    return torch.sigmoid(model(*inputs)).float().cpu().numpy()
