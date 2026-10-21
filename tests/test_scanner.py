from pathlib import Path

from disk_advisor.scanner import scan_tree


def test_scan_finds_large_file(fake_tree: Path) -> None:
    records = list(scan_tree(str(fake_tree), min_large_size=1024))
    assert any("movie.mkv" in r.path for r in records)


def test_scan_skips_hard_excluded(tmp_path: Path) -> None:
    (tmp_path / "System32").mkdir()
    (tmp_path / "System32" / "kernel.dll").write_bytes(b"x" * 4096)
    records = list(scan_tree(str(tmp_path), min_large_size=1))
    assert all("System32" not in r.path for r in records)
