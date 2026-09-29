# Product Specification

Status: Current Source of Truth
Last updated: 2026-09-25

## Purpose

`keiba-lab` is a personal web application for forecasting and evaluating all
JRA races. It connects data collection, point-in-time snapshots, feature
generation, ability prediction, virtual-race simulation, betting-combination
probabilities, odds and expected-value evaluation, money management,
walk-forward backtesting, and auditable calculation traces.

It supports decisions; it does not purchase tickets automatically.

## Users and primary workflow

The sole initial user reviews the day's races, opens a race, and receives one
of two top-level outcomes:

- `BUY`: one or more proposed bets with stake and risk information.
- `SKIP`: a structured reason explaining either lack of market value or lack
  of prediction reliability.

Forecasts are recalculated at the following decision points:

1. previous day;
2. 30 minutes before post time;
3. 10 minutes before post time;
4. immediately after manually entered current odds.

Manual odds update only reruns market evaluation, betting, and allocation when
the underlying race snapshot has not otherwise changed.

## Product principles

- Ability prediction and market valuation are separate systems.
- Current-race odds are never an ability-model feature.
- Every displayable explanation is backed by stored inputs, intermediate
  values, reason codes, and versioned logic. An LLM must not invent reasons.
- Simpler models are the default. A more complex feature, model, blend, or
  pace rule is adopted only after stable future-period improvement.
- BASE-JV remains reproducible even after optional enrichment is added.

## Strategies

The Race page presents Stable, Balanced, Longshot, and an overall
recommendation. Initial race bankroll caps are:

| Strategy | Initial cap | Intent |
|---|---:|---|
| Stable | 2.0% | Fewer selections, higher hit probability, low uncertainty |
| Balanced | 3.0% | Trade off probability, EV, payout, and selection count |
| Longshot | 1.5% | Small positive-EV exposure to high-payout outcomes |

These are safe initial values, not optimized constants. Tune them using
2022-2024 only and freeze them before the 2025 test.

## Information architecture

1. Today
2. Race
3. Logic Explorer
4. Backtest
5. Performance
6. Settings

The Race summary shows BUY/SKIP, confidence, data status, last calculation
time, three strategies, and the overall recommendation. Drill-down follows:
Horse Evaluation -> Finish Probabilities -> Bet Probabilities -> Odds -> EV ->
Decision -> Stake.

## Success criteria

- Walk-forward evaluation runs for 2022, 2023, 2024, and 2025 in order.
- No official run has a failed leak or version guard.
- Any recommendation can be reproduced from data snapshot through money
  allocation.
- Logic Explorer can navigate from UI output to Logic ID, specification,
  implementation reference, inputs, outputs, and validation evidence.

## Explicit exclusions for the initial product

- Automatic ticket purchase.
- Dependence on scraped sites such as netkeiba.
- Neural networks or a dedicated giant trifecta model.
- Hand-authored complex pace/scenario rules in the initial simulation.
- Multi-user accounts, cloud tenancy, Kafka, and independently deployed
  microservices.

## Phase 1 vertical-slice scope

Phase 1 is a fixture-backed, win-only slice. It supports Today -> Race ->
prediction evidence -> manual odds evaluation and exposes `BUY`, `SKIP`, or
`WAIT`. `WAIT` means required odds/data is unavailable or stale and another
update is expected; it is distinct from an evaluated but non-actionable
`SKIP`. No live JV-Link connection or automatic purchase is part of this
slice.
