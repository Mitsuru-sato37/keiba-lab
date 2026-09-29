# Phase 1 Win-Only Recommendation Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing Phase 0 skeleton into a deterministic, fixture-backed Phase 1 vertical slice that lists today's races, shows a race detail and prediction evidence, and persists a reproducible BUY/SKIP/WAIT recommendation for win bets without overwriting history.

**Architecture:** Keep the current Python domain/API, React/Vite web shell, PostgreSQL/Alembic direction, and future Windows JV-Link boundary. Add a provider port with a deterministic fixture implementation, append-only artifact repositories, a win-only prediction/market-evaluation service, and a thin FastAPI read/write surface. Current-race odds are input only to market evaluation after prediction; changing odds creates a new odds snapshot and recommendation while retaining the original prediction.

**Tech Stack:** Python 3.12, Pydantic 2, SQLAlchemy 2, Alembic, FastAPI, pytest, React/TypeScript/Vite, Vitest, PostgreSQL-compatible schema, deterministic in-memory fixtures.

**Spec:** `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/DATA_SPEC.md`, `docs/BETTING_SPEC.md`, `docs/LOGIC_CATALOG.md`, and the user-confirmed Phase 1 requirements in this task.

## Global Constraints

- Phase 1 supports win bets only; do not expose or calculate place, wide, quinella, exacta, trio, or trifecta candidates.
- Prediction and Recommendation are separate immutable artifacts. Prediction must not read current-race odds.
- `fair_odds = 1 / win_probability` and `EV = win_probability * current_odds`; use `Decimal` and explicit rounding/precision rules.
- Recommendation decisions are `BUY`, `SKIP`, or `WAIT`. `SKIP` means an evaluated prediction is not actionable; `WAIT` means required odds/data is not yet available or is stale and another update is expected.
- `RecommendationPolicy` is configuration/version data, not hard-coded business logic. At minimum it contains `min_ev`, `max_uncertainty`, and policy version; the fixture default must be deterministic and documented.
- Raw observations, race/odds snapshots, predictions, recommendations, and lineage/version references are append-only. A changed odds value creates a new snapshot and a new recommendation.
- Every persisted calculation carries snapshot, feature, model, calibration where applicable, logic, and policy version references; missing required versions fail validation.
- The fixture provider is the only Phase 1 data source. The provider port must allow a later JV-Link adapter without changing application services.
- Do not implement automatic purchase, payouts/settlement, bankroll accounting, Kelly, advanced backtesting, neural models, or multi-bet-type support in this phase.
- Stored instants are UTC-aware; JRA calendar/date presentation uses `Asia/Tokyo`.
- Do not run schema creation implicitly from API import or app startup. Migrations remain explicit.

## Current Repository Findings

- Base branch is `codex/phase-1-db-schema`; origin is `https://github.com/Mitsuru-sato37/keiba-lab.git`.
- Phase 0 is present: typed domain contracts, settings, health endpoint, React navigation shell, PostgreSQL compose file, fixture metadata, CI, and repository guidance in `AGENTS.md`.
- Current domain models already enforce UTC, immutable Pydantic values, probability bounds, win/top-2/top-3 ordering, canonical combinations, and BUY/SKIP item-state rules.
- Current UI is only a navigation shell in `apps/web/src/App.tsx`; no Today/Race data flow exists.
- Current provider boundary is documentation only in `services/jvlink-collector/README.md`; no Python provider protocol or fixture records exist.
- Current persistence work is uncommitted in `src/keiba_lab/persistence/schema.py` and `temporal.py`. It has placeholder lifecycle tables and a temporal repository, but no Alembic environment/migration, no odds snapshot, no policy/version tables, and its shared SQLAlchemy `Column` declarations currently fail mypy.
- Baseline observed before implementation: `uv run pytest -q` passes 26 tests; `pwsh -File scripts/verify.ps1` stops at mypy with six errors in `src/keiba_lab/persistence/schema.py`.
- Existing specs describe a broader future product. This plan narrows the implementation to the requested win-only vertical slice and updates the affected current specs/logic references where `WAIT` and the Phase 1 scope are currently absent.

## Review Focus

