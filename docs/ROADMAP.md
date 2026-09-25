# Roadmap

Status: Current Source of Truth
Last updated: 2026-09-25

Each phase exits only after its acceptance criteria pass. Later phases may
refine earlier specifications but cannot relax temporal or reproducibility
invariants.

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
