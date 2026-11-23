"""Phase 0: check the environment (package versions, GPU, PyTorch Geometric).

Usage: uv run python scripts/00_check_env.py
Exits with a non-zero status if a check fails.
"""

import platform
import sys
from importlib.metadata import version

import torch
from torch_geometric.data import HeteroData
from torch_geometric.loader import NeighborLoader
from torch_geometric.nn import HeteroConv, SAGEConv

from src.utils.config import load_config
from src.utils.runlog import setup_run_logging
from src.utils.seed import set_seed

PACKAGES = [
    "torch",
    "torch-geometric",
    "pyg-lib",
    "sentence-transformers",
    "transformers",
    "captum",
    "openreview-py",
    "pandas",
    "pyarrow",
    "numpy",
    "rdflib",
    "scikit-learn",
    "matplotlib",
    "pyyaml",
    "pytest",
]


def toy_hetero_graph() -> HeteroData:
    """Small random paper-review graph, only used to exercise PyG."""
    data = HeteroData()
    data["paper"].x = torch.randn(50, 16)
    data["review"].x = torch.randn(200, 16)
    src = torch.arange(200)
    dst = torch.randint(0, 50, (200,))
    data["review", "evaluates", "paper"].edge_index = torch.stack([src, dst])
    data["paper", "rev_evaluates", "review"].edge_index = torch.stack([dst, src])
    return data


def hetero_forward(data: HeteroData, device: torch.device) -> torch.Tensor:
    conv = HeteroConv(
        {edge_type: SAGEConv((-1, -1), 8) for edge_type in data.edge_types}, aggr="sum"
    ).to(device)
    data = data.to(device)
    return conv(data.x_dict, data.edge_index_dict)["paper"]


def main() -> int:
    cfg = load_config()
    log = setup_run_logging("00_check_env", cfg["paths"]["logs"])
    set_seed(cfg["seeds"][0])

    log.info("python=%s platform=%s", platform.python_version(), platform.platform())
    for pkg in PACKAGES:
        log.info("%s==%s", pkg, version(pkg))

    cuda = torch.cuda.is_available()
    log.info("torch.cuda.is_available()=%s", cuda)
    if cuda:
        props = torch.cuda.get_device_properties(0)
        log.info(
            "gpu=%s memory_gb=%.1f torch_cuda=%s cudnn=%s",
            props.name,
            props.total_memory / 1024**3,
            torch.version.cuda,
            torch.backends.cudnn.version(),
        )
    else:
        log.warning("no GPU detected: training will run on CPU")

    data = toy_hetero_graph()

    out = hetero_forward(data.clone(), torch.device("cpu"))
    log.info("hetero forward on cpu OK, output shape=%s", tuple(out.shape))
    if cuda:
        out = hetero_forward(data.clone(), torch.device("cuda:0"))
        log.info("hetero forward on %s OK, output shape=%s", out.device, tuple(out.shape))

    # NeighborLoader on a heterogeneous graph requires pyg-lib.
    loader = NeighborLoader(
        data, num_neighbors=[5], batch_size=10, input_nodes=("paper", None), shuffle=False
    )
    batch = next(iter(loader))
    log.info(
        "NeighborLoader OK: batch has %d papers, %d reviews",
        batch["paper"].num_nodes,
        batch["review"].num_nodes,
    )

    log.info("environment check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
