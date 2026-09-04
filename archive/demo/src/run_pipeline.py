#!/usr/bin/env python3
"""Run the demo extraction, Stage3 edge generation, and visualization pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the supply-chain graph demo pipeline.")
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    return parser.parse_args()


def run_stage(name: str, command: list[str], products: list[Path]) -> int:
    print(f"[{name}] starting", flush=True)
    started = time.perf_counter()
    result = subprocess.run(command, check=False)
    elapsed = time.perf_counter() - started
    product_text = ", ".join(str(path) for path in products)
    print(f"[{name}] elapsed: {elapsed:.3f}s; products: {product_text}", flush=True)
    if result.returncode != 0:
        print(
            f"[{name}] failed with exit code {result.returncode}; pipeline stopped",
            file=sys.stderr,
        )
    return result.returncode


def main() -> int:
    args = parse_args()
    src_dir = Path(__file__).resolve().parent
    scripts = {
        "extract_tables": src_dir / "extract_tables.py",
        "build_edges": src_dir / "build_edges.py",
        "make_graph": src_dir / "make_graph.py",
    }
    missing = [path for path in scripts.values() if not path.is_file()]
    if missing:
        for path in missing:
            print(f"run_pipeline.py: required stage script not found: {path}", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    extracted = args.out_dir / "extracted.json"
    edges = args.out_dir / "edges.csv"
    nodes = args.out_dir / "nodes.csv"
    graph = args.out_dir / "graph.html"

    stages = [
        (
            "extract_tables",
            [
                sys.executable,
                str(scripts["extract_tables"]),
                "--data-dir",
                str(args.data_dir),
                "--out",
                str(extracted),
            ],
            [extracted],
        ),
        (
            "build_edges",
            [
                sys.executable,
                str(scripts["build_edges"]),
                "--extracted",
                str(extracted),
                "--out-edges",
                str(edges),
                "--out-nodes",
                str(nodes),
            ],
            [edges, nodes],
        ),
        (
            "make_graph",
            [
                sys.executable,
                str(scripts["make_graph"]),
                "--edges",
                str(edges),
                "--nodes",
                str(nodes),
                "--out",
                str(graph),
            ],
            [graph],
        ),
    ]

    for name, command, products in stages:
        return_code = run_stage(name, command, products)
        if return_code != 0:
            return return_code
    print(f"pipeline complete: {graph}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
