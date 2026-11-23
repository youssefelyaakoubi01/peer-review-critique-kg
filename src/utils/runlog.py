"""Per-run logging: every script execution writes a timestamped file in logs/."""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_run_logging(run_name: str, log_dir: str | Path) -> logging.Logger:
    """Return a logger writing to stdout and to logs/<run_name>_<timestamp>.log."""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{run_name}_{stamp}.log"

    logger = logging.getLogger(run_name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(log_file)):
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    logger.info("run=%s log_file=%s", run_name, log_file)
    logger.info("command=%s", " ".join(sys.argv))
    return logger
