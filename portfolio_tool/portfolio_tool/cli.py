from __future__ import annotations

import argparse
from pathlib import Path

from .main import run_study
from .persistence import list_studies, load_study
from .utils import normalize_tickers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portfolio Tool CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run a portfolio study")
    run.add_argument("--tickers", required=True, help="Comma-separated tickers")
    run.add_argument("--period", default="5y")
    run.add_argument("--log-returns", action="store_true")
    run.add_argument("--risk-free", type=float, default=0.0)
    run.add_argument("--mc-sims", type=int, default=20000)
    run.add_argument("--allow-short", action="store_true")
    run.add_argument("--study-name", default="study")

    sub.add_parser("list-studies", help="List saved studies")

    load = sub.add_parser("load", help="Load a study")
    load.add_argument("--study", required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    base_dir = Path.cwd()

    if args.command == "run":
        config = {
            "tickers": normalize_tickers(args.tickers),
            "period": args.period,
            "log_returns": args.log_returns,
            "risk_free_rate": args.risk_free,
            "mc_sims": args.mc_sims,
            "allow_short": args.allow_short,
            "study_name": args.study_name,
            "base_dir": str(base_dir),
        }
        result = run_study(config)
        print("Study completed")
        print("Tickers:", ", ".join(result["tickers"]))
        print("Report:", result["report_paths"].get("excel"))

    elif args.command == "list-studies":
        studies_dir, studies = list_studies(base_dir)
        print("Studies in", studies_dir)
        for s in studies:
            print("-", s)

    elif args.command == "load":
        info = load_study(base_dir, args.study)
        print("Loaded", args.study)
        print(info)


if __name__ == "__main__":
    main()
