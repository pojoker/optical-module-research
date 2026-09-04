from __future__ import annotations

import argparse
from pathlib import Path

from .core import combine_daily_reports, publish_daily_artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m daily_intelligence",
        description="Combine domestic and overseas mirror output without promoting candidates.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    combine = subparsers.add_parser("combine", help="write one Markdown and JSON daily overview")
    combine.add_argument("--date", required=True, help="run date in YYYY-MM-DD form")
    combine.add_argument("--domestic-state-root", required=True, type=Path)
    combine.add_argument("--overseas-state-root", required=True, type=Path)
    combine.add_argument("--output-root", required=True, type=Path)
    publish = subparsers.add_parser(
        "publish",
        help="publish the accepted domestic TXT and overseas HTML verbatim behind one index",
    )
    publish.add_argument("--date", required=True, help="run date in YYYY-MM-DD form")
    publish.add_argument("--domestic-txt", required=True, type=Path)
    publish.add_argument("--overseas-html", required=True, type=Path)
    publish.add_argument("--output-root", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "publish":
        result = publish_daily_artifacts(
            run_date=args.date,
            domestic_txt=args.domestic_txt,
            overseas_html=args.overseas_html,
            output_root=args.output_root,
        )
        print(f"OK: published original artifacts {args.date} -> {result['index_path']}")
    else:
        result = combine_daily_reports(
            run_date=args.date,
            domestic_state_root=args.domestic_state_root,
            overseas_state_root=args.overseas_state_root,
            output_root=args.output_root,
        )
        print(
            f"OK: combined daily {args.date}: {result['assembly_status']} -> "
            f"{result['markdown_path']}"
        )
    return 0
