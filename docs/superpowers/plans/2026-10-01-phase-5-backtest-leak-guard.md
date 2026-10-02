# Phase 5 Backtest Engine and Leak Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a deterministic walk-forward backtest engine that enforces the
required event order, invalidates a run on any temporal/training/odds/result/
version violation, and persists immutable run lineage.

**Architecture:** Keep the contracts, guard decisions, result capability, and
orchestration in the application layer. Inject training, prediction,
recommendation, result, metric, and persistence ports so deterministic fixtures
can exercise the complete flow without JRA-VAN or live data. Add one append-only
SQLAlchemy/Alembic persistence slice for runs, folds, guard results, and
artifacts.

**Tech Stack:** Python 3.12, dataclasses and typing.Protocol, pytest,
SQLAlchemy, Alembic, SQLite migration tests, PostgreSQL migration validation,
Ruff, mypy, and the existing TypeScript/Vite checks.

**Spec:** `docs/superpowers/specs/2026-10-01-phase-5-backtest-leak-guard-design.md`

## Global Constraints

- The first walk-forward test year is 2022; train only on 2019-2021 before generating any 2022 prediction.
- A calculation may read only data effective and received at or before its `as_of_time`.
- Ability prediction never consumes current-race odds.
- Results and payouts are unavailable until the corresponding recommendation has been persisted.
- Raw observations, snapshots, predictions, and recommendations are append-only. Never overwrite a historical prediction with a newer model.
- Every persisted calculation carries data/snapshot lineage plus feature, model, and logic versions.
- A failed leak or version guard invalidates the entire backtest run.
- BUY and SKIP are equally valid recommendation outcomes. Distinguish a market-value SKIP from an unreliable-prediction state.
- Keep the Windows/JV-Link boundary behind a provider interface and run the core against deterministic fixtures.
- Use UTC for stored instants and `Asia/Tokyo` for JRA calendar semantics.
- Keep prediction generation separate from betting-policy replay.
- Do not add external enrichment to the BASE-JV path and never automate ticket purchase.
- Write tests before implementation, including temporal-boundary and negative leak tests.
- Do not claim backtest performance when historical odds coverage is insufficient; report prediction metrics and odds-coverage limitations separately.

## Review Focus

- An input exactly at `as_of_time` is eligible, while an input one instant after it is a LEAK-001 failure.
- A superseded input at the boundary is rejected rather than silently filtered.
- A partial recommendation persistence failure must not grant result access or allow the run to succeed.
- A test race containing odds must be rejected even when the odds appear inside nested feature payloads.
- Repeating the same seeded run must produce the same manifest checksum and artifact IDs without mutating an earlier run.

---

### Task 1: Walk-forward contracts and immutable run manifests

**Files:**
- Create: `packages/application/src/keiba_application/backtest.py`
- Modify: `packages/application/src/keiba_application/errors.py`
- Test: `tests/unit/test_backtest_contracts.py`

**Interfaces:**
- Produces `WalkForwardFold.create(test_year: int) -> WalkForwardFold` with
  `training_years == tuple(range(2019, test_year))` and rejection below 2022.
- Produces `BacktestSpec.create(...) -> BacktestSpec` for ordered test years,
  version IDs, configuration checksum, code revision, dependency checksum, and
  deterministic seeds.
- Produces `BacktestManifest.create(spec, input_snapshot_ids, training_example_ids) -> BacktestManifest` with a canonical SHA-256 checksum.
- Produces immutable `GuardResult`, `FoldManifest`, and `BacktestRunResult`
  value objects with explicit `PENDING`, `RUNNING`, `SUCCEEDED`, and `INVALID`
  status values.

- [ ] **Step 1: Write the failing tests** for the 2022-2025 fold schedule,
  rejection of a missing/extra training year, duplicate fold IDs, missing
  required versions, canonical checksum stability, and invalid-run status.
