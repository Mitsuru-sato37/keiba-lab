from pathlib import Path

ROOT = Path(__file__).parents[2]
COLLECTOR_ROOT = ROOT / "collector" / "KeibaCollector"


def test_collector_shell_is_windows_x64_dotnet_8() -> None:
    project = (COLLECTOR_ROOT / "KeibaCollector.csproj").read_text(encoding="utf-8")

    assert "<TargetFramework>net8.0-windows</TargetFramework>" in project
    assert "<PlatformTarget>x64</PlatformTarget>" in project
    assert "<RuntimeIdentifier>win-x64</RuntimeIdentifier>" in project


def test_collector_shell_uses_the_versioned_wire_contract() -> None:
    source = (COLLECTOR_ROOT / "CollectorEnvelope.cs").read_text(encoding="utf-8")
    program = (COLLECTOR_ROOT / "Program.cs").read_text(encoding="utf-8")

    assert '"jra-van-observation-batch/v1"' in source
    assert '"schema_version"' in source
    assert "CollectorContract.Parse" in program


def test_collector_shell_contains_no_credentials_or_purchase_automation() -> None:
    readme = (COLLECTOR_ROOT / "README.md").read_text(encoding="utf-8")

    assert "credentials" in readme
    assert "ticket" in readme
    assert "JV-Link" in readme