- Odds are missing: the service returns and persists `WAIT`, never fabricates an odds value; test in Task 5.
- Odds change after prediction: the old prediction ID remains unchanged while a new odds snapshot and recommendation are created; test in Task 5.
- EV exactly equals the configured threshold: the documented boundary rule is deterministic; test in Task 4.
- A post-as-of or unpromoted fixture observation is excluded, including exact `effective_from` boundary inclusion; test in Task 2.
- A second write with the same artifact ID is rejected and cannot mutate the first payload; test in Task 3.

## File Map

### Create

- `src/keiba_lab/providers/ports.py` — provider protocol and typed raw race/odds records.
- `src/keiba_lab/providers/fixture.py` — deterministic Phase 1 fixture provider.
- `src/keiba_lab/application/lineage.py` — immutable version/lineage contract.
- `src/keiba_lab/application/policy.py` — configurable `RecommendationPolicy`.
- `src/keiba_lab/application/recommendation.py` — fair-odds, EV, and BUY/SKIP/WAIT evaluation.
- `src/keiba_lab/application/vertical_slice.py` — orchestration from provider snapshots to persisted artifacts.
- `src/keiba_lab/persistence/repositories.py` — append-only artifact repositories and as-of reads.
- `src/keiba_lab/persistence/database.py` — SQLAlchemy engine/session factory boundary without implicit DDL.
- `alembic.ini`, `alembic/env.py`, `alembic/versions/<revision>_phase1_vertical_slice.py` — explicit migration setup.
- `tests/fixtures/phase1.py` — golden race, prediction, and odds-update fixture factories.
- `tests/providers/test_fixture.py` — fixture provider contract tests.
- `tests/application/test_recommendation.py` — policy and numerical decision tests.
- `tests/application/test_vertical_slice.py` — append-only and odds-update orchestration tests.
- `tests/api/test_races.py` — Today/Race API acceptance tests.
- `apps/web/src/api.ts` — typed API client for Today and Race endpoints.
- `apps/web/src/types.ts` — UI response contracts.
- `apps/web/src/components/TodayPage.tsx` — race list.
- `apps/web/src/components/RacePage.tsx` — race detail, prediction evidence, odds input, and recommendation display.
- `apps/web/src/components/LogicEvidence.tsx` — stored input/intermediate/output/version evidence.
- `apps/web/src/components/Phase1App.test.tsx` — UI behavior tests.

### Modify

- `src/keiba_lab/domain/enums.py` — add `WAIT` and win-only Phase 1 reason/status values while retaining future bet-type enums for compatibility.
- `src/keiba_lab/domain/models.py` — add odds snapshot, prediction snapshot, policy, lineage, recommendation evidence, and Phase 1 validation; preserve existing public models unless a compatibility adapter is required.
- `src/keiba_lab/persistence/schema.py` — replace placeholder-only metadata with the Phase 1 lifecycle tables and explicit constraints; keep SQLAlchemy typing mypy-clean.
- `src/keiba_lab/persistence/temporal.py` — retain explicit `as_of_time` eligibility and add batch promotion/status checks needed by the provider repository.
- `src/keiba_lab/persistence/__init__.py` — export the stable persistence boundary, not internal table details.
- `src/keiba_lab/api/main.py` — add dependency-injected Today/Race/odds-update routes without creating tables at import time.
- `apps/web/src/App.tsx` — replace the shell-only navigation with Today -> Race routing/state while retaining Logic Explorer and future-area labels.
- `apps/web/src/App.css` and `apps/web/src/index.css` — style the minimal usable Phase 1 views.
- `docs/PRODUCT_SPEC.md`, `docs/DATA_SPEC.md`, `docs/BETTING_SPEC.md`, `docs/LOGIC_CATALOG.md`, `docs/ROADMAP.md` — record Phase 1 win-only scope, WAIT semantics, formula boundary, and implementation references.
- `README.md` — document fixture startup/verification and the explicit no-live-JV-Link Phase 1 boundary.
- `scripts/verify.ps1` only if needed to add migration/UI acceptance commands; do not weaken existing checks.

## Interfaces

The following names are the contract between tasks. Implementers may choose internal helpers, but later tasks must use these public interfaces.

```python
class RaceProvider(Protocol):
    def list_races(self, *, race_date: date, as_of_time: datetime) -> tuple[RaceRecord, ...]: ...
    def get_race(self, *, race_id: str, as_of_time: datetime) -> RaceRecord: ...
    def get_odds(self, *, race_id: str, as_of_time: datetime) -> OddsSnapshot | None: ...

class RecommendationPolicy(BaseModel):
    policy_id: str
    version: str
    min_ev: Decimal
    max_uncertainty: Decimal

def evaluate_win_recommendation(
    *, prediction: WinPrediction, odds: OddsSnapshot | None, policy: RecommendationPolicy,
    calculated_at: datetime,
) -> Recommendation: ...
```

