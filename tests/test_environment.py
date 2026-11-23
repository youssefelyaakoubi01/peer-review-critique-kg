"""PyTorch Geometric must be importable and able to run a heterogeneous layer."""

import pytest
import torch
from torch_geometric.data import HeteroData
from torch_geometric.loader import NeighborLoader
from torch_geometric.nn import HeteroConv, SAGEConv

from src.utils.seed import set_seed


def make_graph() -> HeteroData:
    data = HeteroData()
    data["paper"].x = torch.randn(20, 8)
    data["review"].x = torch.randn(60, 8)
    src = torch.arange(60)
    dst = torch.randint(0, 20, (60,))
    data["review", "evaluates", "paper"].edge_index = torch.stack([src, dst])
    data["paper", "rev_evaluates", "review"].edge_index = torch.stack([dst, src])
    return data


def forward(data: HeteroData, device: str) -> torch.Tensor:
    conv = HeteroConv({et: SAGEConv((-1, -1), 4) for et in data.edge_types}).to(device)
    data = data.to(device)
    return conv(data.x_dict, data.edge_index_dict)["paper"]


def test_hetero_forward_cpu():
    assert forward(make_graph(), "cpu").shape == (20, 4)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA device available")
def test_hetero_forward_gpu():
    out = forward(make_graph(), "cuda:0")
    assert out.is_cuda and out.shape == (20, 4)


def test_neighbor_loader_on_hetero_graph():
    """Heterogeneous neighbour sampling needs the compiled pyg-lib extension."""
    loader = NeighborLoader(
        make_graph(), num_neighbors=[3], batch_size=5, input_nodes=("paper", None)
    )
    batch = next(iter(loader))
    assert batch["paper"].batch_size == 5


def test_set_seed_is_reproducible():
    set_seed(0)
    a = torch.randn(5)
    set_seed(0)
    b = torch.randn(5)
    assert torch.equal(a, b)
