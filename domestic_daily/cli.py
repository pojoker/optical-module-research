import argparse
from .core import DailyMirror, RequestsClient

# 完成=0；局部失败(partial)=1；未产出日报(failed)=2。
STATUS_EXIT = {"complete": 0, "partial": 1, "failed": 2}


def main(argv=None):
    parser = argparse.ArgumentParser(description="运行隔离的国内日更镜像")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--source-root", required=True)
    run.add_argument("--state-root", required=True)
    run.add_argument("--date", required=True, dest="run_date")
    run.add_argument("--backfill-since", dest="backfill_since", default=None,
                     help="忽略互动易成功水位，从该日期起回填（YYYY-MM-DD），仅用于补历史")
    run.add_argument("--qa-timeout", type=float, default=60, help="每家公司问答抓取墙钟预算（秒，默认60）")
    args = parser.parse_args(argv)
    if args.command == "run":
        result = DailyMirror(args.source_root, args.state_root, RequestsClient(args.source_root), qa_timeout=args.qa_timeout).run(
            args.run_date, backfill_since=args.backfill_since)
        status = result["manifest"].get("run_status") or "complete"
        print(f"日报: {result['daily_path']}")
        print(f"manifest: {result['manifest_path']}")
        print(f"运行状态: {status}")
        for line in (result["manifest"].get("errors") or [])[:10]:
            print(f"  失败: {line}")
        return STATUS_EXIT.get(status, 2)
    return 2
