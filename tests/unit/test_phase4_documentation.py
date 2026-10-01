from pathlib import Path

ROOT = Path(__file__).parents[2]


def read_doc(name: str) -> str:
    return (ROOT / "docs" / name).read_text(encoding="utf-8")


def test_model_spec_records_phase4_baseline_contract() -> None:
    document = read_doc("MODEL_SPEC.md")

    assert "MODEL-BASE-001" in document
    assert "baseline-gate-v1" in document
    assert "2019-2021" in document
    assert "current-race odds" in document


def test_data_spec_records_prediction_persistence_contract() -> None:
    document = read_doc("DATA_SPEC.md")

    assert "Phase 4 baseline prediction contract" in document
    assert "training_manifest_id" in document
    assert "model_manifest_checksum" in document
    assert "append-only" in document


def test_logic_catalog_records_phase4_implementation_references() -> None:
    document = read_doc("LOGIC_CATALOG.md")

    assert "keiba_infrastructure.baseline_prediction.GateStrengthBaseline" in document
    assert "tests/unit/test_baseline_prediction.py" in document
    assert "tests/integration/test_prediction_persistence.py" in document


def test_progress_moves_handoff_to_phase5() -> None:
    document = read_doc("PROGRESS.md")

    assert "Phase 4 — baseline and prediction interfaces" in document
    assert "Phase 5 — backtest engine and leak guard" in document
    assert "MODEL-BASE-001" in document
