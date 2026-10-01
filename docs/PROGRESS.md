# Progress

Status: Current handoff
Last updated: 2026-10-01

## Current phase

Phase 3 — snapshot and feature engine.

The Phase 3 acceptance slice is implemented against deterministic observations
and the point-in-time data boundary. It does not require JRA-VAN credentials,
a use key, JV-Link installation, or login.

## Completed

- Product specification, architecture, data, model, betting, backtest, and
  logic-catalog documents.
- Python/TypeScript project configuration and React/Vite web shell.
- Typed domain contracts, UTC instants, local settings, redacted logging, and
  FastAPI health endpoints.
- PostgreSQL Docker Compose and Alembic foundation migration.
- Temporal observation eligibility, append-only guards, lineage columns, and
  recommendation-before-result persistence gate.
- `ObservationBatch`/`ObservationProvider` application contract.
- Deterministic fixture provider with stable batch identity and seed behavior.
- Versioned collector JSON envelope with checksum, UTC, duplicate-ID, and
  fail-closed validation.
- Windows x64 .NET 8 collector shell source and documented standard-I/O
  handoff. .NET SDK 8.0.420 is installed in the local tool area and the
  collector builds successfully for win-x64.
- `ingestion_batches` migration and idempotent batch promotion. Repeating an
  identical batch is a no-op; conflicting batch reuse fails closed.
- Provider record type/key and ingestion batch lineage preservation in raw
  observations.
- Explicit as-of race snapshot construction with temporal leak rejection,
  deterministic membership/checksum, and runner identity validation.
- Core Feature v1 generation with explicit missing fields, feature/data/logic
  lineage, and current-race odds rejection.
- SQLite migration compatibility and PostgreSQL migration validation for the
  new feature logic lineage column.

## Next implementation target

Phase 4 — prediction baseline: add a first walk-forward-safe model contract on
top of the persisted snapshot and feature artifacts.

## Constraints

- Keep the Windows/JV-Link boundary behind a provider interface.
- Preserve temporal, lineage, leak-prevention, and reproducibility invariants.
- Do not add external enrichment to BASE-JV.
- Never automate ticket purchase.
- Docker Desktop is installed and running through WSL 2. PostgreSQL validation
  is now active. The local SDK/tool directories are ignored by Git.

## Current handoff details

- Branch: `codex/phase-3-snapshot-feature-engine`.
- Phase 2 provider commits: `64ae7ca`, `fd3fa30`, and `797d59b`.
- Phase 1 branch and commit: `codex/phase-1-data-foundation` at `d6d5d3a`.
- No user input or external credential is currently required.

## Verified commands

- Focused Phase 3 suite: 12 passed with the project-local pytest temporary
  directory. Full-suite verification is run before the Phase 3 checkpoint.
- Collector shell static contract tests and real .NET build: passed.
- PostgreSQL Alembic migration: `0002_phase2_ingestion_batches` was applied;
  Phase 3 migration is pending final verification.
- Full Python/TypeScript checks are rerun after the dependency update.
