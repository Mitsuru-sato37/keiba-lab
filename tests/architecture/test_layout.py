from pathlib import Path

import keiba_lab

ROOT = Path(__file__).resolve().parents[2]


def test_required_repository_boundaries_exist() -> None:
    required = (
        ROOT / "pyproject.toml",
        ROOT / "src" / "keiba_lab",
        ROOT / "docs" / "ARCHITECTURE.md",
    )
    assert all(path.exists() for path in required)


def test_package_exposes_version() -> None:
    assert keiba_lab.__version__ == "0.1.0"
