"""Gradient attributions of the critique features, with captum.

The features of every critique node of the neighbourhood are the inputs; the other
features are constants. Attribution of a critique = sum over its feature columns.
Integrated gradients start from a zero baseline (the training mean of the text
embedding, no label): the attributions then sum to the logit minus the logit with all
critique features at zero.
"""

import numpy as np
import torch
from captum.attr import InputXGradient, IntegratedGradients

from src.explain import subgraph
from src.explain.subgraph import Neighbourhood

METHODS = ("input_x_gradient", "integrated_gradients")


def critique_attributions(model: torch.nn.Module, hood: Neighbourhood, method: str, steps: int = 20) -> np.ndarray:
    """Attribution of each critique node of the neighbourhood (use `hood.critiques` to
    read those of the article)."""
    if method not in METHODS:
        raise ValueError(f"unknown attribution method: {method!r}")

    def forward(critique_x: torch.Tensor) -> torch.Tensor:  # captum wants a batch dimension
        return subgraph.logit(model, hood, x={**hood.x, "critique": critique_x.squeeze(0)}).view(1)

    inputs = hood.x["critique"].unsqueeze(0)
    if method == "input_x_gradient":
        attribution = InputXGradient(forward).attribute(inputs)
    else:  # one interpolation step per forward pass: the nodes are not a batch
        attribution = IntegratedGradients(forward).attribute(inputs, baselines=torch.zeros_like(inputs), n_steps=steps,
                                                             internal_batch_size=1)
    return attribution.squeeze(0).sum(dim=1).detach().numpy().astype(float)
