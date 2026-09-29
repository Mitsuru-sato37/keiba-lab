from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_phase1_win_only_contract_is_documented() -> None:
    text = "\n".join(
        (ROOT / name).read_text(encoding="utf-8")
        for name in (
            "docs/PRODUCT_SPEC.md",
            "docs/DATA_SPEC.md",
            "docs/BETTING_SPEC.md",
            "docs/LOGIC_CATALOG.md",
        )
    )
    assert "win-only" in text.lower()
    assert "WAIT" in text
    assert "fair_odds = 1 / win_probability" in text
    assert "EV = win_probability * current_odds" in text
    assert "fixture" in text.lower()
