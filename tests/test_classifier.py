from disk_advisor.classifier import refine_risk
from disk_advisor.scanner import FileRecord


def test_junk_under_temp_stays_green() -> None:
    rec = FileRecord(
        path=r"C:\Users\x\AppData\Local\Temp\big.bin",
        size=1024,
        category="large",
        risk="yellow",
        matched_rule="size>=1024",
    )
    assert refine_risk(rec).risk == "green"


def test_migratable_media_rule() -> None:
    rec = FileRecord(
        path=r"C:\Users\x\Downloads\movie.mkv",
        size=1024,
        category="large",
        risk="yellow",
        matched_rule="size>=1024",
    )
    assert refine_risk(rec).matched_rule == "migratable:.mkv"