- [ ] **Step 2: Run the contract tests** with
  `./.venv/Scripts/python.exe -m pytest tests/unit/test_backtest_contracts.py -q`.
  Confirm they fail because the contracts do not exist.
- [ ] **Step 3: Implement the frozen/slotted dataclasses and typed errors** in
  `backtest.py` and `errors.py`. Validate exact fold windows, nonempty IDs,
  required version identifiers, unique inputs, and canonical JSON checksums.
- [ ] **Step 4: Re-run the focused contract tests** and confirm they pass.
- [ ] **Step 5: Run Ruff and mypy** on the changed packages and tests.
- [ ] **Step 6: Commit** with `feat: add backtest run contracts`.

### Task 2: Leak guards and result-access capability

**Files:**
- Create: `packages/application/src/keiba_application/backtest_guards.py`
- Modify: `packages/application/src/keiba_application/errors.py`
- Test: `tests/unit/test_backtest_guards.py`

**Interfaces:**
- `BacktestGuards.check_temporal_eligibility(records, as_of_time) -> GuardResult`.
- `BacktestGuards.check_training_window(manifest, fold) -> GuardResult`.
- `BacktestGuards.check_ability_inputs(inputs) -> GuardResult`.
- `BacktestGuards.check_versions(required_versions, artifact_versions) -> GuardResult`.
- `BacktestGuards.require_pass(results) -> None`, raising a typed guard error.
- `RecommendationPersistenceGate.issue(recommendation_ids, persisted_ids) -> ResultAccessCapability`.
- `ResultAccessCapability.allows(race_id) -> bool`, with no public constructor
  that can be used to bypass the gate in normal application code.

- [ ] **Step 1: Write failing tests** for LEAK-001 boundary/supersession
  behavior, LEAK-002 test-year contamination, LEAK-003 direct and nested odds,
  VERSION-001 missing/mismatched versions, and LEAK-004 capability denial for
  missing or partially persisted recommendations.
- [ ] **Step 2: Run the focused guard tests** and confirm expected failures.
- [ ] **Step 3: Implement the five guard checks** with stable guard IDs and
  diagnostic checked-input IDs. Reuse the existing temporal and odds rules
  rather than duplicating alternate definitions.
- [ ] **Step 4: Implement the recommendation persistence gate** so a capability
  is issued only when every requested recommendation ID is persisted; result
  access for another race is denied.
- [ ] **Step 5: Re-run the focused guard tests**, then the existing temporal,
  prediction, and result-gate tests.
- [ ] **Step 6: Commit** with `feat: add backtest leak guards`.

### Task 3: Deterministic backtest orchestration

**Files:**
- Create: `packages/application/src/keiba_application/backtest_engine.py`
- Create: `tests/unit/test_backtest_engine.py`
- Modify: `packages/application/src/keiba_application/backtest.py` only if a
  shared race/recommendation protocol must be added.

**Interfaces:**
- `BacktestRace` contains race ID, test year, as-of time, feature vectors,
  result payload, and odds-coverage metadata.
- `BacktestTrainer.fit(manifest, examples) -> BacktestPredictor`.
- `BacktestPredictor.predict(race) -> PredictionSnapshot`.
- `RecommendationService.create(prediction) -> RecommendationArtifact`.
- `BacktestArtifactStore.persist_prediction(...)` and
  `persist_recommendation(...) -> None`.
- `ResultReader.reveal(race_id, capability) -> ResultArtifact`.
- `BacktestOrchestrator.run(spec, input_provider, services) -> BacktestRunResult`.

- [ ] **Step 1: Write failing tests** for chronological race processing,
  prediction before recommendation before result, expanding training windows,
  no admission of a test year before fold completion, deterministic seeded
  output, separate prediction/betting metric coverage, and whole-run
  invalidation after one guard failure.
- [ ] **Step 2: Run the orchestration tests** and confirm they fail because the
  orchestrator and ports do not exist.
