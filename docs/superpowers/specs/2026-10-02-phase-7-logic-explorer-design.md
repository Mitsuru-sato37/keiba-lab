# Phase 7 Logic Explorer Mock Design

**Date:** 2026-10-02
**Status:** Approved design
**Scope:** A deterministic React mock UI for tracing a Golden Race recommendation
from the displayed outcome back to its stored calculation evidence.

## Intent and success criteria

The first web experience should let the user understand why a recommendation
is `BUY` or `SKIP` without requiring an API, JRA-VAN subscription, or expert
knowledge. The screen must make the calculation path visible while preserving
the repository's auditability rules.

Phase 7 succeeds when the mock UI can:

1. show the deterministic Golden Race cases as race cards on a Today view;
2. open a selected race in a Race view with its recommendation, confidence,
   data status, calculation time, and strategy summary;
3. navigate through the stored stage order in a Logic Explorer view;
4. show each stage's inputs, conditions, outputs, versions, and validation
   evidence from typed fixture data;
5. display both `BUY` and `SKIP` as valid outcomes, including the structured
   `SKIP_NO_VALUE` reason;
6. keep prediction evidence separate from odds-dependent market evidence; and
7. pass deterministic component tests, a production build, and type checking.

The mock does not claim live performance and does not purchase tickets.

## Alternatives considered

### Recommended: one-page click-through mock

Use the existing React/Vite shell and a small typed Golden Race fixture in the
web package. React state controls the selected race and selected stage. The
three product views are represented by stable view state rather than adding a
router dependency.

This is recommended because it delivers the Phase 7 acceptance slice with the
fewest moving parts, keeps the UI deterministic, and leaves a clean seam for a
future API client to replace the fixture provider.

### Route-based mock

Add a routing dependency and give Today, Race, and Logic Explorer separate
URLs. This would resemble the eventual product more closely, but adds browser
history and route-state behavior before the API contract exists.

### API-first implementation

Add FastAPI read endpoints and connect the React app to persisted PostgreSQL
artifacts now. This would test a larger deployment path, but Phase 6 has no
stable read API contract yet and the acceptance goal is a UI trace over known
Golden Race artifacts.

## User flow

```text
Today
  -> choose golden-buy or golden-skip
Race summary
  -> open calculation evidence
Logic Explorer
  -> choose a stage
Stage evidence
  -> inspect inputs, conditions, outputs, versions, validation
  -> return to Race or Today
```

The Today view starts with the two deterministic fixture cases. Selecting a
card opens the Race view. The Race view presents the top-level recommendation
and a compact stage timeline. Selecting a timeline item opens the Logic
Explorer detail for that stage. Back controls return to the previous product
view without changing the fixture or inventing a new calculation.

## Data contract

The web package owns a read-only fixture adapter whose types mirror the
persisted Phase 6 evidence, not the database implementation. The adapter must
provide:

- `GoldenRaceCase`: race identity, display metadata, recommendation, reason
  codes, confidence, calculation time, and ordered stage evidence;
- `StageEvidence`: stage ID, display label, input summaries, conditions,
  output summaries, lineage versions, and validation references;
- `StrategySummary`: strategy name, decision, candidate count, stake, and
  market-value explanation;
- `LineageSummary`: data snapshot, feature, model, logic, seed, and code
  versions where applicable.

The fixture adapter is the only source for displayed explanation content. The
components must not derive new reasons from free-form text or infer missing
lineage. Any absent optional field is rendered as `未提供` or an equivalent
explicit missing-data state.

The two required cases are:

- `golden-buy`: `BUY`, with visible positive-value evidence and at least one
  strategy summary;
- `golden-skip`: `SKIP`, with reason code `SKIP_NO_VALUE`, showing that the
  prediction can be reliable while the market has no acceptable value.

Odds-dependent fields are labeled as market evidence and appear only in the
market-evaluation, betting, allocation, and recommendation stages. Ability
prediction stages must not receive or display current-race odds as inputs.

## Component boundaries

Keep the web code in small components with explicit props:

- `AppShell`: owns view and selected-case state and renders navigation;
- `TodayView`: lists the two fixture cases and their top-level outcomes;
- `RaceView`: shows recommendation summary, data status, strategies, and the
  ordered stage timeline;
- `LogicExplorerView`: shows selected stage evidence and lineage;
- `StageTimeline`: renders the fixed Phase 6 stage order and selected state;
- `StatusBadge` and `EvidenceRow`: shared presentational components for
  outcome/status and labeled evidence values;
- `goldenRaceFixture.ts`: typed immutable fixture adapter and display labels.

The initial implementation may keep these files under `apps/web/src/` and use
plain CSS in the existing web entrypoint. No component should call a database,
read environment secrets, or perform a network request.

## Invariants and error behavior

- The stage timeline order is fixed by the Phase 6 Golden Race contract.
- A selected stage must always resolve to evidence belonging to the selected
  race; stale selections fall back to the first available stage.
- Unknown or missing evidence is shown as an explicit unavailable state, not
  replaced with a guessed explanation.
- The result/recommendation gate is represented in the fixture evidence: the
  UI never shows result or payout data before the recommendation stage.
- `BUY` and `SKIP` use the same summary layout so `SKIP` is not treated as an
  error state.
- The UI is informational only; no ticket purchase, account action, or
  external write is exposed.

## Testing and acceptance

Tests must cover:

1. both fixture cases render with the correct recommendation and reason;
2. selecting a race opens the corresponding Race view;
3. selecting a stage shows the matching evidence and lineage versions;
4. ability-stage evidence contains no current-race odds field;
5. pre-recommendation stages do not expose result or payout data;
6. missing evidence renders an explicit unavailable state;
7. stage navigation is deterministic and preserves the selected race; and
8. the web test, typecheck, and production build pass.

The mock is not a performance report. Fixture results must not be described
as actual 2022 race performance.

## Future seam

The fixture adapter should expose the same read shape a future API client can
implement. Replacing the adapter must not require changing the view
components. API pagination, authentication, live polling, and route URLs are
out of scope for Phase 7.
