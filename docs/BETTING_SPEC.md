# Betting and Money Management Specification

Status: Current Source of Truth
Last updated: 2026-09-25

## Bet candidate contract

Each candidate contains bet type, canonical combination, model probability,
current odds, predicted final odds, conservative probability, conservative
odds, expected value, uncertainty, overlap group, odds snapshot ID, and logic
version.

Market evaluation occurs only after ability prediction. A manual odds update
creates a new odds snapshot and reevaluates downstream candidates; it does not
mutate the ability prediction.

## Decision states

- `BUY`: one or more candidates survive all value, reliability, and capital
  checks.
- `SKIP_NO_VALUE`: prediction is usable but conservative EV is insufficient.
- `SKIP_UNRELIABLE`: data/model reliability is insufficient.
- `SKIP_CAPITAL`: allocation constraints prevent a valid stake.
- `SKIP_STALE`: a material event occurred and recalculation is incomplete.

Reason codes are stored as structured values, not display-only prose.

## Phase 1 win-only evaluation

The fixture-backed Phase 1 evaluator supports only `WIN` candidates. After
ability prediction, it computes the exact Decimal formulas:

```text
fair_odds = 1 / win_probability
EV = win_probability * current_odds
```

Missing or stale odds produce `WAIT`; an evaluated EV below the injected,
versioned policy threshold produces `SKIP_NO_VALUE`; a usable candidate at or
above the threshold may produce `BUY`.

## Initial strategy policy

- Stable favors win/place/wide/quinella, few selections, and low uncertainty;
  race cap 2%.
- Balanced considers every supported bet type; race cap 3%.
- Longshot permits higher-payout candidates only with positive conservative EV
  and uses small stakes; race cap 1.5%.

All parameters are versioned. Tune on 2022-2024 and freeze before 2025.

## Allocation order

1. Compute full Kelly from conservative probability and conservative odds.
2. Apply 1/4 Kelly.
3. Reduce for model disagreement and uncertainty.
4. Enforce candidate, strategy, and race caps.
5. Enforce overlap/correlation controls.
6. Enforce unsettled-exposure and daily-loss limits.
7. Round down to JPY 100 units.
8. If the remaining valid amount is below JPY 100, SKIP.

## Capital accounting

- Unsettled tickets are tracked separately from available capital.
- Initial unsettled exposure is capped at 10% of available capital.
- Daily budget means allowable realized loss, not gross turnover.
- Settled returns may fund later races.
- Stop after realized daily loss reaches the configured budget.
- No loss-chasing or automatic cap increase is permitted.
- Increasing a safety cap requires an explicit user setting change and creates
  a new betting-policy version.

## SKIP conditions

At minimum: low conservative EV; large probability/ranking disagreement;
missing required day-of data; stale calculation after scratch/jockey change;
excessive odds movement; unstable single-feature dependence; capital limit;
or inability to size at the JPY 100 minimum.

## Overall recommendation

The overall recommendation is a deterministic, versioned selection from the
three strategy outputs. It may be SKIP even when an individual strategy has a
BUY if portfolio or reliability controls reject the combined exposure.