The recommendation evaluator must be pure: it reads a persisted/immutable prediction and an optional odds snapshot, never a provider or database session. The orchestration layer is responsible for persistence and linking artifact IDs.

## Task 1: Reconcile the Phase 1 contract and baseline

**Files:**
- Modify: `docs/PRODUCT_SPEC.md`, `docs/DATA_SPEC.md`, `docs/BETTING_SPEC.md`, `docs/LOGIC_CATALOG.md`, `docs/ROADMAP.md`
- Modify: `README.md`
- Test: `tests/architecture/test_layout.py` or a new `tests/architecture/test_phase1_docs.py`

- [ ] **Step 1: Add a failing documentation/contract test** asserting that the current docs mention win-only Phase 1, `WAIT`, the exact fair-odds/EV formulas, and the fixture-only boundary.
- [ ] **Step 2: Run the focused test** with `uv run pytest tests/architecture/test_phase1_docs.py -q`; it must fail against the current docs.
- [ ] **Step 3: Update the current specs** without rewriting future-phase requirements. Define `WAIT` as “required odds/data unavailable or stale and another update is expected,” define `SKIP` as evaluated but not actionable, and register `EV-001`, `RECO-001`, and a Phase 1 provider validation reference.
- [ ] **Step 4: Run the focused test** and confirm it passes.
- [ ] **Step 5: Run `git diff --check`** and commit the coherent specification change as `docs: define phase 1 win-only vertical slice`.

## Task 2: Define provider ports and deterministic fixture data

**Files:**
- Create: `src/keiba_lab/providers/ports.py`
- Create: `src/keiba_lab/providers/fixture.py`
- Create: `tests/fixtures/phase1.py`
- Create: `tests/providers/test_fixture.py`
- Modify: `services/jvlink-collector/README.md`

**Interfaces:**
- Produces `RaceRecord`, `RunnerRecord`, `OddsRecord`, and `RaceProvider` with source/provider key, received/effective timestamps, snapshot ID, and payload checksum.

- [ ] **Step 1: Write failing provider tests** for deterministic race listing, race lookup, odds lookup, provider metadata, and exact as-of boundaries. Include one observation that is future-effective and one non-promoted observation that must be invisible.
- [ ] **Step 2: Run `uv run pytest tests/providers/test_fixture.py -q`** and confirm failure because the provider port/factory is absent.
- [ ] **Step 3: Implement typed provider contracts** using frozen Pydantic models and a `Protocol`; require timezone-aware UTC instants and non-empty natural keys.
- [ ] **Step 4: Implement `FixtureProvider`** from `tests/fixtures/phase1.py`. Use a fixed race date, fixed UTC timestamps, stable race IDs/horse IDs, and at least two odds snapshots for the same race. The provider must filter via `as_of_time` and never mutate fixture records.
- [ ] **Step 5: Add a fixture contract test** that the same query twice returns equal values and the provider has no JV-Link/network dependency.
- [ ] **Step 6: Run provider tests and `uv run ruff check src/keiba_lab/providers tests/providers tests/fixtures`**; expected result is PASS.
- [ ] **Step 7: Commit** as `feat: add fixture provider port for phase 1`.

## Task 3: Complete append-only persistence, lineage, and migration foundation

**Files:**
- Modify: `src/keiba_lab/persistence/schema.py`, `src/keiba_lab/persistence/temporal.py`, `src/keiba_lab/persistence/__init__.py`
- Create: `src/keiba_lab/persistence/repositories.py`, `src/keiba_lab/persistence/database.py`
- Create: `alembic.ini`, `alembic/env.py`, `alembic/versions/<revision>_phase1_vertical_slice.py`
- Modify: `tests/persistence/test_schema.py`

**Interfaces:**
- `metadata` contains `raw_observation`, `race`, `runner`, `race_snapshot`, `odds_snapshot`, `prediction_snapshot`, `horse_prediction`, `recommendation`, `logic_version`, `policy_version`, and `backtest_run`.
- `AppendOnlyRepository.append(artifact)` inserts once and rejects duplicate IDs; it exposes no update/delete method.
- `TemporalRepository.eligible(provider_key, as_of_time)` includes records with `received_timestamp <= as_of_time` and `effective_from <= as_of_time`, excludes superseded/unpromoted records, and rejects naive/non-UTC `as_of_time`.

