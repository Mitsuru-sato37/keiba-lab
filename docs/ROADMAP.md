# Roadmap

Status: Current Source of Truth
Last updated: 2026-09-25

Each phase exits only after its acceptance criteria pass. Later phases may
refine earlier specifications but cannot relax temporal or reproducibility
invariants.

## Delivery cadence

Each phase normally uses its own `codex/` branch and pull request. Within a
phase, commit every coherent, verified unit and push at meaningful recovery or
review checkpoints. Before phase work and before opening a pull request, fetch
`origin/main` and reconcile divergence. A phase is not complete until its exit
criteria pass, its specification and Logic Catalog references are current, and
the final pull-request diff has been reviewed.

## Phase 0 - Project skeleton

- Monorepo layout, locked Python/TypeScript environments, quality commands.
- Typed domain contracts, configuration, logging, and health endpoints.
- PostgreSQL development setup and deterministic fixture conventions.
- CI-ready unit test layout.

Exit: clean setup from documented steps; smoke tests and quality checks pass.

## Phase 1 - Database schema and migrations

- Raw/normalized/snapshot/artifact/version/trace/backtest entities.
- Append-only and lineage constraints.
- Temporal query repository tests.

Exit: migrations round-trip on a clean database and temporal negative tests
pass.

## Phase 2 - JRA-VAN adapter interface

- Provider port and fixture implementation first.
- .NET 8 x64 collector shell and import contract without credentials.
- Idempotent batch promotion and structured errors.

Exit: fixture and collector-contract tests pass. Stop only when live membership,
use key, JV-Link installation, or login is required.

## Phase 3 - Snapshot and Feature Engine

- Race snapshot builder and Core Feature v1 registry.
- Full lineage and LEAK-001 enforcement.

Exit: point-in-time fixtures pass at boundary timestamps.

## Phase 4 - Baseline and prediction interfaces

- Baseline, probability/ranking ports, calibration, model manifests.
- CatBoost implementations after fixture contracts stabilize.

Exit: probability invariants, training-period isolation, and deterministic
inference tests pass.

## Phase 5 - Backtest Engine and Leak Guard

- Fold orchestration, result capability gate, immutable manifests.
- LEAK-001 through LEAK-004 and VERSION-001.

Exit: all positive fixtures pass and every seeded violation invalidates its run.

## Phase 6 - Dummy-data Golden Race

- Complete gated pipeline through evaluation using deterministic fixtures.
- Persisted traces and betting-policy replay.

Exit: a recommendation is reproducible end-to-end and result access before
persistence demonstrably fails.

## Phase 7 - Logic Explorer mock

- Mock Today, Race, and Logic Explorer flows against Golden Race artifacts.
- Click-through input, conditions, output, next stage, and versions.

Exit: UI can trace a displayed recommendation to stored calculation evidence.

## Expansion

Golden Race -> one day -> all 2022 -> 2023 -> 2024 -> frozen 2025 test ->
2019-2025 final training -> 2026 live validation.

## Phase 0 evidence (2026-09-29)

- Local acceptance: `pwsh -File scripts/verify.ps1` passed (23 Python tests and Web test/typecheck/lint/build).
- Commits: `2f4c48c` Python bootstrap, `ce7d7a0` domain contracts, `5891861` settings/API, `cfcb289` Web shell.
- CI workflow: `.github/workflows/ci.yml` defines required `python` and `web` jobs.
- Docker and .NET SDK runtime checks were explicitly skipped with warnings because they are unavailable in this environment; Phase 0 mandatory checks do not require them.

## Phase 1 evidence (in progress, 2026-09-29)

- Dedicated branch: `codex/phase-1-db-schema`.
- Added SQLAlchemy metadata, Alembic configuration, initial migration, temporal append-only repository contract, fixture provider, configurable win-only EV policy, and Today → Race API/UI flow.
- Focused provider/persistence/application/API tests and the full local verification command pass (39 Python tests plus Web checks).
- PostgreSQL runtime round-trip remains pending because Docker is unavailable; Alembic offline SQL generation succeeds.

- Current Phase 1 checkpoint: `a3c90dd` plus the verified Web/API vertical slice on `codex/phase-1-db-schema`.
