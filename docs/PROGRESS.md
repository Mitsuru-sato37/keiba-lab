# Progress

Status: Current implementation handoff
Last updated: 2026-10-02

## Current phase

Expansion Slice 1 — 2022 one-day validation (completed on this branch).

Phase 7 — Logic Explorer mock (completed and merged in PR #6).

Phase 5 — backtest engine and leak guard (completed).

The Phase 4 acceptance slice is implemented against deterministic training
examples and immutable Phase 3 feature vectors. It does not require JRA-VAN
credentials, a use key, JV-Link installation, or login.

The Phase 5 acceptance slice adds deterministic walk-forward orchestration,
run-invalidating leak/version guards, a recommendation-before-result
capability gate, and append-only backtest manifests. It does not claim
live-equivalent betting performance when historical odds coverage is
insufficient.

The Phase 6 slice has been completed and merged in PR #5. The deterministic
Golden Race contracts, BUY/SKIP fixture cases, seeded gated pipeline,
immutable calculation artifacts, `TRACE-001` traces, policy replay, and
SQLite/PostgreSQL migration are implemented and verified.

The Phase 7 slice presents Today, Race, and Logic Explorer views against typed
Golden Race evidence and is merged in PR #6.

The first expansion slice adds a deterministic one-day 2022 validation fixture
and a replayable runner around the existing walk-forward orchestrator. It
does not claim real-world 2022 performance or official ROI.

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
- Walk-forward training manifest rejects test-year contamination and incomplete
  2019..test-year-1 windows.
- MODEL-BASE-001 deterministic gate-strength baseline emits coherent
  probabilities without
  current-race odds and persists model/training lineage.
- Prediction snapshots are append-only and preserve raw/constrained runner
  probabilities.
- Walk-forward backtest contracts enforce the 2022 first fold and expanding
  training windows through 2025.
- LEAK-001 through LEAK-004 and VERSION-001 are recorded as run-invalidating
  guard results.
- Backtest run, fold, guard, and artifact manifests are persisted by migration
  `0004_phase5_backtest_records` with append-only guards.
- Golden Race fixture v2 contains reproducible BUY and SKIP cases with odds
  kept outside ability-prediction inputs.
- Golden Race pipeline persists 11 pre-result stage artifacts and linked logic
  traces, with deterministic simulation seed and version lineage.
- Golden Race persistence migration `0005_phase6_golden_race` adds simulation,
  odds, candidate, recommendation-item, evaluation, and trace storage with
  append-only protections.
- Betting-policy replay preserves the original prediction checksum and
  separates prediction metrics from odds-dependent betting metrics.
- Phase 7 typed Golden Race fixture, Today/Race views, Logic Explorer evidence,
  deterministic navigation, and a first-2022 validation race summary are
  implemented without an API dependency.
- Expansion Slice 1 deterministic 2022 one-day fixture, input provider,
  replayable validation runner, and leak/gate/odds-coverage tests.

## Next implementation target

Expansion Slice 2 — all eligible 2022 races after a BASE-JV historical input
path is available.

## Constraints

- Keep the Windows/JV-Link boundary behind a provider interface.
- Preserve temporal, lineage, leak-prevention, and reproducibility invariants.
- Do not add external enrichment to BASE-JV.
- Never automate ticket purchase.
- Docker Desktop is installed and running through WSL 2. PostgreSQL validation
  is now active. The local SDK/tool directories are ignored by Git.

## Current handoff details

- Branch: `codex/expansion-2022-validation`.
- Phase 2 provider commits: `64ae7ca`, `fd3fa30`, and `797d59b`.
- Phase 1 branch and commit: `codex/phase-1-data-foundation` at `d6d5d3a`.
- No user input or external credential is currently required.

## Verified commands

- Phase 4 contract and baseline unit suite: 21 passed.
- Phase 4 prediction persistence suite: 4 passed.
- Phase 4 documentation contract suite: 4 passed.
- Full Python suite: 74 passed; Ruff and mypy passed.
- Phase 5 full Python suite: 118 passed; Ruff and mypy passed.
- Web test, production build, and typecheck passed.
- Collector shell static contract tests and real .NET build: passed.
- PostgreSQL Alembic migration: `0003_phase3_feature_logic_lineage` verified.
- SQLite migration and append-only validation: `0004_phase5_backtest_records` and
  `0005_phase6_golden_race` verified.
- Phase 6 targeted tests: contracts, pipeline, replay, persistence, result gate,
  and end-to-end flow pass.
- Phase 7 web suite: 10 tests passed; typecheck and production build passed.
- Expansion Slice 1 Python suite: 145 tests passed; Ruff and mypy passed.
- PostgreSQL Docker runtime validation: Docker Desktop 4.93.0 with PostgreSQL
  16 Alpine is healthy, and Alembic is at
  `0005_phase6_golden_race (head)`.
- PostgreSQL append-only validation for Phase 6 calculation artifacts passed;
  validation data was rolled back.