- [ ] **Step 1: Add failing tests** for the complete required table set, lineage columns on prediction/recommendation, duplicate-ID rejection, immutable payload behavior, migration metadata, and boundary/supersession rules.
- [ ] **Step 2: Run `uv run pytest tests/persistence -q`** and record the missing-table/migration failures.
- [ ] **Step 3: Correct the existing SQLAlchemy schema**. Use typed `Column[<type>]` declarations or `Mapped`/`mapped_column` consistently so `uv run mypy src/keiba_lab` passes. Do not keep a generic shared `Column` tuple if it causes the current six mypy errors.
- [ ] **Step 4: Add the Phase 1 tables and constraints**. Keep raw observations lossless; store snapshots and artifacts immutably; separate `prediction_snapshot` from `odds_snapshot` and `recommendation`; represent lineage/version IDs explicitly even when payload JSON is retained.
- [ ] **Step 5: Add explicit Alembic configuration and one deterministic initial migration**. Import metadata only; never call `create_all()` from API/application import. Ensure offline SQL generation is possible.
- [ ] **Step 6: Implement repository insert/read methods** with validation before persistence and no overwrite path. A changed odds snapshot must be a different ID.
- [ ] **Step 7: Run `uv run pytest tests/persistence -q`, `uv run mypy src/keiba_lab`, and `uv run ruff check src/keiba_lab tests/persistence`**; expected result is PASS.
- [ ] **Step 8: Inspect migration SQL** with the repository's chosen Alembic command and verify no implicit migration runs during `from keiba_lab.api.main import app`.
- [ ] **Step 9: Commit** as `feat: add phase 1 append-only persistence boundary`.

## Task 4: Implement win prediction contract, policy, fair odds, and EV

**Files:**
- Modify: `src/keiba_lab/domain/enums.py`, `src/keiba_lab/domain/models.py`
- Create: `src/keiba_lab/application/lineage.py`, `src/keiba_lab/application/policy.py`, `src/keiba_lab/application/recommendation.py`
- Create: `tests/application/test_recommendation.py`

**Interfaces:**
- `WinPrediction` contains race/horse IDs, `win_probability`, `uncertainty`, input race snapshot ID, model/feature/calibration/logic versions, and calculation time.
- `OddsSnapshot` contains race ID, observed/effective time, source, current win odds, snapshot ID, and lineage.
- `Recommendation` supports `BUY`, `SKIP`, and `WAIT`; every outcome carries reason codes and policy/logic/prediction/odds references as applicable.

- [ ] **Step 1: Write failing tests** for `fair_odds = 1 / win_probability`, `EV = win_probability * current_odds`, Decimal arithmetic, zero/negative inputs, exact threshold behavior, `BUY`, `SKIP_NO_VALUE`, `SKIP_UNRELIABLE`, and `WAIT` without odds.
- [ ] **Step 2: Run `uv run pytest tests/application/test_recommendation.py -q`** and confirm failure before implementation.
- [ ] **Step 3: Add `WAIT` to the decision contract** and add explicit Phase 1 reason codes. Keep existing future `BetType` enum values for compatibility, but reject non-`WIN` candidates in the Phase 1 evaluator.
- [ ] **Step 4: Implement `RecommendationPolicy`** as frozen validated configuration. Default fixture policy must be a named/versioned value; the evaluator must receive the policy rather than read environment globals.
- [ ] **Step 5: Implement pure `evaluate_win_recommendation(...)`**. If odds are absent/stale, return WAIT. If uncertainty exceeds policy, return SKIP with unreliable reason. Otherwise compute fair odds and EV; EV at or above `min_ev` returns BUY with one WIN candidate, and below it returns SKIP with no-value reason. Preserve all input/output values and version references in evidence.
- [ ] **Step 6: Run focused tests, then `uv run ruff check` and `uv run mypy src/keiba_lab`**; expected result is PASS.
- [ ] **Step 7: Commit** as `feat: add configurable win recommendation policy`.

## Task 5: Build the fixture-backed vertical-slice orchestration and odds-update behavior

