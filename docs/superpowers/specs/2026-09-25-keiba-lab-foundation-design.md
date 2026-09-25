# keiba-lab Foundation Design

Status: Approved conversational design, pending written-spec review
Date: 2026-09-25

## Intent

Build a personal, auditable JRA forecasting and validation application that
separates sporting ability from market value, prevents future-information
leakage by construction, and makes every recommendation reproducible.

The detailed current requirements are split into the Source of Truth documents
in `docs/`. This document records the foundation design that binds them.

## Recommended approach

Use a modular monorepo. Keep the data/model/backtest domain in Python, expose it
through FastAPI, implement the local UI in React/TypeScript, persist operational
artifacts in PostgreSQL, and isolate the Windows COM/JV-Link boundary in a thin
.NET 8 x64 collector. Use deterministic fixture adapters until live JRA-VAN
credentials and local setup are available.

This approach is preferred to an all-Python collector because JV-Link's
documented integration boundary is Microsoft-centric, and preferred to
microservices because a single-user MVP does not justify distributed-system
cost.

## Key design decisions

1. Append-only, point-in-time data and artifact lineage are domain rules, not
   reporting conventions.
2. Backtests inject an as-of clock and a restricted repository capability set.
3. Results become accessible only after recommendation persistence.
4. Ability prediction and odds/EV evaluation have separate inputs, artifacts,
   and versions.
5. Betting policy is replayable against an immutable prediction snapshot.
6. Explanation is a persisted trace of real calculations, not generated prose.
7. The first complete vertical slice is a deterministic Golden Race, then the
   real first eligible 2022 race.
8. Complexity is earned through walk-forward evidence; it is not assumed.

## Component and data flow

Provider records are stored losslessly, normalized into time-aware facts, and
assembled into immutable race snapshots. Feature generation accepts an
explicit as-of time and version. Probability and ranking models produce runner
predictions; calibration enforces coherent probabilities. Simulation derives
combination probabilities. Market evaluation combines those probabilities with
an odds snapshot, after which strategy and money allocation produce a persisted
BUY or SKIP recommendation. Only then may evaluation reveal result and payout.

Every transition writes a trace linking inputs, rules, outputs, next stage,
versions, and validation evidence.

## Error and invalidation model

Import batches are promoted atomically. Pipeline stages have explicit status
and structured failure details. Retries are idempotent. A correction creates a
new observation. Any mandatory leak/version guard failure invalidates the
complete backtest run. Incomplete historical odds coverage limits the claims a
report may make rather than being silently imputed as live data.

## Testing strategy

Development begins with failing contract and invariant tests. Temporal boundary
fixtures cover facts immediately before and after as-of/post time. Each leak
guard has a must-fail fixture. Simulation tests use persisted deterministic
seeds. The Golden Race is an end-to-end acceptance test with result access
denied until the recommendation commit. The walk-forward suite verifies exact
training/test year manifests before evaluating any performance metric.

## Initial delivery boundary

The first implementation plan covers Phases 0-2 at contract/skeleton depth and
the minimum cross-cutting domain/test scaffolding needed by later phases. It
does not require JRA-VAN membership, install live JV-Link, train a real model,
or claim betting performance.

## Source-of-Truth map

- Product behavior: `docs/PRODUCT_SPEC.md`
- Components and technology: `docs/ARCHITECTURE.md`
- Temporal data and schema concepts: `docs/DATA_SPEC.md`
- Features, prediction, calibration, simulation: `docs/MODEL_SPEC.md`
- Walk-forward and guards: `docs/BACKTEST_SPEC.md`
- EV, strategy, and money management: `docs/BETTING_SPEC.md`
- Traceable logic identifiers: `docs/LOGIC_CATALOG.md`
- Delivery sequence: `docs/ROADMAP.md`
- Historical conversation: `docs/history/`
