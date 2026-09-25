# Phase 0 Project Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a reproducible, tested monorepo skeleton for the Python domain/API, React web UI, PostgreSQL development service, and later .NET JV-Link collector work.

**Architecture:** The repository has one Python distribution under `src/keiba_lab` for the domain and FastAPI boundary, one independently built React application under `apps/web`, infrastructure definitions under `infra`, and PowerShell entry points under `scripts`. Phase 0 deliberately avoids database tables, model training, live JV-Link integration, and betting logic; it establishes typed contracts and verification seams that those phases consume.

**Tech Stack:** CPython 3.12 managed by uv, FastAPI, Pydantic v2, pydantic-settings, pytest, Ruff, mypy, React with TypeScript and Vite, Vitest, Node.js 24, pnpm 11, PostgreSQL 17 development container, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-25-keiba-lab-foundation-design.md`

## Global Constraints

- The first walk-forward test year is 2022; 2022 data must never enter the 2022 training manifest.
- Current-race odds never enter the Core Ability Model.
- Result and payout access remains unavailable until recommendation persistence.
- Stored instants are timezone-aware UTC; JRA calendar semantics use `Asia/Tokyo`.
- Historical artifacts are append-only and carry snapshot, feature, model, and logic version lineage.
- The Windows/JV-Link boundary stays behind a provider interface; Phase 0 uses no credentials and performs no live connection.
- Python is exactly the 3.12 minor line; Node.js is the 24 major line; pnpm is the 11 major line; the future collector targets .NET 8 x64.
- The root verification command is `pwsh -File scripts/verify.ps1`.
- No dependency or generated build output is committed except `uv.lock` and `pnpm-lock.yaml`.

## Review Focus

- Naive datetimes must be rejected by domain contracts rather than silently interpreted in local time; Task 2 pins this behavior.
- Win/top-2/top-3 probabilities must reject non-monotonic values; Task 2 pins this behavior.
- BUY recommendations without items and SKIP recommendations with purchase items must fail validation; Task 2 pins this behavior.
- Missing environment variables must not leak placeholder credentials or secret values into health output; Task 3 pins this behavior.
- A developer machine without Docker or the .NET SDK must still run Python and web verification, while reporting unavailable optional prerequisites clearly; Tasks 6 and 7 pin this behavior.

---

## Planned file map

```text
.editorconfig                     Cross-language whitespace policy
.env.example                      Safe local configuration names and defaults
.gitattributes                    Stable line endings for source and scripts
.gitignore                        Python, Node, .NET, IDE, data, model exclusions
.python-version                   uv Python selection (3.12)
README.md                         Setup, verification, repository map
pyproject.toml                    Python package, dependencies, test/lint/type config
uv.lock                           Locked Python dependency graph
src/keiba_lab/__init__.py         Package version
src/keiba_lab/domain/enums.py     Shared domain enums
src/keiba_lab/domain/models.py    Phase 0 immutable contracts and invariants
src/keiba_lab/settings.py         Validated environment configuration
src/keiba_lab/logging.py          Structured JSON application logging
src/keiba_lab/api/main.py         FastAPI application factory and health route
tests/architecture/test_layout.py Repository-boundary smoke tests
tests/domain/test_models.py       Contract invariant tests
tests/test_settings.py            Configuration and redaction tests
tests/test_logging.py             Structured logging tests
tests/api/test_health.py          API smoke tests
apps/web/*                        Vite React TypeScript application and tests
infra/compose.yaml                Local PostgreSQL development service
scripts/verify.ps1                Complete local verification entry point
.github/workflows/ci.yml          Python and web required checks
services/jvlink-collector/README.md  Phase 2 boundary and prerequisites only
```

### Task 1: Reproducible Python repository bootstrap

**Files:**
- Create: `.editorconfig`
- Create: `.gitattributes`
- Create: `.gitignore`
- Create: `.python-version`
- Create: `pyproject.toml`
- Create: `src/keiba_lab/__init__.py`
- Create: `tests/architecture/test_layout.py`
- Create after dependency resolution: `uv.lock`

**Interfaces:**
- Consumes: repository conventions in `AGENTS.md` and architecture decisions in `docs/ARCHITECTURE.md`.
- Produces: importable package `keiba_lab`, `keiba_lab.__version__`, and the standard Python verification commands used by every later task.

- [ ] **Step 1: Add the failing repository-layout test**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_required_repository_boundaries_exist() -> None:
    required = (
        ROOT / "pyproject.toml",
        ROOT / "src" / "keiba_lab",
        ROOT / "docs" / "ARCHITECTURE.md",
    )
    assert all(path.exists() for path in required)


def test_package_exposes_version() -> None:
    import keiba_lab

    assert keiba_lab.__version__ == "0.1.0"
```

- [ ] **Step 2: Create the root Python project and tool configuration**

Create `pyproject.toml` with this functional content:

```toml
[project]
name = "keiba-lab"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
  "fastapi>=0.115,<1",
  "pydantic>=2.10,<3",
  "pydantic-settings>=2.7,<3",
  "uvicorn>=0.34,<1",
]

[dependency-groups]
dev = [
  "httpx>=0.28,<1",
  "mypy>=1.14,<2",
  "pytest>=8.3,<9",
  "pytest-cov>=6,<7",
  "pyyaml>=6,<7",
  "ruff>=0.9,<1",
]

[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/keiba_lab"]

[tool.pytest.ini_options]
addopts = "-ra --strict-config --strict-markers"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.12"
strict = true
packages = ["keiba_lab"]
```

Create `.python-version` containing `3.12`, and set `__version__ = "0.1.0"` in `src/keiba_lab/__init__.py`.

- [ ] **Step 3: Add cross-platform repository policies**

Set UTF-8, final newline, four-space Python indentation, two-space JSON/YAML/TypeScript indentation in `.editorconfig`. Set `*.ps1 text eol=crlf` and source/Markdown files to `eol=lf` in `.gitattributes`. Ignore `.venv`, Python caches, coverage, `.mypy_cache`, `.ruff_cache`, `node_modules`, `dist`, `.env`, IDE state, `data/`, `models/`, and all .NET `bin/` and `obj/` directories in `.gitignore`.

- [ ] **Step 4: Install the managed Python and lock dependencies**

Run:

```powershell
uv python install 3.12
uv sync --all-groups
```

Expected: `.venv` and `uv.lock` are created; `uv run python --version` reports Python 3.12.x.

- [ ] **Step 5: Run the new test and verify the bootstrap passes**

Run:

```powershell
uv run pytest tests/architecture/test_layout.py -v
```

Expected: both tests pass. Later tasks extend the layout test only when they create their own boundaries, so this task does not commit a known failure.

- [ ] **Step 6: Commit the reproducible Python bootstrap**

```powershell
git add .editorconfig .gitattributes .gitignore .python-version pyproject.toml uv.lock src tests/architecture
git commit -m "build: bootstrap Python project"
```

### Task 2: Immutable domain contracts and invariants

**Files:**
- Create: `src/keiba_lab/domain/__init__.py`
- Create: `src/keiba_lab/domain/enums.py`
- Create: `src/keiba_lab/domain/models.py`
- Create: `tests/domain/test_models.py`

**Interfaces:**
- Consumes: Pydantic v2 and timezone-aware `datetime` values.
- Produces: `Strategy`, `Decision`, `SkipCategory`, `DataStatus`, `BetType`, `VersionRef`, `RaceSnapshot`, `RunnerSnapshot`, `HorsePrediction`, `BetCandidate`, `RecommendationItem`, and `Recommendation`.

- [ ] **Step 1: Write failing enum and timezone tests**

```python
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from keiba_lab.domain.enums import Decision, Strategy
from keiba_lab.domain.models import RaceSnapshot, RunnerSnapshot


def test_stable_external_enum_values() -> None:
    assert Decision.BUY.value == "BUY"
    assert Decision.SKIP.value == "SKIP"
    assert Strategy.LONGSHOT.value == "LONGSHOT"


def test_race_snapshot_rejects_naive_as_of_time() -> None:
    runner = RunnerSnapshot(horse_id="H1", horse_number=1)
    with pytest.raises(ValidationError, match="timezone-aware"):
        RaceSnapshot(
            race_id="R1",
            snapshot_id="S1",
            as_of_time=datetime(2022, 1, 1, 0, 0),
            scheduled_post_time=datetime(2022, 1, 1, 6, 0, tzinfo=UTC),
            runners=(runner,),
        )
```

- [ ] **Step 2: Implement enums and the shared immutable base model**

Use `str, Enum` values exactly matching their persisted uppercase values. Define an immutable Pydantic base with `ConfigDict(frozen=True, extra="forbid")`. Implement a reusable field validator that rejects `datetime` values whose `tzinfo` or `utcoffset()` is absent.

```python
# enums.py
from enum import Enum


class Strategy(str, Enum):
    STABLE = "STABLE"
    BALANCED = "BALANCED"
    LONGSHOT = "LONGSHOT"
    OVERALL = "OVERALL"


class Decision(str, Enum):
    BUY = "BUY"
    SKIP = "SKIP"


class SkipCategory(str, Enum):
    NO_VALUE = "NO_VALUE"
    UNRELIABLE = "UNRELIABLE"
    CAPITAL = "CAPITAL"
    STALE = "STALE"


class DataStatus(str, Enum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    INVALID = "INVALID"


class BetType(str, Enum):
    WIN = "WIN"
    PLACE = "PLACE"
    QUINELLA = "QUINELLA"
    EXACTA = "EXACTA"
    WIDE = "WIDE"
    TRIO = "TRIO"
    TRIFECTA = "TRIFECTA"
```

```python
# models.py foundation
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from keiba_lab.domain.enums import BetType, Decision, SkipCategory, Strategy


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RunnerSnapshot(DomainModel):
    horse_id: str = Field(min_length=1)
    horse_number: int = Field(ge=1)


class RaceSnapshot(DomainModel):
    race_id: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    as_of_time: datetime
    scheduled_post_time: datetime
    runners: tuple[RunnerSnapshot, ...] = Field(min_length=1)

    @field_validator("as_of_time", "scheduled_post_time")
    @classmethod
    def require_aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value
```

- [ ] **Step 3: Run the timezone tests**

Run `uv run pytest tests/domain/test_models.py -v`.

Expected: enum and naive-time tests pass.

- [ ] **Step 4: Add failing probability-order tests**

```python
from decimal import Decimal


def test_prediction_requires_monotonic_finish_probabilities() -> None:
    with pytest.raises(ValidationError, match="win <= top2 <= top3"):
        HorsePrediction(
            horse_id="H1",
            win_probability=Decimal("0.30"),
            top2_probability=Decimal("0.20"),
            top3_probability=Decimal("0.60"),
            ranking_score=Decimal("1.2"),
            uncertainty=Decimal("0.1"),
            model_version=VersionRef(name="baseline", version="1"),
            feature_version=VersionRef(name="core", version="1"),
        )
```

- [ ] **Step 5: Implement prediction and bet contracts**

Use `Decimal` fields constrained to `[0, 1]` for probabilities and uncertainty, strictly positive odds, non-empty canonical combinations, and non-empty version names/versions. Add a model validator enforcing `win_probability <= top2_probability <= top3_probability`.

```python
Probability = Annotated[Decimal, Field(ge=0, le=1)]


class VersionRef(DomainModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class HorsePrediction(DomainModel):
    horse_id: str = Field(min_length=1)
    win_probability: Probability
    top2_probability: Probability
    top3_probability: Probability
    ranking_score: Decimal
    uncertainty: Probability
    model_version: VersionRef
    feature_version: VersionRef

    @model_validator(mode="after")
    def validate_probability_order(self) -> Self:
        if not self.win_probability <= self.top2_probability <= self.top3_probability:
            raise ValueError("probabilities must satisfy win <= top2 <= top3")
        return self


class BetCandidate(DomainModel):
    bet_type: BetType
    combination: tuple[str, ...] = Field(min_length=1)
    model_probability: Probability
    current_odds: Decimal = Field(gt=0)
    predicted_final_odds: Decimal = Field(gt=0)
    conservative_probability: Probability
    conservative_odds: Decimal = Field(gt=0)
    expected_value: Decimal
    uncertainty: Probability
    logic_version: VersionRef
```

- [ ] **Step 6: Add failing recommendation-state tests**

```python
def test_buy_requires_at_least_one_item() -> None:
    with pytest.raises(ValidationError, match="BUY requires items"):
        Recommendation(
            recommendation_id="REC1",
            prediction_snapshot_id="P1",
            strategy=Strategy.STABLE,
            decision=Decision.BUY,
            items=(),
            reason_codes=(),
            logic_version=VersionRef(name="RECO-001", version="1"),
            calculated_at=datetime(2022, 1, 1, tzinfo=UTC),
        )


def make_item() -> RecommendationItem:
    candidate = BetCandidate(
        bet_type=BetType.WIN,
        combination=("H1",),
        model_probability=Decimal("0.30"),
        current_odds=Decimal("4.0"),
        predicted_final_odds=Decimal("3.8"),
        conservative_probability=Decimal("0.25"),
        conservative_odds=Decimal("3.5"),
        expected_value=Decimal("0.875"),
        uncertainty=Decimal("0.10"),
        logic_version=VersionRef(name="EV-001", version="1"),
    )
    return RecommendationItem(candidate=candidate, amount_yen=100)


def test_skip_rejects_purchase_items() -> None:
    with pytest.raises(ValidationError, match="SKIP cannot contain items"):
        Recommendation(
            recommendation_id="REC2",
            prediction_snapshot_id="P1",
            strategy=Strategy.STABLE,
            decision=Decision.SKIP,
            skip_category=SkipCategory.NO_VALUE,
            items=(make_item(),),
            reason_codes=("EV_BELOW_THRESHOLD",),
            logic_version=VersionRef(name="RECO-001", version="1"),
            calculated_at=datetime(2022, 1, 1, tzinfo=UTC),
        )
```

- [ ] **Step 7: Implement recommendation state validation**

Require BUY to have one or more items and no skip category. Require SKIP to have zero items, one skip category, and one or more reason codes. Keep `prediction_snapshot_id`, `logic_version`, and `calculated_at` mandatory for both outcomes.

```python
class RecommendationItem(DomainModel):
    candidate: BetCandidate
    amount_yen: int = Field(ge=100, multiple_of=100)


class Recommendation(DomainModel):
    recommendation_id: str = Field(min_length=1)
    prediction_snapshot_id: str = Field(min_length=1)
    strategy: Strategy
    decision: Decision
    items: tuple[RecommendationItem, ...]
    skip_category: SkipCategory | None = None
    reason_codes: tuple[str, ...]
    logic_version: VersionRef
    calculated_at: datetime

    @field_validator("calculated_at")
    @classmethod
    def require_aware_calculated_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_decision_state(self) -> Self:
        if self.decision is Decision.BUY:
            if not self.items:
                raise ValueError("BUY requires items")
            if self.skip_category is not None:
                raise ValueError("BUY cannot have a skip category")
        else:
            if self.items:
                raise ValueError("SKIP cannot contain items")
            if self.skip_category is None or not self.reason_codes:
                raise ValueError("SKIP requires a category and reason codes")
        return self
```

- [ ] **Step 8: Run domain verification and commit**

```powershell
uv run pytest tests/domain/test_models.py -v
uv run mypy src/keiba_lab/domain
uv run ruff check src/keiba_lab/domain tests/domain
git add src/keiba_lab/domain tests/domain
git commit -m "feat: add immutable domain contracts"
```

Expected: all commands exit 0.

### Task 3: Validated settings and API health contract

**Files:**
- Create: `.env.example`
- Create: `src/keiba_lab/settings.py`
- Create: `src/keiba_lab/logging.py`
- Create: `src/keiba_lab/api/__init__.py`
- Create: `src/keiba_lab/api/main.py`
- Create: `tests/test_settings.py`
- Create: `tests/test_logging.py`
- Create: `tests/api/test_health.py`

**Interfaces:**
- Consumes: environment variables prefixed `KEIBA_`.
- Produces: `Settings`, `get_settings() -> Settings`, `create_app(settings: Settings | None = None) -> FastAPI`, and module variable `app`.
- Produces additionally: `configure_logging(level: str) -> None` with one JSON object per log record.

- [ ] **Step 1: Write failing settings tests**

```python
from pydantic import SecretStr

from keiba_lab.settings import Settings


def test_settings_have_safe_local_defaults() -> None:
    settings = Settings()
    assert settings.environment == "development"
    assert settings.timezone == "Asia/Tokyo"
    assert settings.database_url.get_secret_value().startswith("postgresql+")


def test_settings_repr_redacts_database_url() -> None:
    settings = Settings(database_url=SecretStr("postgresql+psycopg://user:secret@host/db"))
    assert "secret" not in repr(settings)
```

- [ ] **Step 2: Implement environment settings**

Use `BaseSettings` with `env_prefix="KEIBA_"`, `env_file=".env"`, `extra="ignore"`. Fields are `environment: Literal["development", "test", "production"]`, `timezone: Literal["Asia/Tokyo"]`, `database_url: SecretStr`, `log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]`, and `api_version: str = "0.1.0"`. The safe local database default matches `infra/compose.yaml` but contains no production credential.

```python
from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KEIBA_", env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    timezone: Literal["Asia/Tokyo"] = "Asia/Tokyo"
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://keiba:keiba_local@localhost:5432/keiba_lab"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    api_version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 3: Create `.env.example`**

```dotenv
KEIBA_ENVIRONMENT=development
KEIBA_TIMEZONE=Asia/Tokyo
KEIBA_DATABASE_URL=postgresql+psycopg://keiba:keiba_local@localhost:5432/keiba_lab
KEIBA_LOG_LEVEL=INFO
```

- [ ] **Step 4: Run settings tests**

Run `uv run pytest tests/test_settings.py -v`.

Expected: both tests pass and no secret appears in test output.

- [ ] **Step 5: Write the failing structured-logging test**

```python
import json
import logging

import pytest

from keiba_lab.logging import configure_logging


def test_logging_emits_parseable_structured_record(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")
    logging.getLogger("keiba_lab.test").info("pipeline ready")
    record = json.loads(capsys.readouterr().err)
    assert record["level"] == "INFO"
    assert record["logger"] == "keiba_lab.test"
    assert record["message"] == "pipeline ready"
    assert record["timestamp"].endswith("Z")
```

- [ ] **Step 6: Implement the JSON formatter and logging setup**

```python
import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
```

- [ ] **Step 7: Run logging tests**

Run `uv run pytest tests/test_logging.py -v`.

Expected: the emitted stderr line parses as JSON and contains all four stable keys.

- [ ] **Step 8: Write the failing health test**

```python
from fastapi.testclient import TestClient

from keiba_lab.api.main import create_app
from keiba_lab.settings import Settings


def test_health_exposes_no_configuration_secrets() -> None:
    settings = Settings(database_url="postgresql+psycopg://user:secret@host/db")
    response = TestClient(create_app(settings)).get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "keiba-lab-api",
        "version": "0.1.0",
    }
    assert "secret" not in response.text
```

- [ ] **Step 9: Implement the application factory**

Create FastAPI with title `keiba-lab API`, version from settings, and `GET /health` returning exactly the tested JSON. Do not connect to PostgreSQL during import or health checks. Set `app = create_app()` for Uvicorn.

```python
from fastapi import FastAPI

from keiba_lab.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    application = FastAPI(title="keiba-lab API", version=resolved.api_version)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "keiba-lab-api", "version": resolved.api_version}

    return application


app = create_app()
```

- [ ] **Step 10: Verify and commit**

```powershell
uv run pytest tests/test_settings.py tests/test_logging.py tests/api/test_health.py -v
uv run mypy src/keiba_lab
uv run ruff check src tests
git add .env.example src/keiba_lab/settings.py src/keiba_lab/logging.py src/keiba_lab/api tests/test_settings.py tests/test_logging.py tests/api
git commit -m "feat: add settings and API health endpoint"
```

Expected: all commands exit 0.

### Task 4: React/TypeScript application shell

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/pnpm-lock.yaml`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/App.test.tsx`
- Create: remaining Vite TypeScript support files generated by the pinned template.

**Interfaces:**
- Consumes: no backend endpoint beyond the future `/health` contract.
- Produces: a buildable application shell with Today, Race, Logic Explorer, Backtest, Performance, and Settings navigation labels.

- [ ] **Step 1: Scaffold the Vite React TypeScript application**

Run from the repository root:

```powershell
pnpm create vite apps/web --template react-ts
Set-Location apps/web
pnpm install
pnpm add -D vitest jsdom @testing-library/react @testing-library/jest-dom
Set-Location ../..
```

Expected: `apps/web/package.json` and the root or app lockfile are created without modifying files outside `apps/web` except the selected lockfile.

- [ ] **Step 2: Configure the test environment and write the failing navigation test**

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('shows the required product areas', () => {
    render(<App />)
    for (const label of ['Today', 'Race', 'Logic Explorer', 'Backtest', 'Performance', 'Settings']) {
      expect(screen.getByRole('navigation')).toHaveTextContent(label)
    }
  })
})
```

Configure Vitest with `environment: 'jsdom'`, a setup file importing `@testing-library/jest-dom/vitest`, and package scripts `test: "vitest run"`, `typecheck: "tsc -b"`, and the existing `build`/`lint` scripts.

- [ ] **Step 3: Run the test and confirm failure**

Run `pnpm --dir apps/web test`.

Expected: FAIL because the generated Vite demo does not contain the required navigation.

- [ ] **Step 4: Implement the minimal accessible application shell**

Render an application title and one `<nav aria-label="Primary">` containing buttons or links for the six required areas. Keep this as a semantic shell; do not add routing, charts, API calls, or final visual design in Phase 0.

```tsx
const areas = ['Today', 'Race', 'Logic Explorer', 'Backtest', 'Performance', 'Settings']

export default function App() {
  return (
    <main>
      <h1>keiba-lab</h1>
      <nav aria-label="Primary">
        <ul>
          {areas.map((area) => (
            <li key={area}><button type="button">{area}</button></li>
          ))}
        </ul>
      </nav>
    </main>
  )
}
```

- [ ] **Step 5: Verify web tests, types, lint, and build**

```powershell
pnpm --dir apps/web test
pnpm --dir apps/web typecheck
pnpm --dir apps/web lint
pnpm --dir apps/web build
```

Expected: all commands exit 0 and `apps/web/dist` remains ignored.

- [ ] **Step 6: Commit the web shell**

```powershell
git add apps/web
git commit -m "feat: add web application shell"
```

### Task 5: PostgreSQL development service and collector boundary

**Files:**
- Create: `infra/compose.yaml`
- Create: `services/jvlink-collector/README.md`
- Modify: `tests/architecture/test_layout.py`
- Create: `tests/architecture/test_infrastructure.py`

**Interfaces:**
- Consumes: safe local settings from `.env.example`.
- Produces: PostgreSQL service name `postgres`, database `keiba_lab`, health check, named volume, and the documented Phase 2 collector import boundary.

- [ ] **Step 1: Add failing infrastructure contract tests**

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_postgres_compose_contract() -> None:
    document = yaml.safe_load((ROOT / "infra" / "compose.yaml").read_text(encoding="utf-8"))
    postgres = document["services"]["postgres"]
    assert postgres["image"].startswith("postgres:17")
    assert postgres["environment"]["POSTGRES_DB"] == "keiba_lab"
    assert "healthcheck" in postgres


def test_collector_boundary_documents_no_live_requirement() -> None:
    text = (ROOT / "services" / "jvlink-collector" / "README.md").read_text(encoding="utf-8")
    assert "Phase 0 does not require JV-Link" in text
    assert "BASE-JV" in text
```

- [ ] **Step 2: Run tests and confirm failure**

Run `uv run pytest tests/architecture/test_layout.py tests/architecture/test_infrastructure.py -v`.

Expected: FAIL because the compose file and collector README do not exist.

- [ ] **Step 3: Implement the PostgreSQL compose contract**

Create a PostgreSQL 17 service bound to `127.0.0.1:5432`, with local-only user `keiba`, password `keiba_local`, database `keiba_lab`, a `pg_isready` health check, and named volume `postgres-data`. Do not add application migrations in Phase 0.

```yaml
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: keiba_lab
      POSTGRES_USER: keiba
      POSTGRES_PASSWORD: keiba_local
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U keiba -d keiba_lab"]
      interval: 5s
      timeout: 5s
      retries: 10
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

- [ ] **Step 4: Document the future collector boundary**

The README must state that Phase 0 does not require JV-Link, credentials, .NET SDK, or a Data Lab subscription. It must define Phase 2's responsibility as a Windows x64 .NET 8 adapter that emits versioned BASE-JV import batches and does not write analytical tables directly.

```markdown
# JV-Link Collector Boundary

Phase 0 does not require JV-Link, a JRA-VAN Data Lab subscription, credentials,
or the .NET SDK. Phase 2 will implement this directory as a Windows x64 .NET 8
adapter. It emits versioned BASE-JV import batches through the provider contract
and never writes normalized, feature, prediction, or recommendation tables
directly.
```

- [ ] **Step 5: Verify contracts and optional runtime availability**

```powershell
uv run pytest tests/architecture -v
if (Get-Command docker -ErrorAction SilentlyContinue) {
  docker compose -f infra/compose.yaml config --quiet
} else {
  Write-Warning 'Docker unavailable: compose runtime check skipped; YAML contract test passed.'
}
```

Expected: pytest passes. Docker validation passes when Docker is installed; otherwise the warning is explicit and the optional check does not hide the missing prerequisite.

- [ ] **Step 6: Commit infrastructure contracts**

```powershell
git add infra services/jvlink-collector tests/architecture
git commit -m "build: add development infrastructure contracts"
```

### Task 6: One-command verification and setup documentation

**Files:**
- Create: `scripts/verify.ps1`
- Create: `README.md`
- Modify: `tests/architecture/test_layout.py`

**Interfaces:**
- Consumes: uv, pnpm, and optional Docker/.NET commands.
- Produces: `scripts/verify.ps1` with mandatory Python/web checks and explicit optional-prerequisite reporting.

- [ ] **Step 1: Extend the failing layout test**

Add assertions that `README.md`, `scripts/verify.ps1`, `.env.example`, and `infra/compose.yaml` exist. Run `uv run pytest tests/architecture/test_layout.py -v` and confirm it fails for the missing README/script.

- [ ] **Step 2: Implement `scripts/verify.ps1`**

Use `$ErrorActionPreference = 'Stop'`. Run, in order:

```powershell
uv sync --all-groups --locked
uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src/keiba_lab
uv run pytest --cov=keiba_lab --cov-report=term-missing
pnpm --dir apps/web install --frozen-lockfile
pnpm --dir apps/web test
pnpm --dir apps/web typecheck
pnpm --dir apps/web lint
pnpm --dir apps/web build
```

After mandatory checks, print detected versions for uv, Node, and pnpm. If Docker is present, run `docker compose -f infra/compose.yaml config --quiet`; otherwise print a warning. If `dotnet --list-sdks` returns no SDK, print a warning that .NET 8 is required in Phase 2; do not fail Phase 0.

```powershell
$ErrorActionPreference = 'Stop'

uv sync --all-groups --locked
uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src/keiba_lab
uv run pytest --cov=keiba_lab --cov-report=term-missing
pnpm --dir apps/web install --frozen-lockfile
pnpm --dir apps/web test
pnpm --dir apps/web typecheck
pnpm --dir apps/web lint
pnpm --dir apps/web build

uv --version
node --version
pnpm --version

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose -f infra/compose.yaml config --quiet
} else {
    Write-Warning 'Docker unavailable; compose runtime validation was not run.'
}

$dotnetSdks = if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    @(dotnet --list-sdks)
} else {
    @()
}
if ($dotnetSdks.Count -eq 0) {
    Write-Warning '.NET SDK unavailable; .NET 8 is required for the Phase 2 collector.'
}
```

- [ ] **Step 3: Write README setup and repository map**

Document Windows 11 prerequisites, `uv python install 3.12`, `uv sync --all-groups`, `pnpm --dir apps/web install`, optional PostgreSQL startup, API command `uv run uvicorn keiba_lab.api.main:app --reload`, web command `pnpm --dir apps/web dev`, and full verification command. Explicitly state Docker and .NET are not currently installed on the development machine as observed on 2026-09-25 and are not required for mandatory Phase 0 verification.

- [ ] **Step 4: Run the complete verification command**

Run `pwsh -File scripts/verify.ps1`.

Expected: every mandatory command exits 0; Docker/.NET absence produces warnings rather than false success claims about those optional runtime checks.

- [ ] **Step 5: Commit verification and documentation**

```powershell
git add README.md scripts/verify.ps1 tests/architecture/test_layout.py
git commit -m "build: add one-command verification"
```

### Task 7: GitHub Actions and Phase 0 acceptance

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `docs/ROADMAP.md`

**Interfaces:**
- Consumes: lockfiles and the same commands used by `scripts/verify.ps1`.
- Produces: separate `python` and `web` CI jobs suitable for required checks and a recorded Phase 0 completion status only after both local and GitHub verification pass.

- [ ] **Step 1: Add CI workflow contract test**

Create `tests/architecture/test_ci.py`:

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_ci_has_python_and_web_jobs() -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    assert {"python", "web"} <= set(workflow["jobs"])
```

Run `uv run pytest tests/architecture/test_ci.py -v` and confirm it fails because the workflow does not exist.

- [ ] **Step 2: Implement the CI workflow**

Trigger on pull requests and pushes to `main`. The Python job runs on `windows-latest`, installs Python 3.12 through `astral-sh/setup-uv`, then executes locked sync, Ruff format/check, mypy, and pytest with coverage. The web job runs on `windows-latest`, installs Node 24 and pnpm 11, uses the pnpm cache, then executes frozen install, test, typecheck, lint, and build.

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  python:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          python-version: "3.12"
          enable-cache: true
      - run: uv sync --all-groups --locked
      - run: uv run ruff format --check src tests
      - run: uv run ruff check src tests
      - run: uv run mypy src/keiba_lab
      - run: uv run pytest --cov=keiba_lab --cov-report=term-missing
  web:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
        with:
          version: 11
      - uses: actions/setup-node@v4
        with:
          node-version: "24"
          cache: pnpm
          cache-dependency-path: apps/web/pnpm-lock.yaml
      - run: pnpm --dir apps/web install --frozen-lockfile
      - run: pnpm --dir apps/web test
      - run: pnpm --dir apps/web typecheck
      - run: pnpm --dir apps/web lint
      - run: pnpm --dir apps/web build
```

- [ ] **Step 3: Run local acceptance verification**

```powershell
pwsh -File scripts/verify.ps1
git diff --check origin/main...HEAD
git status --short
```

Expected: verification exits 0, diff check emits no errors, and status contains only the intended final plan/status changes before commit.

- [ ] **Step 4: Update roadmap evidence without overstating remote checks**

Add a Phase 0 evidence subsection listing the local verification command, commit IDs, and CI workflow name. Do not mark GitHub CI or branch protection as active until the pushed workflow has actually completed successfully.

- [ ] **Step 5: Commit, push, and open the Phase 0 pull request**

```powershell
git add .github/workflows/ci.yml tests/architecture/test_ci.py README.md docs/ROADMAP.md
git commit -m "ci: verify Phase 0 skeleton"
git fetch origin main
git rebase origin/main
pwsh -File scripts/verify.ps1
git push -u origin codex/phase-0-skeleton
```

Open a pull request titled `build: establish Phase 0 project skeleton`. Its body must summarize the Python/API/web/infrastructure boundaries, list the local verification command and results, disclose skipped Docker/.NET runtime checks, and link `docs/ROADMAP.md` plus this plan.

- [ ] **Step 6: Verify GitHub checks and review the complete branch diff**

Wait for both CI jobs. If either fails, reproduce and fix it on the branch, commit the focused repair, push, and wait again. Review `origin/main...HEAD` for secrets, generated artifacts, missing specification updates, and unrelated changes before requesting merge.
