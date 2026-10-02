# Phase 7 Logic Explorer Mock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic React mock that lets a user move from Golden Race recommendations to stored calculation evidence.

**Architecture:** Keep the existing Vite/React shell and introduce a typed, read-only Golden Race fixture adapter. `AppShell` owns selected race, view, and stage state; focused presentational components render Today, Race, and Logic Explorer views. No API, database, router, or external write is added in this phase.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, plain CSS.

**Spec:** `docs/superpowers/specs/2026-10-02-phase-7-logic-explorer-design.md`

## Global Constraints

- The UI must use deterministic Golden Race fixture data and must not claim actual 2022 performance.
- Ability prediction must never consume or display current-race odds.
- Result and payout evidence must remain unavailable before the recommendation stage.
- `BUY` and `SKIP` are equally valid outcomes; `SKIP_NO_VALUE` is a structured reason, not an error.
- Displayed explanations must come from typed fixture evidence; components must not invent reasons.
- The UI must not purchase tickets or perform external writes.
- The existing web package must continue to pass test, typecheck, and production build commands.

## Review Focus

- A stale stage selection must not show evidence from another race; test the fallback to the first stage.
- Ability-stage inputs must not expose current-race odds; test the rendered DOM and fixture shape.
- Result/payout data must remain hidden until recommendation; test an early stage and the recommendation stage separately.
- Missing optional evidence must be explicit and never rendered as an inferred explanation; test `未提供`.
- The two outcome types must share the same layout while preserving their distinct decision/reason fields; test BUY and SKIP side by side.

---

### Task 1: Add the typed Golden Race fixture adapter

**Files:**
- Create: `apps/web/src/goldenRaceFixture.ts`
- Test: `apps/web/src/goldenRaceFixture.test.ts`

**Interfaces:**
- Produces immutable `GoldenRaceCase`, `StageEvidence`, `StrategySummary`, and `LineageSummary` types.
- Produces `goldenRaceCases`, `GOLDEN_STAGE_ORDER`, `getGoldenRaceCase(caseId)`, and `getStageEvidence(race, stageId)`.

- [ ] **Step 1: Write the failing fixture contract tests**

  Add tests that assert both `golden-buy` and `golden-skip` exist, have the expected decisions, expose `SKIP_NO_VALUE` only for the skip case, preserve the fixed stage order, and return explicit unavailable values for missing optional evidence.

- [ ] **Step 2: Run the fixture tests to verify they fail**

  Run: `pnpm vitest run src/goldenRaceFixture.test.ts`

  Expected: FAIL because the adapter and exported types do not exist.

- [ ] **Step 3: Implement the read-only fixture adapter**

  Define narrow string unions for decisions and stage IDs, create the two deterministic cases from the Phase 6 fixture evidence, keep odds only on market-dependent stages, and return `null`/missing fields without deriving replacement explanations.

- [ ] **Step 4: Run the fixture tests to verify they pass**

  Run: `pnpm vitest run src/goldenRaceFixture.test.ts`

  Expected: PASS.

- [ ] **Step 5: Commit the fixture adapter**

  ```bash
  git add apps/web/src/goldenRaceFixture.ts apps/web/src/goldenRaceFixture.test.ts
  git commit -m "feat: add typed golden race web fixture"
  ```

### Task 2: Build shared evidence and stage navigation components

**Files:**
- Create: `apps/web/src/components/EvidenceRow.tsx`
- Create: `apps/web/src/components/StatusBadge.tsx`
- Create: `apps/web/src/components/StageTimeline.tsx`
- Create: `apps/web/src/components/GoldenRaceComponents.test.tsx`

**Interfaces:**
- `EvidenceRow({label, value}: {label: string; value: string | number | null})` renders a labeled value and `未提供` for null.
- `StatusBadge({decision}: {decision: "BUY" | "SKIP"})` renders the decision as a visible status.
- `StageTimeline({stages, selectedStageId, onSelect})` renders the supplied ordered stages and calls `onSelect(stageId)` exactly for the clicked stage.

- [ ] **Step 1: Write failing component tests**

  Test visible BUY/SKIP badges, the explicit missing-value label, deterministic stage order, selected-stage state, and click callback behavior.

- [ ] **Step 2: Run the component tests to verify they fail**

  Run: `pnpm vitest run src/components/GoldenRaceComponents.test.tsx`

  Expected: FAIL because the components do not exist.

- [ ] **Step 3: Implement the shared components**

  Use semantic headings, buttons, lists, and accessible labels. Keep the components presentational and do not import the fixture adapter into them.

- [ ] **Step 4: Run the component tests to verify they pass**

  Run: `pnpm vitest run src/components/GoldenRaceComponents.test.tsx`

  Expected: PASS.

- [ ] **Step 5: Commit the shared components**

  ```bash
  git add apps/web/src/components
  git commit -m "feat: add logic explorer evidence components"
  ```

### Task 3: Implement Today and Race views with stateful navigation

**Files:**
- Create: `apps/web/src/components/TodayView.tsx`
- Create: `apps/web/src/components/RaceView.tsx`
- Create: `apps/web/src/components/TodayRaceViews.test.tsx`

**Interfaces:**
- `TodayView({cases, onSelectRace})` renders one card per Golden Race case and calls the callback with its ID.
- `RaceView({race, onBack, onExploreStage})` renders recommendation, confidence, data status, calculation time, strategy summaries, and the stage timeline.

