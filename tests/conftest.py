from pathlib import Path

import pytest


@pytest.fixture
def fake_tree(tmp_path: Path) -> Path:
    (tmp_path / "Temp").mkdir()
    (tmp_path / "Temp" / "a.tmp").write_bytes(b"x" * 1024)
    (tmp_path / "movie.mkv").write_bytes(b"x" * 2048)
    return tmp_path
