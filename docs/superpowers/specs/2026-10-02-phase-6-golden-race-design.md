# Phase 6 Golden Race Design

## Status

Approved design for implementation on `codex/phase-6-golden-race`.

## Purpose

Phase 6 completes one deterministic, end-to-end Golden Race through the
application and persistence layers. The goal is to prove that a prediction can
be reproduced, converted into a BUY or SKIP recommendation, persisted with an
auditable trace, and evaluated only after the recommendation has been saved.

This phase uses versioned synthetic fixtures. It does not claim to predict an
actual 2022 JRA race and it does not introduce ticket-purchase behavior.

## Goals

- Run the full gated sequence defined by `BACKTEST_SPEC.md`:

  `Data Snapshot -> Feature Snapshot -> Prediction -> Calibration ->
  Simulation -> Bet Probability -> Odds Snapshot -> EV -> Strategy -> Money
  Allocation -> persist Recommendation -> reveal Result -> Evaluation`

- Persist immutable stage artifacts and logic traces that link each output to
  its inputs, lineage, feature/model/logic versions, and deterministic seed
  where applicable.
- Prove that the same fixture and seed produce the same prediction,
  recommendation, and evaluation inputs.
- Exercise both valid recommendation outcomes: BUY and SKIP. SKIP must retain
  an explicit reason and must be distinguishable from an unreliable prediction
  state.
- Replay betting policies against persisted predictions and market inputs
  without retraining or regenerating the ability prediction.
- Enforce the existing temporal, version, append-only, and recommendation
  persistence invariants.

## Non-goals

- Connecting JV-Link or requiring a JRA-VAN subscription.
- Importing actual historical 2022 race data or asserting live odds coverage.
- Building the user interface; that remains Phase 7.
- Automating ticket purchase or sending any order to a betting service.
- Adding external enrichment to the BASE-JV path.

## Fixture design

The Golden Race fixture remains deterministic and versioned. The existing
fixture version and seed are extended only through a deliberate fixture-version
change; historical fixture records are never overwritten.

The fixture contains two independent cases:

1. A value case whose strategy result is BUY.
2. A no-value or capped-capital case whose strategy result is SKIP with a
   persisted reason such as `SKIP_NO_VALUE` or `SKIP_CAPITAL`.

Each case supplies the race identity, effective and received timestamps,
runner features available at the as-of time, deterministic race outcome,
market odds received before the odds snapshot time, expected payouts, and the
expected result contract. Odds are exposed only to the market-value stages;
the ability predictor receives no current-race odds.

## Application flow

The application orchestrator executes one stage at a time and passes typed
stage outputs to the next stage. Each stage returns a value object containing
the stage identity, input references, output payload, lineage, versions,
calculation timestamp, and status.

The orchestrator must reject out-of-order calls and must stop the entire run
when a temporal or version guard fails. It must persist the recommendation
before it allows a result or payout lookup. Evaluation receives only the
persisted recommendation and the now-available result.

Prediction generation and betting-policy replay are separate entry points:

- Prediction generation creates the immutable ability prediction and market
  inputs once.
- Policy replay consumes those persisted inputs and produces a new,
  versioned policy result without retraining.

## Persistence model

Phase 6 adds the minimum persistence needed for the Golden Race while keeping
all historical records append-only. The exact SQL names may follow the current
schema conventions, but the persisted concepts are:

- simulation and simulation-result records, including seed and convergence
  metadata;
- odds snapshot records with received/as-of times and coverage metadata;
- bet candidates with probability, odds, EV, uncertainty, and source links;
- recommendation items and recommendation status/reason;
- evaluation records separated into prediction metrics and betting metrics;
- logic traces with stage order, input/output references, lineage, versions,
  duration, status, and error information.

The recommendation persistence boundary is the authorization point for result
and payout access. A result repository call without a persisted recommendation
for the same race and run must fail deterministically.

## Logic and version requirements

The implementation uses the catalogued logic IDs where applicable:

- `SIM-001` for seeded virtual-race simulation;
- `EV-001` for conservative odds and EV calculation;
- `BET-001` for strategy candidate selection;
- `MONEY-001` for one-quarter Kelly and safety-cap allocation;
- `TRACE-001` for persisted calculation traces.

Every persisted calculation carries data/snapshot lineage plus feature, model,
and logic versions. A replay changes the policy/logic lineage and creates new
records; it never overwrites the original prediction or recommendation.

## Verification requirements

Tests are written before production implementation for each slice. Required
coverage includes:

- deterministic replay with the same fixture version and seed;
- stage ordering and trace-link integrity;
- temporal boundary inclusion/exclusion and negative current-odds leakage;
- version mismatch invalidating the complete run;
- BUY and SKIP outcomes, including explicit skip reasons;
- EV and money-allocation boundary, cap, and rounding behavior;
- rejection of result/payout access before recommendation persistence;
- append-only rejection for each new Phase 6 record type;
- policy replay without a second prediction/training call;
- separation of prediction metrics from betting metrics when odds coverage is
  incomplete.

The narrow Phase 6 tests run first, followed by the repository-wide Python,
web, lint, type, migration, and PostgreSQL verification already required by
the repository.

## Acceptance criteria

Phase 6 is complete when:

1. A versioned Golden Race fixture runs end-to-end through evaluation.
2. Repeating the run with the same fixture and seed produces the same
   persisted stage outputs and recommendation decision.
3. Both BUY and SKIP are demonstrated with auditable reasons.
4. A pre-persistence result lookup fails, while the same lookup succeeds after
   recommendation persistence.
5. All stage traces and lineage links are persisted and validated.
6. A betting-policy replay completes without retraining or changing the
   original prediction.
7. A failed leak or version guard invalidates the full run.
8. Specifications, logic references, fixture documentation, and verification
   results are updated in the same change.

