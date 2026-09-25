# Backtest Specification

Status: Current Source of Truth
Last updated: 2026-09-25

## Walk-forward schedule

| Fold | Train | Test |
|---|---|---|
| 1 | 2019-2021 | 2022 |
| 2 | 2019-2022 | 2023 |
| 3 | 2019-2023 | 2024 |
| 4 | 2019-2024 | 2025 |

The final operating model trains on 2019-2025. Data from 2026 onward is live or
ongoing validation data.

For every fold, execute in this order:

1. train without the test year;
2. generate and persist test-year predictions and recommendations in event
   order;
3. reveal actual results and payouts;
4. finalize metrics and immutable fold artifacts;
5. only then admit the test year to the next fold's training data.

## Golden Race progression

1. Golden Race fixture;
2. first eligible real 2022 race;
3. one race day;
4. all 2022;
5. 2023, 2024, and 2025 in order.

For a Golden Race, the gated sequence is:

```text
Data Snapshot -> Feature Snapshot -> Prediction -> Calibration -> Simulation
-> Bet Probability -> Odds Snapshot -> EV -> Strategy -> Money Allocation
-> persist Recommendation -> reveal Result -> Evaluation
```

## Mandatory guards

| Logic ID | Failure condition |
|---|---|
| LEAK-001 | A feature contains information effective or received after post/as-of time |
| LEAK-002 | The training manifest for a test year contains that year |
| LEAK-003 | Current-race odds enter an ability-model input |
| LEAK-004 | Result or payout is accessed before recommendation persistence |
| VERSION-001 | Feature, model, calibration where applicable, or logic version is missing |

Any failure sets the complete run to `invalid`. Metrics from invalid runs are
diagnostic only and cannot be reported as official performance.

## Evaluation

Prediction quality and betting quality are reported separately.

Prediction metrics include log loss, Brier score, calibration/reliability,
ranking quality, and coverage by decision point.

Betting metrics include hit rate, ROI, maximum drawdown/loss, maximum losing
streak, bet count, bet-type/strategy performance, and stability by month,
course, distance, and track condition.

## Replayability

One prediction snapshot can be replayed through 1/8 Kelly, 1/4 Kelly, fixed
stake, strategy variants, and SKIP-threshold variants without retraining.
Replay outputs receive a new betting-logic version and retain the original
prediction ID.

## Reproducibility manifest

Every run records code revision, configuration checksum, input snapshot
manifest, training rows/years, feature/model/logic versions, random seeds,
dependency lock checksum, guard results, and produced artifact IDs.
