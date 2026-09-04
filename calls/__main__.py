"""Command line entry: python3 -m calls {check,render,all}."""

from __future__ import annotations

import argparse
from pathlib import Path

from .renderer import render
from .validator import ValidationError, validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and render the overseas calls intelligence ledger")
    parser.add_argument("command", choices=("check", "render", "all"), nargs="?", default="all")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        if args.command in {"check", "all", "render"}:
            for message in validate(root):
                print(f"OK: {message}")
        if args.command in {"render", "all"}:
            paths = render(root)
            print(f"OK: rendered {len(paths)} files under calls/out")
    except (ValidationError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
