# Phase 0 Project Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, locally testable Python/API and TypeScript project skeleton that preserves the keiba-lab boundaries without requiring JRA-VAN, credentials, or PostgreSQL.

**Architecture:** Keep domain contracts independent of FastAPI, persistence, and JV-Link. Compose a small FastAPI service over application ports, add deterministic fixture adapters, and keep the React web shell independent of the analytical core. PostgreSQL/Alembic and Docker are development entry points only; Phase 1 owns business schema and temporal repositories.

**Tech Stack:** Python 3.12, `uv`, FastAPI, Pydantic Settings, pytest, Ruff, mypy, Node.js 22, pnpm, Vite, React, TypeScript, Alembic, PostgreSQL, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-10-01-phase-0-skeleton-design.md`, plus `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, and `AGENTS.md`.

## Global Constraints

- The first walk-forward test year is 2022; Phase 0 must not create a path that weakens this invariant.
- A calculation may read only data effective and received at or before its `as_of_time`.
- Ability prediction never consumes current-race odds.
- Results and payouts are unavailable until the corresponding recommendation has been persisted.
- Raw observations, snapshots, predictions, and recommendations are append-only.
- Every persisted calculation carries data/snapshot lineage plus feature, model, and logic versions.
- A failed leak or version guard invalidates the entire backtest run.
- BUY and SKIP are equally valid recommendation outcomes.
- The Windows/JV-Link boundary remains behind a provider interface.
- Stored instants use UTC; JRA calendar semantics use `Asia/Tokyo`.
- Phase 0 does not require JRA-VAN membership, JV-Link installation, credentials, or a live database.

## Review Focus

- Importing the domain package must not import FastAPI, SQLAlchemy, or JV-Link; test package boundaries in `tests/unit/test_import_boundaries.py`.
- Naive or non-UTC instants must be rejected or normalized explicitly; test this in `tests/unit/test_time_values.py`.
- A fixture result must be identical for the same fixture version and seed; test this in `tests/unit/test_fixtures.py`.
- Health readiness must remain usable with no JRA-VAN or PostgreSQL; test both routes in `tests/integration/test_health_api.py`.
- Configuration and logs must not expose secrets; test defaults and redaction in `tests/unit/test_settings.py` and `tests/unit/test_logging.py`.

---

### Task 1: Lock the Python and TypeScript toolchains

**Files:** `pyproject.toml`, `.python-version`, `uv.lock`, `package.json`, `pnpm-workspace.yaml`, `apps/web/*`

- [ ] Write the failing React smoke test for product name and Phase 0 status.
- [ ] Run `pnpm --filter web test -- --run`; expect missing package/app configuration.
- [ ] Add Python 3.12 and Node 22 configuration, React/Vite/Vitest shell, and Python quality commands.
- [ ] Run web test and `pnpm --filter web build`; expect both to pass.
- [ ] Commit `build: lock phase 0 toolchains`.

### Task 2: Add domain contracts, configuration, logging, and fixture ports

**Files:** `packages/{domain,application,infrastructure}/src/**`, `tests/unit/test_{import_boundaries,time_values,fixtures,settings,logging}.py`

- [ ] Write failing tests for UTC values, versions, deterministic fixture equality, settings defaults, secret redaction, and import boundaries.
- [ ] Run the focused pytest command; expect missing imports/contracts.
- [ ] Implement `UtcInstant`, `AppVersion`, `HealthStatus`, `ObservationProvider`, typed `Settings`, structured logging, and `DeterministicFixtureProvider(seed, fixture_version)`.
- [ ] Run focused pytest, `uv run ruff check packages tests`, and `uv run mypy packages`; expect all to pass.
- [ ] Commit `feat: add phase 0 domain and fixture contracts`.

### Task 3: Expose FastAPI health endpoints

**Files:** `apps/api/src/keiba_api/{app,health}.py`, `tests/integration/test_health_api.py`

- [ ] Write failing ASGI tests for exact JSON from `GET /health/live` and `GET /health/ready`, with no optional service initialization.
- [ ] Run the API test; expect missing `keiba_api` import.
- [ ] Implement `create_app(settings: Settings | None = None) -> FastAPI` and stable local-ready responses.
- [ ] Run the API tests and an optional local Uvicorn startup check; expect pass.
- [ ] Commit `feat: add api health endpoints`.

### Task 4: Add PostgreSQL/Alembic development entry points

**Files:** `alembic.ini`, `alembic/env.py`, `alembic/versions/.gitkeep`, `docker-compose.yml`, `.env.example`, `tests/integration/test_database_entrypoint.py`

- [ ] Write failing tests for a localhost-only PostgreSQL service and an Alembic environment without business models.
- [ ] Run the focused tests; expect missing files/configuration.
- [ ] Add the optional service, non-secret example URL, and empty migration environment; never create schema implicitly at app startup.
- [ ] Run `docker compose config` and the focused tests; expect valid configuration and pass.
- [ ] Commit `build: add postgres development entrypoint`.

### Task 5: Document deterministic fixtures, commands, and progress

**Files:** `fixtures/golden-race/*`, `README.md`, `docs/PROGRESS.md`, `docs/LOGIC_CATALOG.md`, `tests/unit/test_fixture_files.py`

- [ ] Write a failing fixture/documentation test for fixture metadata, seed, and required commands.
- [ ] Run it; expect missing fixture/documentation entries.
- [ ] Add synthetic fixture data, setup/quality commands, Phase 0 Logic Catalog entry, and progress/handoff details.
- [ ] Run the focused test; expect pass.
- [ ] Commit `docs: document phase 0 setup and fixtures`.

### Task 6: Run complete Phase 0 verification and handoff

- [ ] Run `uv run pytest -q`.
- [ ] Run `uv run ruff format --check .`, `uv run ruff check .`, and `uv run mypy packages apps tests`.
- [ ] Run `pnpm test -- --run` and `pnpm build`.
- [ ] Run `git diff --check`, inspect the complete diff, and verify every Phase 0 acceptance criterion.
- [ ] Record exact results in `docs/PROGRESS.md`; commit if Git metadata is writable, otherwise report the native App action required.

