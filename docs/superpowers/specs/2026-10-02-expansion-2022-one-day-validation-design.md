# 2022 One-Day Validation Design

Status: Proposed for implementation
Last updated: 2026-10-02

## Goal

Create the first expansion slice after the Golden Race: a deterministic,
replayable validation run for one eligible 2022 race day. The run must use the
existing walk-forward and leak-guard contracts so that the project can prove
the end-to-end validation order before historical BASE-JV data is connected.

This slice is a validation harness, not a claim about actual 2022 betting
performance.

## Shared understanding

- The first walk-forward test year remains 2022.
- Training for the 2022 fold contains only 2019, 2020, and 2021 examples.
- Predictions and recommendations are produced in chronological race order.
- Results and payouts are revealed only after the recommendation for the race
  has been persisted.
- Ability prediction inputs do not contain current-race odds.
- BUY and SKIP are both valid outcomes.
- Prediction metrics and odds-dependent betting metrics remain separate.
- Missing or incomplete odds coverage prevents an official betting result.
- The first implementation uses a versioned deterministic fixture with the
  same typed boundary expected from BASE-JV. JRA-VAN/JV-Link integration is
  explicitly outside this slice.

## Scope

### Included

1. A versioned one-day fixture representing the earliest eligible 2022
   validation day for this harness.
2. Training examples for 2019-2021 and multiple 2022 races ordered by their
   post/as-of time.
3. A provider or adapter that exposes the fixture through the existing
   `BacktestInputProvider` contract.
4. A repeatable runner/test scenario that invokes the existing
   `BacktestOrchestrator` for `test_years=(2022,)`.
5. Tests proving training-window isolation, chronological processing,
   recommendation-before-result gating, odds exclusion from ability inputs,
   deterministic replay, and incomplete-odds reporting.
6. Documentation and Logic Catalog references for this validation slice.

### Excluded

- Live or credentialed JRA-VAN/JV-Link collection.
- Scraping or external enrichment.
- All-2022 processing, later-year folds, or final 2019-2025 training.
- Model-family comparison or model tuning.
- New betting strategies or ticket purchase automation.
- A web UI for validation reports.
- Any official ROI or live-equivalent performance claim.

## Proposed approaches and decision

### Recommended: deterministic fixture through the existing backtest port

Add a small, versioned fixture and an adapter that implements the already
tested backtest input boundary. Reuse `BacktestOrchestrator`, the baseline
predictor contracts, and the existing result/odds gates. This is the smallest
vertical slice and proves the temporal behavior without requiring credentials
or an installed JV-Link runtime.

### Deferred: connect BASE-JV data immediately

This would exercise more production-like data, but the repository currently
has no imported historical BASE-JV dataset or credentialed collector contract
available to the deterministic test environment. Starting here would make
the first validation dependent on unavailable external state and would not
prove the core orchestration more reliably.

### Rejected: build the report UI first

The Logic Explorer already demonstrates the display path. A UI-first change
would not prove that the 2022 training window, reveal gate, and metrics
coverage rules hold in a run.

## Data and lineage contract

The fixture is immutable and carries:

- `fixture_version` and content checksum;
- source/provider identifier marking it as deterministic test data;
- target validation date and canonical race IDs;
- race post/as-of times in UTC, with Tokyo calendar semantics;
- raw observations with received/effective timestamps no later than their
  race as-of time;
- explicit result/payout payloads held behind the recommendation gate;
- odds coverage per race and decision point;
- feature, model, logic, training, and simulation seed lineage.

The adapter must not silently filter temporal violations. A malformed or
future-dated fixture record must cause the backtest run to become invalid via
the existing guards.

## Execution flow

```text
Load immutable one-day fixture
        |
Build BacktestSpec(test_years=(2022,))
        |
Request training examples for 2019-2021 only
        |
Fit deterministic baseline predictor
        |
For each 2022 race in chronological order:
  validate temporal, version, and odds guards
  predict without current-race odds
  persist prediction
  create and persist BUY or SKIP recommendation
  issue result capability
  reveal result/payout
        |
Report prediction metrics separately from odds-dependent metrics
```

The runner must rely on the existing orchestrator for this ordering rather
than duplicating gate logic in a fixture-specific path.

## Reporting behavior

The successful fixture run reports:

- run and fold identifiers;
- ordered race identifiers;
- guard results and artifact identifiers;
- prediction metrics when the run is valid;
- betting metrics only when the fixture's odds coverage is sufficient;
- an explicit coverage status when betting metrics are withheld;
- deterministic seed and fixture checksum.

If any leak or version guard fails, the complete run is `invalid`, official
metrics are unavailable, and the failure remains diagnostic only.

## Testing and acceptance criteria

The slice is accepted only when all of the following are true:

1. A fresh run requests training years exactly `(2019, 2020, 2021)`.
2. No 2022 race is predicted before the training manifest is created and
   persisted.
3. Races are processed by as-of time and canonical race ID.
4. A test that injects current-race odds into an ability input invalidates the
   run before prediction.
5. A test that omits recommendation persistence cannot reveal a result.
6. Repeating the same fixture, versions, and seeds produces the same ordered
   artifacts and report checksum.
7. BUY and SKIP recommendations are both represented in the fixture path.
8. Incomplete historical odds coverage preserves prediction metrics but
   withholds official betting metrics.
9. The full Python suite, linter, and type checker remain green.
10. The relevant specification and Logic Catalog entries describe the new
    validation slice without claiming real-world 2022 performance.

## Risks and boundaries

- The fixture validates orchestration and contracts, not data completeness or
  predictive quality of real historical races.
- Odds coverage in the fixture must not be presented as historical BASE-JV
  coverage.
- The adapter must remain behind `BacktestInputProvider` so a later BASE-JV
  implementation can replace it without changing the orchestrator.
- No code path may purchase or submit betting tickets.