**Files:**
- Create: `src/keiba_lab/application/vertical_slice.py`
- Modify: `src/keiba_lab/persistence/repositories.py`
- Create: `tests/application/test_vertical_slice.py`

**Interfaces:**
- `Phase1Service.list_today(race_date, as_of_time) -> tuple[RaceSummary, ...]`
- `Phase1Service.get_race(race_id, as_of_time) -> RaceDetail`
- `Phase1Service.update_odds(race_id, odds_input, calculated_at) -> Recommendation`
- `Phase1Service` receives provider, repositories, clock, and policy through dependency injection.

- [ ] **Step 1: Write failing tests** for a complete fixture flow: list race -> load detail -> persist race snapshot -> persist prediction -> no-odds WAIT -> submit odds -> persist odds snapshot and BUY/SKIP -> submit changed odds -> new odds snapshot and new recommendation while prediction ID and payload remain unchanged.
- [ ] **Step 2: Add a negative test** that result/payout access is not available in the Phase 1 service and that no automatic purchase method exists.
- [ ] **Step 3: Implement prediction generation as a deterministic fixture adapter**. It may use fixture probabilities, but it must be clearly a prediction artifact with a model version and must not receive odds as an argument.
- [ ] **Step 4: Implement orchestration** in the order race snapshot -> prediction -> optional odds snapshot -> recommendation. Persist every artifact append-only and return stored evidence IDs rather than recomputing explanations.
- [ ] **Step 5: Implement odds updates** as new snapshots and re-run only market evaluation/recommendation when the race snapshot and prediction are unchanged.
- [ ] **Step 6: Run `uv run pytest tests/application/test_vertical_slice.py -q` and the full Python suite**; expected result is PASS.
- [ ] **Step 7: Commit** as `feat: add fixture-backed phase 1 race flow`.

## Task 6: Expose Today/Race API with stored evidence

**Files:**
- Modify: `src/keiba_lab/api/main.py`
- Create: `tests/api/test_races.py`
- Modify: `src/keiba_lab/settings.py` only if dependency wiring needs an explicit fixture mode.

- [ ] **Step 1: Write failing API tests** for `GET /races?date=YYYY-MM-DD`, `GET /races/{race_id}`, and `POST /races/{race_id}/odds`; assert response fields include recommendation state, data status, last calculation time, prediction probability, fair odds/EV when odds exist, reason codes, and evidence/version IDs.
- [ ] **Step 2: Run `uv run pytest tests/api/test_races.py -q`** and confirm routes are absent.
- [ ] **Step 3: Add dependency-injected app construction** so tests use in-memory fixture services and production startup does not create schema or access JV-Link.
- [ ] **Step 4: Implement the three routes** with UTC conversion at the boundary, `Asia/Tokyo` date interpretation, structured validation errors, and no result/payout/purchase endpoints.
- [ ] **Step 5: Run focused API tests and the full Python suite**; expected result is PASS.
- [ ] **Step 6: Commit** as `feat: expose phase 1 race and odds API`.

## Task 7: Implement the minimal Today -> Race UI

**Files:**
- Create: `apps/web/src/api.ts`, `apps/web/src/types.ts`, `apps/web/src/components/TodayPage.tsx`, `apps/web/src/components/RacePage.tsx`, `apps/web/src/components/LogicEvidence.tsx`, `apps/web/src/components/Phase1App.test.tsx`
- Modify: `apps/web/src/App.tsx`, `apps/web/src/App.css`, `apps/web/src/index.css`

