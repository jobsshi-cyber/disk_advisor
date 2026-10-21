# classifier.py
from pathlib import Path

from .rules import MIGRATION_STRATEGY, YELLOW_NAMES
from .scanner import FileRecord


def refine_risk(record: FileRecord) -> FileRecord:
    path = Path(record.path)
    parts = {p.lower() for p in path.parts}

    # 在 Temp/Cache 目录下的大文件 → 仍然绿灯垃圾
    if "temp" in parts or "cache" in parts:
        record.category = "junk"
        record.risk = "green"
        record.matched_rule = "under_temp_or_cache"
        return record

    # 提前判断扩展名是否可迁移
    ext = path.suffix.lower()
    is_migratable = record.category == "large" and ext in MIGRATION_STRATEGY

    # 黄灯目录中的大文件 → 不自动建议删除，只报告
    if any(name.lower() in parts for name in YELLOW_NAMES):
        record.risk = "yellow"
        if is_migratable:
            record.matched_rule = f"migratable:{ext}"
        else:
            record.matched_rule = "in_user_data_dir"
        return record

    # 可迁移类型 → 给出迁移建议，而不是删除建议
    if record.category == "large" and record.risk == "yellow":
        if is_migratable:
            record.matched_rule = f"migratable:{ext}"
        else:
            record.matched_rule = "large_unknown_type"

    return record
