import argparse

from .classifier import refine_risk
from .reporter import write_html_report
from .scanner import scan_tree


def main() -> None:
    parser = argparse.ArgumentParser(description="磁盘清理顾问")
    parser.add_argument("--root", help="扫描根目录 (如果提供此项，将执行无界面静默扫描)")
    parser.add_argument("--min-large-mb", type=int, default=500, help="大文件阈值(MB)")
    parser.add_argument("--output", default="disk_report.html", help="报告输出路径")
    args = parser.parse_args()

    # 如果传了 --root，走命令行静默模式（适合高级用户或自动化）
    if args.root:
        print(f"正在扫描: {args.root} ...")
        records = [
            refine_risk(r)
            for r in scan_tree(args.root, args.min_large_mb * 1024 * 1024, report_junk_files=True)
        ]
        write_html_report(records, args.output)
        print(f"扫描完成，报告已生成：{args.output}")
    else:
        # 否则，默认启动图形界面
        from .gui import start_gui

        start_gui()


if __name__ == "__main__":
    main()
