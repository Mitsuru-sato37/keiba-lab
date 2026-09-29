from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_ci_has_python_and_web_jobs() -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    assert {"python", "web"} <= set(workflow["jobs"])
