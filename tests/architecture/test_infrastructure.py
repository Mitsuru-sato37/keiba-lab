from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_postgres_compose_contract() -> None:
    document = yaml.safe_load((ROOT / "infra" / "compose.yaml").read_text(encoding="utf-8"))
    service = document["services"]["postgres"]
    assert service["image"].startswith("postgres:")
    assert service["healthcheck"]
    assert service["volumes"]


def test_collector_boundary_documents_no_live_requirement() -> None:
    text = (ROOT / "services" / "jvlink-collector" / "README.md").read_text(encoding="utf-8")
    assert "Phase 0" in text and "credentials" in text
