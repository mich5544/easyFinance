from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from .utils import ensure_dir, get_logger

logger = get_logger()


def study_dir(base_dir: Path, study_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "_".join(study_name.strip().split()) or "study"
    return ensure_dir(base_dir / "studies" / f"{safe_name}_{timestamp}")


def save_study(
    base_dir: Path,
    study_name: str,
    config: Dict,
    data: Dict,
    outputs: Dict,
    output_dir: Path | None = None,
) -> Path:
    root = output_dir or study_dir(base_dir, study_name)
    figures_dir = ensure_dir(root / "figures")

    (root / "config.json").write_text(json.dumps(config, indent=2), encoding="ascii")

    if "prices" in data:
        data["prices"].to_csv(root / "prices.csv")
    if "returns" in data:
        data["returns"].to_csv(root / "returns.csv")
    if "cov" in data:
        data["cov"].to_csv(root / "covariance.csv")
    if "corr" in data:
        data["corr"].to_csv(root / "correlation.csv")
    if "frontier_weights" in data and data["frontier_weights"]:
        fw_path = Path(data["frontier_weights"])
        if fw_path.exists():
            target = root / fw_path.name
            if fw_path != target:
                target.write_bytes(fw_path.read_bytes())

    summary = {
        "tickers": config.get("tickers", []),
        "period": config.get("period"),
        "log_returns": config.get("log_returns"),
        "risk_free_rate": config.get("risk_free_rate"),
        "allow_short": config.get("allow_short"),
        "min_variance": outputs.get("min_variance", {}),
        "max_sharpe": outputs.get("max_sharpe", {}),
        "risk_metrics": outputs.get("risk_metrics", {}),
    }
    (root / "study.json").write_text(json.dumps(summary, indent=2), encoding="ascii")

    for name, path in outputs.get("figures", {}).items():
        if path and Path(path).exists():
            target = figures_dir / Path(path).name
            if Path(path) != target:
                target.write_bytes(Path(path).read_bytes())

    if "excel" in outputs and outputs["excel"]:
        excel_path = Path(outputs["excel"])
        if excel_path.exists():
            target = root / excel_path.name
            if excel_path != target:
                target.write_bytes(excel_path.read_bytes())

    logger.info("Study saved at %s", root)
    return root


def list_studies(base_dir: Path) -> Tuple[Path, list[str]]:
    studies_dir = ensure_dir(base_dir / "studies")
    items = sorted([p.name for p in studies_dir.iterdir() if p.is_dir()], reverse=True)
    return studies_dir, items


def load_study(base_dir: Path, name: str) -> Dict:
    path = base_dir / "studies" / name
    if not path.exists():
        raise FileNotFoundError(f"Study not found: {name}")
    config = json.loads((path / "config.json").read_text(encoding="ascii"))
    study = json.loads((path / "study.json").read_text(encoding="ascii"))
    return {"path": str(path), "config": config, "summary": study}