- [ ] **Step 1: Write failing view tests**

  Assert both cards render, selecting a card reports the correct case ID, BUY and SKIP summaries use the same structure, SKIP shows `SKIP_NO_VALUE`, and Race view forwards a selected stage.

- [ ] **Step 2: Run the view tests to verify they fail**

  Run: `pnpm vitest run src/components/TodayRaceViews.test.tsx`

  Expected: FAIL because the views do not exist.

- [ ] **Step 3: Implement Today and Race views**

  Render only fields supplied by the typed fixture. Keep market evidence grouped separately from prediction summary and label the result/payout gate when it is unavailable.

- [ ] **Step 4: Run the view tests to verify they pass**

  Run: `pnpm vitest run src/components/TodayRaceViews.test.tsx`

  Expected: PASS.

- [ ] **Step 5: Commit the views**

  ```bash
  git add apps/web/src/components/TodayView.tsx apps/web/src/components/RaceView.tsx apps/web/src/components/TodayRaceViews.test.tsx
  git commit -m "feat: add today and race golden views"
  ```

### Task 4: Implement Logic Explorer detail and wire the application shell

**Files:**
- Create: `apps/web/src/components/LogicExplorerView.tsx`
- Create: `apps/web/src/components/AppShell.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Create: `apps/web/src/components/LogicExplorerView.test.tsx`

**Interfaces:**
- `LogicExplorerView({race, stageId, onBack, onSelectStage})` renders the selected stage's inputs, conditions, outputs, lineage, validation references, and explicit unavailable values.
- `AppShell` owns `view: "today" | "race" | "logic"`, `selectedCaseId`, and `selectedStageId`; it resets a stale stage to the first stage for the selected race.

- [ ] **Step 1: Write failing Logic Explorer and shell tests**

  Test stage evidence and lineage rendering, no odds in ability-stage evidence, no result/payout before recommendation, explicit missing values, Today → Race → Logic navigation, back navigation, and stale-stage fallback.

- [ ] **Step 2: Run the tests to verify they fail**

  Run: `pnpm vitest run src/components/LogicExplorerView.test.tsx src/App.test.tsx`

  Expected: FAIL because the new view and shell behavior do not exist.

- [ ] **Step 3: Implement Logic Explorer and AppShell**

  Keep selection state local, resolve evidence through the fixture adapter, and use the fixed stage order. The shell must never fetch data or create explanations.

- [ ] **Step 4: Update the app entrypoint and existing test**

  Make `App` render `AppShell` and replace the Phase 0 assertion with the Today view acceptance assertions.

- [ ] **Step 5: Run the focused web suite**

  Run: `pnpm test`

  Expected: all web tests pass.

- [ ] **Step 6: Commit the wired application**

  ```bash
  git add apps/web/src/App.tsx apps/web/src/App.test.tsx apps/web/src/components/LogicExplorerView.tsx apps/web/src/components/AppShell.tsx apps/web/src/components/LogicExplorerView.test.tsx
  git commit -m "feat: wire golden race logic explorer"
  ```

### Task 5: Add visual styling and documentation status

**Files:**
- Create or modify: `apps/web/src/styles.css`
- Modify: `apps/web/src/main.tsx`
- Modify: `docs/PROGRESS.md`
- Modify: `docs/ROADMAP.md` only if the Phase 7 acceptance wording needs a precise reference update

**Interfaces:**
- The styling layer consumes semantic component markup only; it does not change fixture or navigation behavior.

- [ ] **Step 1: Write the styling/status acceptance test**

  Add a lightweight assertion that the application exposes the product navigation labels Today, Race, and Logic Explorer, includes the synthetic-fixture notice, and applies the `app-shell`/view class hooks used by the local stylesheet without relying on external assets.

- [ ] **Step 2: Run the test to verify it fails**

  Run: `pnpm vitest run src/App.test.tsx`

  Expected: FAIL until the final labels, notice, and style hooks are wired.

- [ ] **Step 3: Implement responsive local styling and status updates**

  Provide a readable desktop/mobile layout, visible BUY/SKIP contrast, stage navigation, evidence cards, and an explicit synthetic-fixture note. Update progress to mark Phase 6 complete and Phase 7 in progress, keeping the no-ticket-purchase constraint visible.

- [ ] **Step 4: Run the complete verification suite**

  Run from `apps/web`: `pnpm test`, `pnpm typecheck`, and `pnpm build`.

  Expected: all tests pass, TypeScript reports no errors, and Vite produces a production build.

- [ ] **Step 5: Review the final diff and commit**

  ```bash
  git diff --check origin/main...HEAD
  git status --short
  git add apps/web/src docs/PROGRESS.md docs/ROADMAP.md
  git commit -m "feat: present golden race evidence in logic explorer"
  ```

## Final branch verification

- [ ] Run `pnpm test` from `apps/web`.
- [ ] Run `pnpm typecheck` from `apps/web`.
- [ ] Run `pnpm build` from `apps/web`.
- [ ] Review the rendered flow for both `golden-buy` and `golden-skip`.
- [ ] Confirm the ability-stage DOM contains no current-race odds labels or values.
- [ ] Confirm pre-recommendation stages contain no result or payout values.
- [ ] Confirm `git diff --check origin/main...HEAD` and `git status --short` are clean before opening a PR.
