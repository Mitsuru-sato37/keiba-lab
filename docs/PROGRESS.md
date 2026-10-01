# Progress

Status: Current handoff
Last updated: 2026-10-01

## Current phase

Phase 2 — JRA-VAN adapter interface.

Phase 0 and Phase 1 are complete and saved on their Git branches. Phase 2
currently covers the Python provider boundary and deterministic collector
import contract.

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
- Provider record type/key preservation through raw observation persistence.

## Next implementation target

Complete the remaining Phase 2 slice: document and test the .NET 8 x64
collector shell/import handoff, then add idempotent batch promotion at the
application persistence boundary. Stop before requiring JV-Link installation,
membership, use key, or login.

## Constraints

- Keep the Windows/JV-Link boundary behind a provider interface.
- Preserve temporal, lineage, leak-prevention, and reproducibility invariants.
- Do not add external enrichment to BASE-JV.
- Never automate ticket purchase.
- Docker CLI is not installed in this environment; PostgreSQL validation is
  deferred, while offline compose and SQLite integration checks remain active.

## Current handoff details

- Branch: `codex/phase-2-jra-van-adapter`.
- Phase 1 branch and commit: `codex/phase-1-data-foundation` at `d6d5d3a`.
- No user input or external credential is currently required.

## Verified commands

- Focused Phase 2 tests: 10 passed.
- Full Python/TypeScript checks are rerun before the phase commit.
