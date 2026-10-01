import json
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_golden_race_fixture_declares_stable_metadata() -> None:
    fixture = json.loads(
        (ROOT / "fixtures" / "golden-race" / "fixture.json").read_text(encoding="utf-8"),
    )

    assert fixture["fixture_version"] == "golden-race-v1"
    assert fixture["seed"] == 20220101
    assert fixture["source"] == "deterministic-fixture"
    assert len(fixture["observations"]) > 0


def test_readme_documents_reproducible_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "pytest" in readme
    assert "pnpm" in readme
    assert "JRA-VAN" in readme
