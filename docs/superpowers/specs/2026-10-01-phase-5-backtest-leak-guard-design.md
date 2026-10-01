# Phase 5 Backtest Engine and Leak Guard Design

Status: Proposed implementation design
Last updated: 2026-10-01

## Goal

Build a deterministic walk-forward backtest core that executes the existing
prediction contracts in the required event order, rejects temporal, training,
odds, result-access, and version leaks, and records an immutable run manifest.

This phase proves orchestration and safety with deterministic fixtures. It does
not claim live-equivalent betting performance, connect to JRA-VAN, automate
ticket purchase, or introduce external enrichment.

## Scope and acceptance criteria

The implementation covers:

- the Phase 5 fold schedule: 2019-2021 -> 2022, then expanding training
  windows through the 2025 test fold;
- immutable run, fold, guard-result, and artifact-manifest contracts;
- orchestration of training, prediction, recommendation persistence, result
  reveal, and metric finalization in that order;
- LEAK-001 through LEAK-004 and VERSION-001 as run-invalidating guards;
- a capability-based result repository boundary that cannot reveal results
  before all recommendations for the race are persisted;
- deterministic replay and separate prediction-quality and betting-quality
  reporting, including historical odds coverage limitations;
- repository and migration tests for append-only backtest records.

The implementation does not cover CatBoost, calibration, a production betting
policy, broad historical data loading, UI screens, or ticket purchase.

## Invariants

1. The first test fold is 2022 and its training years are exactly 2019, 2020,
   and 2021. No test year is admitted to training before its fold is complete.
2. A feature or observation is eligible only when both received and effective
   timestamps are at or before the fold's `as_of_time`, and it is not
   superseded at that time.
3. Current-race odds are never passed to ability training or prediction.
4. Results and payouts are inaccessible until the corresponding recommendation
   identifiers have been durably persisted.
5. A failed guard invalidates the complete run. Metrics from an invalid run are
   diagnostic only and cannot be reported as official performance.
6. Run, fold, guard, and artifact manifests are append-only and retain data,
   feature, model, logic, training, seed, and code lineage.
7. Prediction-quality metrics and betting-quality metrics remain separate. A
   betting report must include odds coverage and must not imply ROI validity
   when coverage is insufficient.

## Architecture

### Application contracts

The application layer owns typed immutable contracts for:

- `WalkForwardFold`: one test year and its exact contiguous training window;
- `BacktestSpec`: ordered folds, as-of policy, configuration checksum, random
  seeds, and required version identifiers;
- `BacktestManifest`: canonical run inputs and checksum;
- `GuardResult`: guard ID, version, status, checked inputs, and diagnostic
  details;
- `BacktestRunResult`: terminal status, fold results, guard results, metrics,
  and produced artifact IDs;
- an opaque `ResultAccessCapability` issued only after recommendation
  persistence has been verified.

These contracts reject malformed windows, missing versions, duplicate IDs, and
non-deterministic manifest inputs before orchestration begins.

### Guard layer

The guard layer exposes small validators with stable Logic IDs:

- `LEAK-001`: temporal eligibility of every input artifact;
- `LEAK-002`: training manifest contains only years before the test year and
  matches the fold window;
- `LEAK-003`: ability inputs contain no current-race odds fields or odds
  records;
- `LEAK-004`: result access requires a valid recommendation-persistence
  capability for the race;
- `VERSION-001`: required feature, model, calibration-when-used, logic, and
  implementation versions are present and mutually consistent.

The orchestrator records every guard result. A failed result raises a typed
guard error and transitions the run to `invalid`; the error is retained as
diagnostic data rather than being silently skipped.

### Orchestrator

`BacktestOrchestrator` receives provider, trainer, prediction, recommendation,
result, metric, clock, and persistence dependencies through explicit ports.
It does not read an unrestricted database session. For each fold it:

1. creates and persists the fold manifest;
2. validates the training window, versions, temporal inputs, and odds boundary;
3. trains without the test year;
4. processes test races in chronological order, persisting prediction and
   recommendation artifacts before requesting results;
5. obtains the result capability only after persistence confirmation;
6. reveals results and computes prediction metrics and, where coverage allows,
   betting metrics;
7. persists the fold artifact and admits the completed test year to the next
   fold's training pool.

Any guard or stage failure invalidates the run and prevents official metric
finalization. Retry-safe IDs and append-only stores prevent a retry from
overwriting a previous artifact.

### Persistence

Add a migration and SQLAlchemy models/repositories for:

- `backtest_runs`: immutable run manifest, status, timestamps, and checksum;
- `backtest_folds`: fold window, status, manifest checksum, and run lineage;
- `backtest_guard_results`: guard ID/version, pass/fail status, checked input
  IDs, and diagnostic payload;
- `backtest_artifacts`: immutable produced artifact references and kind.

SQLite and PostgreSQL use the existing append-only trigger convention. The
repository layer also rejects update and delete attempts. JSON manifests use a
canonical serialization so identical inputs produce identical checksums.

## Data flow

```text
BacktestSpec
    -> immutable BacktestManifest
    -> ordered WalkForwardFold
    -> guard checks
    -> train on prior years only
    -> prediction snapshot
    -> recommendation persisted
    -> ResultAccessCapability
    -> result/payout reveal
    -> separate metrics
    -> immutable fold/run artifact manifests
```

Result access is represented by a capability object rather than a boolean
flag. The result port accepts the capability as a required argument, making
premature access fail at the interface boundary as well as in tests.

## Failure handling

- Invalid fold windows, missing versions, temporal leaks, odds leaks, and
  premature result access are typed failures tied to their Logic ID.
- The run status changes to `invalid` on the first guard failure or stage
  failure; later folds do not run.
- Invalid runs preserve guard diagnostics and input lineage but expose no
  official performance summary.
- A missing or incomplete historical odds set records coverage limitations and
  allows prediction metrics to be reported separately from betting metrics.
- Existing immutable artifacts remain untouched when a retry or newer model
  produces a new run.

## Verification strategy

Tests are written before implementation and include:

- positive fold schedule and expanding-window tests;
- negative tests for each LEAK-001 through LEAK-004 and VERSION-001;
- a test proving one failed guard invalidates the entire run;
- timestamp boundary tests for received, effective, and superseded inputs;
- a test proving current-race odds never reach the ability trainer;
- result access denial before persistence and success after persistence;
- deterministic seed/checksum replay tests and chronological race ordering;
- append-only repository and SQLite/PostgreSQL migration tests;
- documentation and Logic Catalog references for the new implementation.

The full Python suite, Ruff, mypy, web checks, and migration validation remain
required before opening a pull request.

## Logic and trace references

Phase 5 implementation references will be added to `docs/LOGIC_CATALOG.md`
for the backtest orchestrator, guard layer, and immutable manifest persistence.
Each material stage will retain its Logic ID, version, input artifact IDs,
output IDs, status, and validation test reference so a later Logic Explorer
screen can trace a result without recomputing it.
