import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from .rules import HARD_EXCLUDE_NAMES


@dataclass
class FileRecord:
    path: str
    size: int
    category: str  # "large" | "junk"
    risk: str  # "green" | "yellow" | "red"
    matched_rule: str


def should_skip(entry: os.DirEntry[str]) -> bool:
    if entry.name in HARD_EXCLUDE_NAMES:
        return True
    try:
        if entry.is_symlink():
            return True
    except OSError:
        return True
    return False


def scan_tree(
    root: str,
    min_large_size: int = 500 * 1024 * 1024,
    follow_symlinks: bool = False,
    report_junk_files: bool = False,
) -> Iterator[FileRecord]:
    junk_dir_names = {"temp", "cache", "code cache", "gpucache", "__pycache__"}
    stack = [Path(root)]

    while stack:
        current = stack.pop()
        in_junk_dir = current.name.lower() in junk_dir_names

        try:
            entries = list(os.scandir(current))
        except (PermissionError, FileNotFoundError, NotADirectoryError):
            continue

        for entry in entries:
            if should_skip(entry):
                continue
            try:
                if entry.is_dir(follow_symlinks=follow_symlinks):
                    stack.append(Path(entry.path))
                    continue
            except OSError:
                continue
            if not entry.is_file(follow_symlinks=follow_symlinks):
                continue
            try:
                size = entry.stat(follow_symlinks=False).st_size
            except OSError:
                continue

            if in_junk_dir and report_junk_files:
                yield FileRecord(
                    path=entry.path,
                    size=size,
                    category="junk",
                    risk="green",
                    matched_rule=f"under:{current.name}",
                )
            elif size >= min_large_size:
                yield FileRecord(
                    path=entry.path,
                    size=size,
                    category="large",
                    risk="yellow",
                    matched_rule=f"size>={min_large_size}",
                )
