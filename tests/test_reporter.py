from disk_advisor.reporter import human_size


def test_human_size_units() -> None:
    assert human_size(0) == "0.0 B"
    assert human_size(1024) == "1.0 KB"
    assert human_size(1024**3) == "1.0 GB"
