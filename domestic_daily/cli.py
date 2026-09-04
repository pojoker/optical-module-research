import argparse
from .core import DailyMirror, RequestsClient


def main(argv=None):
    parser = argparse.ArgumentParser(description="运行隔离的国内日更镜像")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--source-root", required=True)
    run.add_argument("--state-root", required=True)
    run.add_argument("--date", required=True, dest="run_date")
    args = parser.parse_args(argv)
    if args.command == "run":
        result = DailyMirror(args.source_root, args.state_root, RequestsClient(args.source_root)).run(args.run_date)
        print(f"日报: {result['daily_path']}")
        print(f"manifest: {result['manifest_path']}")
        return 0
    return 2
