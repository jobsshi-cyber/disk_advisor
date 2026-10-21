# reporter.py
from collections import defaultdict
from pathlib import Path

from .rules import MIGRATION_STRATEGY
from .scanner import FileRecord


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def build_report(records: list[FileRecord]) -> str:
    greens = [r for r in records if r.risk == "green"]
    migratable = [r for r in records if r.matched_rule.startswith("migratable:")]
    unknown_large = [
        r for r in records if r.category == "large" and r.matched_rule == "large_unknown_type"
    ]

    lines = ["# 磁盘扫描报告（只读，未执行任何删除/迁移）\n"]

    # ========== 绿灯 ==========
    total_green = human_size(sum(r.size for r in greens))
    lines.append(f"## 一、可安全清理的垃圾（绿灯）  合计 {total_green}\n")
    by_rule: dict[str, dict[str, int]] = defaultdict(lambda: {"size": 0, "count": 0})
    for r in greens:
        by_rule[r.matched_rule]["size"] += r.size
        by_rule[r.matched_rule]["count"] += 1
    for rule, stat in sorted(by_rule.items(), key=lambda x: -x[1]["size"]):
        lines.append(f"- **{rule}**：{stat['count']} 项，{human_size(stat['size'])}")
    lines.append(
        "\n> 这些路径属于系统或软件运行中产生的临时数据，清理后通常会自动重建。"
        "建议关闭相关程序后再清理浏览器缓存。\n"
    )

    # ========== 可迁移大文件 ==========
    total_migratable = human_size(sum(r.size for r in migratable))
    lines.append(f"## 二、建议迁移而非删除的大文件  合计 {total_migratable}\n")
    for r in sorted(migratable, key=lambda x: -x.size):
        ext = Path(r.path).suffix.lower()
        strategy = MIGRATION_STRATEGY.get(ext, "可直接剪切到其他盘")
        lines.append(f"- `{r.path}`  **{human_size(r.size)}**  \n  → {strategy}")
    lines.append(
        "\n> **迁移通用步骤**：① 关闭所有可能占用该文件的程序；"
        "② 复制（不是剪切）到目标盘；③ 校验文件数量和大小一致；"
        "④ 确认无误后删除 C 盘原文件。"
        "如果迁移的是软件会主动访问的目录，而不是普通资料文件，"
        "必须用 `mklink /J` 在原路径创建目录联接，否则软件会找不到文件。\n"
    )

    # ========== 未知大文件 ==========
    total_unknown = human_size(sum(r.size for r in unknown_large))
    lines.append(f"## 三、需要你自行判断的大文件  合计 {total_unknown}\n")
    lines.append(
        "以下文件体积较大，但不属于可自动判断的类型。**程序不给出迁移建议**，"
        "因为它们可能是软件数据库、工作库或配置依赖文件。\n"
    )
    for r in sorted(unknown_large, key=lambda x: -x.size):
        lines.append(
            f"- `{r.path}`  **{human_size(r.size)}**  \n"
            f"  属于未知类型，迁移前请在对应软件中检查是否有“更改存储位置”的设置。"
        )

    return "\n".join(lines)