- [ ] **Step 1: Write failing Vitest tests** for Today race list navigation, Race detail display, BUY/SKIP/WAIT state, prediction evidence, odds entry, changed-odds refresh, and visible distinction between fair odds and current odds.
- [ ] **Step 2: Run `pnpm --dir apps/web test -- --run`** (or the repository's existing Vitest command) and confirm new tests fail.
- [ ] **Step 3: Add typed API contracts and fetch functions** for the three endpoints; keep API calls isolated from presentation components.
- [ ] **Step 4: Build Today page** showing race time, race name/ID, data status, and current recommendation state; selecting a race opens Race page state without introducing a router dependency unless the existing app already uses one.
- [ ] **Step 5: Build Race page** showing BUY/SKIP/WAIT, win probability, fair odds, current odds, EV, policy threshold, reason codes, lineage/version IDs, and stored evidence. Provide a manual odds input that calls the update endpoint and refreshes the recommendation.
- [ ] **Step 6: Preserve navigation labels** for Logic Explorer, Backtest, Performance, and Settings, but mark them unavailable/future rather than fabricating data.
- [ ] **Step 7: Run Web tests, typecheck, lint, and build**; expected result is PASS.
- [ ] **Step 8: Commit** as `feat: add phase 1 today and race views`.

## Task 8: Finish migration, documentation, and acceptance verification

**Files:**
- Modify: `README.md`, `docs/ROADMAP.md`, `docs/LOGIC_CATALOG.md`, `docs/ARCHITECTURE.md`
- Modify: `scripts/verify.ps1` only for missing required commands.
- Test: existing Python/Web tests plus the new acceptance suites.

- [ ] **Step 1: Add a deterministic end-to-end acceptance test** covering Today -> Race -> prediction evidence -> WAIT without odds -> odds update -> BUY/SKIP -> changed odds -> new recommendation, and assert old rows remain queryable.
- [ ] **Step 2: Add negative acceptance tests** for future observation leakage, current odds passed into prediction, missing lineage/version, duplicate artifact ID, non-WIN candidate, and pre-recommendation result access.
- [ ] **Step 3: Run the narrow checks**: `uv run pytest tests/providers tests/persistence tests/application tests/api -q` and the Web test command.
- [ ] **Step 4: Run repository-wide verification**: `pwsh -File scripts/verify.ps1`; required result is no mypy/ruff/test/typecheck/lint/build failure. Document Docker/.NET/JV-Link as not required for this phase.
- [ ] **Step 5: Review `git diff --check`, migration files, API contracts, and the UI acceptance path**. Confirm no automatic purchase or payout feature was added.
- [ ] **Step 6: Update the roadmap evidence** with exact test commands/results and stable module/symbol references for `DATA-001`, `EV-001`, `RECO-001`, and the fixture provider contract.
- [ ] **Step 7: Commit** as `test: verify phase 1 win-only vertical slice` and open a reviewable PR only after the full verification is green.

## Acceptance Criteria

The implementation is complete only when all of the following are true:

1. From the fixture-backed Today view, a user can open a race detail page and see stored prediction evidence and a BUY/SKIP/WAIT state.
2. Phase 1 calculates only win-bet candidates; `fair_odds` and EV use the exact formulas `1 / win_probability` and `win_probability * current_odds`.
3. Missing/stale odds produce WAIT; evaluated insufficient value produces SKIP; usable value at/above policy threshold produces BUY. Reason codes are structured and persisted.
4. Recommendation policy parameters are injected, versioned, and visible in evidence; changing policy does not mutate old recommendations.
5. Updating odds never mutates the prediction or old odds/recommendation rows. It creates a new odds snapshot and a new recommendation, and tests prove a decision can change as odds cross the threshold.
6. All persisted artifacts retain snapshot/lineage/version references and reject duplicate IDs or incomplete required versions.
7. Fixture observations honor received/effective/as-of boundaries and promoted batch status; no JV-Link, credentials, network, or external scraping is needed.
8. API and UI expose Today -> Race -> prediction evidence -> recommendation -> manual odds update. Future areas remain visibly unimplemented rather than returning invented data.
9. No automatic purchase, payout/settlement, bankroll management, Kelly, advanced backtest, or multi-bet-type implementation is introduced.
10. `uv run pytest -q`, `pwsh -File scripts/verify.ps1`, and the Web test/typecheck/lint/build checks pass; migration SQL is inspectable and schema creation is never implicit on import.

## Handoff Notes

Implementers must account for the existing Phase 1 persistence foundation in `src/keiba_lab/persistence/`, `tests/persistence/`, `pyproject.toml`, and `uv.lock`. Preserve useful work, but do not treat the current schema as complete: it lacks the Phase 1 odds/policy/version boundaries. Do not reset or discard those files without inspecting their diff first.

## Execution status (2026-09-30)

- Tasks 1–7 implemented on `codex/phase-1-db-schema`.
- Task 8 acceptance verification passed: `uv run pytest -q` (39 passed), `pwsh -File scripts/verify.ps1`, Web test/typecheck/lint/build, Alembic offline SQL generation, and `git diff --check`.
- PostgreSQL runtime migration round-trip remains pending because Docker is unavailable; no JV-Link contract, credentials, or external login was required.
