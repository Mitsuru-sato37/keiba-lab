# Phase 6 Golden Race Implementation Plan

> **Execution note:** Implement this plan in the current workspace on
> `codex/phase-6-golden-race`. Follow test-first development for every slice:
> add the failing test, run it to show RED, implement the smallest change,
> rerun to show GREEN, then run the relevant regression tests.

## Baseline and checkpoints

- Confirm the worktree is clean and `HEAD` equals `origin/main` before the
  first implementation commit.
- Keep the approved design at
  `docs/superpowers/specs/2026-10-02-phase-6-golden-race-design.md` as the
  behavior authority for this phase.
- Commit each coherent, passing slice with its tests and documentation. Push
  after the first passing vertical slice and at the final clean handoff.
- Do not mix Phase 7 UI work into this branch.

## Slice 1: typed Golden Race contracts and fixture loading

### Tests first

Add `tests/unit/test_golden_race_contracts.py` covering:

- immutable stage outputs include stage ID, input references, lineage,
  feature/model/logic versions, calculation time, status, and error data;
- fixture version and seed are required and stable;
- BUY and SKIP scenarios carry explicit expected decisions/reasons;
- timestamps are UTC and fixture observations obey effective/received
  boundaries;
- odds are represented as a later market input and are not part of the
  ability-prediction input contract.

Run the new test file and capture the expected RED failure before adding
production code.

### Implementation

- Add typed application contracts in a focused module such as
  `packages/application/src/keiba_application/golden_race.py` (or split the
  value objects into a nearby module if that keeps imports small).
- Reuse `UtcInstant`, existing prediction contracts, lineage/version IDs, and
  append-only repository conventions instead of creating duplicate concepts.
- Add a deterministic fixture loader/adapter under
  `packages/infrastructure/src/keiba_infrastructure/` that reads the versioned
  Golden Race fixture without requiring JV-Link or a database connection.
- Extend the fixture documentation and data with two explicit cases, using a
  new fixture version rather than mutating the meaning of the old version.

### Verification and commit

Run the new unit tests plus the existing snapshot/prediction contract tests.
Commit the typed contracts and fixture update as one coherent slice.

## Slice 2: deterministic gated calculation pipeline

### Tests first

Add `tests/unit/test_golden_race_pipeline.py` covering:

- the exact stage order from the approved design;
- deterministic simulation for the same fixture version and seed;
- a changed seed producing a different simulation checksum;
- current-race odds never reaching the ability predictor;
- temporal boundary and negative leak cases;
- a failed leak or version guard marks the complete run invalid and prevents
  downstream recommendation/evaluation;
- BUY and SKIP strategy outcomes, including `SKIP_NO_VALUE` or
  `SKIP_CAPITAL`.

Run the file to show RED.

### Implementation

- Implement a small orchestrator with explicit ports for feature creation,
  prediction, simulation, odds access, recommendation persistence, result
  reveal, and evaluation.
- Keep ability prediction before market-value stages and pass odds only to
  bet-probability/EV/strategy stages.
- Implement the deterministic simulation under `SIM-001`, conservative EV
  under `EV-001`, strategy selection under `BET-001`, and capped one-quarter
  Kelly allocation under `MONEY-001`.
- Reuse Phase 5 guard behavior and make guard failure invalidate the complete
  Golden Race run.
- Return immutable stage results; do not overwrite an earlier stage artifact
  when a replay is requested.

### Verification and commit

Run the pipeline unit tests and the existing Phase 4/5 backtest and prediction
tests. Commit the passing in-memory vertical slice before adding database
tables.

## Slice 3: persisted artifacts, traces, and result gate

### Tests first

Add integration tests in:

- `tests/integration/test_golden_race_persistence.py` for persisted stage
  artifacts, lineage links, logic IDs, versions, and trace order;
- `tests/integration/test_golden_race_result_gate.py` for result/payout access
  failing before recommendation persistence and succeeding afterward;
- append-only tests for new simulation, odds, candidate, recommendation-item,
  evaluation, and trace records.

Use the existing SQLite test setup and PostgreSQL migration roundtrip pattern.
Run these tests to show RED.

### Implementation

- Extend `packages/infrastructure/src/keiba_infrastructure/schema.py` with the
  minimum tables for simulation/results, odds snapshots, bet candidates,
  recommendation items, evaluations, and logic traces. Reuse the existing
  `Recommendation` and `Result` tables where their contracts already match.
- Add Alembic migration `0005_phase6_golden_race.py` with constraints,
  foreign keys, and database-level append-only protections consistent with
  Phase 5.
- Add repository methods in
  `packages/infrastructure/src/keiba_infrastructure/repositories.py` for
  append-only writes and trace-linked reads.
- Keep the recommendation persistence boundary in the result repository:
  result and payout reads/writes must verify the matching persisted
  recommendation and race ID.
- Add `TRACE-001` trace creation and stage-link validation without recomputing
  values when traces are read.

### Verification and commit

Run the integration tests against SQLite and the Docker PostgreSQL service,
then run the migration upgrade/downgrade or roundtrip checks supported by the
repository. Commit the persistence slice only after append-only and gate tests
pass.

## Slice 4: policy replay and separated evaluation

### Tests first

Add `tests/unit/test_golden_race_replay.py` and extend integration coverage to
prove:

- policy replay reads persisted prediction/market artifacts;
- the trainer/predictor is not called during replay;
- replay writes a new policy-versioned result and leaves the original
  prediction/recommendation unchanged;
- prediction metrics remain available when odds coverage is incomplete;
- betting metrics are withheld or marked unavailable when odds coverage is
  insufficient.

Run the tests to show RED.

### Implementation

- Add a replay entry point separate from prediction generation.
- Persist replay lineage, policy/logic version, deterministic seed, and
  coverage limitations.
- Add evaluation contracts that expose prediction and betting metrics as
  separate result groups.

### Verification and commit

Run the new replay tests and all Phase 6 unit/integration tests. Commit this
slice before final documentation updates.

## Slice 5: specifications, logic catalog, and handoff

- Update `docs/BACKTEST_SPEC.md`, `docs/DATA_SPEC.md`,
  `docs/LOGIC_CATALOG.md`, `docs/ROADMAP.md`, and `docs/PROGRESS.md` with the
  accepted Phase 6 behavior, schema concepts, validation references, and any
  odds-coverage limitation.
- Update `fixtures/golden-race/README.md` with fixture version, seed,
  scenarios, and reproducibility instructions.
- Add or update documentation tests so the current phase and Logic IDs cannot
  silently drift.
- Run the narrowest tests first, then the complete required verification:
  Python tests, Ruff, mypy, web tests/build/typecheck, Alembic checks, and
  PostgreSQL append-only validation.
- Review the final diff, confirm no automated ticket purchase path exists, and
  push the verified branch for a Phase 6 pull request.

## Expected deliverables

- Deterministic versioned Golden Race fixture with BUY and SKIP cases.
- Typed, guarded, reproducible end-to-end pipeline.
- Persisted immutable stage artifacts and `TRACE-001` logic traces.
- Result/payout persistence gate tests.
- Betting-policy replay without retraining.
- Updated specifications, logic catalog, fixture documentation, and verified
  Phase 6 branch ready for review.