- [ ] **Step 3: Implement minimal injected protocols and deterministic fixture
  adapters**. The orchestrator must record each guard, stop later folds after
  the first invalidating failure, issue result capability only after the store
  confirms all recommendations, and finalize official metrics only for a
  successful run.
- [ ] **Step 4: Add a test that verifies current-race odds never reach the
  trainer or predictor**, even when the recommendation service receives market
  data later in the flow.
- [ ] **Step 5: Re-run the focused orchestration tests and the full Python
  suite**.
- [ ] **Step 6: Commit** with `feat: add deterministic backtest orchestrator`.

### Task 4: Immutable backtest persistence and migration

**Files:**
- Modify: `packages/infrastructure/src/keiba_infrastructure/schema.py`
- Modify: `packages/infrastructure/src/keiba_infrastructure/repositories.py`
- Create: `alembic/versions/0004_phase5_backtest_records.py`
- Test: `tests/integration/test_backtest_persistence.py`
- Modify: `tests/integration/test_migration_roundtrip.py` if the migration
  contract enumerates expected tables.

**Interfaces:**
- SQLAlchemy tables: `backtest_runs`, `backtest_folds`,
  `backtest_guard_results`, and `backtest_artifacts`.
- `BacktestPersistenceRepository.add_run(...)`, `add_fold(...)`,
  `add_guard_result(...)`, and `add_artifact(...)`.
- `update(...)` and `delete(...)` on all four repositories raise
  `AppendOnlyViolationError`.

- [ ] **Step 1: Write failing migration and repository tests** for table
  creation, foreign-key lineage, immutable inserts, update/delete rejection,
  manifest checksum persistence, and all four guard statuses.
- [ ] **Step 2: Run the focused integration tests** and confirm they fail on
  the missing migration/models/repository.
- [ ] **Step 3: Add the SQLAlchemy models and Alembic migration** with UTC
  timestamps, JSON manifests, checksums, status constraints, foreign keys,
  indexes, and SQLite/PostgreSQL append-only triggers.
- [ ] **Step 4: Implement repository inserts and explicit update/delete guards**
  with canonical manifest payloads.
- [ ] **Step 5: Run the focused persistence tests and migration validation** on
  SQLite and the available PostgreSQL environment.
- [ ] **Step 6: Commit** with `feat: persist immutable backtest manifests`.

### Task 5: Source-of-truth documentation and final verification

**Files:**
- Modify: `docs/BACKTEST_SPEC.md`
- Modify: `docs/DATA_SPEC.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/LOGIC_CATALOG.md`
- Modify: `docs/PROGRESS.md`
- Create: `tests/unit/test_phase5_documentation.py`

- [ ] **Step 1: Write failing documentation tests** for the Phase 5 contract,
  implementation references, migration ID, guard IDs, and invalid-run/reporting
  limitations.
- [ ] **Step 2: Run the documentation tests** and confirm the new references
  are absent.
- [ ] **Step 3: Update all source-of-truth documents** with stable module and
  symbol references, validation test references, migration details, and the
  separate odds-coverage reporting rule.
- [ ] **Step 4: Run documentation tests and the complete verification set:**
  `./.venv/Scripts/python.exe -m pytest -q --basetemp tmp/pytest-phase5-final -p no:cacheprovider`,
  Ruff, mypy, `pnpm test`, `pnpm build`, `pnpm typecheck`, and migration
  validation.
- [ ] **Step 5: Review the complete diff against `origin/main`**, confirm the
  worktree is clean, and record the handoff in `docs/PROGRESS.md`.
- [ ] **Step 6: Commit** with `docs: record phase 5 backtest handoff`.

## Commit sequence

1. `feat: add backtest run contracts`
2. `feat: add backtest leak guards`
3. `feat: add deterministic backtest orchestrator`
4. `feat: persist immutable backtest manifests`
5. `docs: record phase 5 backtest handoff`

Each commit must have its task's focused tests passing before the next task
starts. The branch must be fetched against `origin/main` before opening a pull
request, and no known-failing work may be pushed as complete.
