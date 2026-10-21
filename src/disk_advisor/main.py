import argparse
from pathlib import Path

from .classifier import refine_risk
from .reporter import build_report
from .scanner import scan_tree


def main() -> None:
    ap = argparse.ArgumentParser(description="磁盘清理顾问（只读扫描）")
    ap.add_argument("--root", default="C:\\")
    ap.add_argument("--min-large-mb", type=int, default=500)
    ap.add_argument("--output", default="disk_report.md")
    args = ap.parse_args()

    records = [
        refine_risk(r)
        for r in scan_tree(
            args.root,
            args.min_large_mb * 1024 * 1024,
            report_junk_files=True,
        )
    ]
    Path(args.output).write_text(build_report(records), encoding="utf-8")
    print(f"报告已生成：{args.output}")


if __name__ == "__main__":
    main()
