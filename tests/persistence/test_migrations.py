from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_alembic_migration_is_present_and_api_does_not_create_schema() -> None:
    assert (ROOT / "alembic.ini").exists()
    versions = list((ROOT / "alembic" / "versions").glob("*.py"))
    assert versions
    assert "create_all" not in (ROOT / "src" / "keiba_lab" / "api" / "main.py").read_text()
