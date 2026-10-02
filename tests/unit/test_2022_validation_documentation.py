from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_source_of_truth_documents_record_one_day_validation_slice() -> None:
    roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs" / "PROGRESS.md").read_text(encoding="utf-8")
    catalog = (ROOT / "docs" / "LOGIC_CATALOG.md").read_text(encoding="utf-8")

    assert "Expansion Slice 1 - 2022 one-day validation" in roadmap
    assert "codex/expansion-2022-validation" in progress
    assert "does not claim real-world 2022 performance" in progress
    assert "BACKTEST-004" in catalog
    assert "validation_fixture.OneDayValidationInputProvider" in catalog
    assert "tests/integration/test_2022_one_day_validation.py" in catalog
