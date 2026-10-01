# Progress

Status: Current handoff
Last updated: 2026-10-01

## Current phase

Phase 2 — JRA-VAN adapter interface.

The Phase 2 acceptance slice is implemented without requiring JRA-VAN
credentials, a use key, JV-Link installation, or login.

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
  handoff. Actual .NET build is deferred because this host has no .NET SDK.
- `ingestion_batches` migration and idempotent batch promotion. Repeating an
  identical batch is a no-op; conflicting batch reuse fails closed.
- Provider record type/key and ingestion batch lineage preservation in raw
  observations.

## Next implementation target

Phase 3 — snapshot and feature engine: build the race snapshot contract and
Core Feature v1 registry on top of the now-stable point-in-time data boundary.

## Constraints

- Keep the Windows/JV-Link boundary behind a provider interface.
- Preserve temporal, lineage, leak-prevention, and reproducibility invariants.
- Do not add external enrichment to BASE-JV.
- Never automate ticket purchase.
- Docker CLI and .NET SDK are not installed in this environment. PostgreSQL
  and collector build validation remain deferred; SQLite integration tests and
  static collector contract tests are active.

## Current handoff details

- Branch: `codex/phase-2-jra-van-adapter`.
- Phase 2 provider commit: `64ae7ca`.
- Phase 1 branch and commit: `codex/phase-1-data-foundation` at `d6d5d3a`.
- No user input or external credential is currently required.

## Verified commands

- Full Python suite and integration migration checks: rerun before commit.
- Collector shell static contract tests: passed.
- Full Python/TypeScript checks are rerun before the phase commit.
