from pathlib import Path

ROOT = Path(__file__).parents[2]


def read(name: str) -> str:
    return (ROOT / "docs" / name).read_text(encoding="utf-8")


def test_backtest_spec_records_phase5_execution_and_reporting_contract() -> None:
    document = read("BACKTEST_SPEC.md")

    assert "BacktestOrchestrator" in document
    assert "backtest_runs" in document
    assert "odds coverage" in document
    assert "official" in document


def test_data_spec_records_immutable_phase5_manifest_storage() -> None:
    document = read("DATA_SPEC.md")

    assert "Phase 5 backtest engine and leak guard" in document
    assert "0004_phase5_backtest_records" in document
    assert "backtest_guard_results" in document


def test_architecture_records_capability_result_boundary() -> None:
    document = read("ARCHITECTURE.md")

    assert "ResultAccessCapability" in document
    assert "BacktestOrchestrator" in document
    assert "run to `invalid`" in document


def test_logic_catalog_and_progress_reference_phase5_evidence() -> None:
    catalog = read("LOGIC_CATALOG.md")
    progress = read("PROGRESS.md")

    assert "BacktestOrchestrator" in catalog
    assert "backtest_guards" in catalog
    assert "tests/unit/test_backtest_engine.py" in catalog
    assert "Phase 5 — backtest engine and leak guard (completed)" in progress
    assert "0004_phase5_backtest_records" in progress
