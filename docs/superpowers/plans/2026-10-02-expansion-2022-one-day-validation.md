# 2022 One-Day Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add a deterministic one-day 2022 validation slice that runs through the existing walk-forward orchestrator and proves the temporal, lineage, recommendation-gate, and odds-coverage contracts without claiming real historical performance.

**Architecture:** Keep the existing BacktestOrchestrator as the only owner of run ordering and leak/result gates. Add a versioned fixture loader and BacktestInputProvider adapter at the infrastructure boundary, then exercise the real baseline predictor through an integration-style scenario with test-only service doubles for persistence, recommendations, results, and metrics.

**Tech Stack:** Python 3.12, dataclasses, JSON fixtures, pytest, Ruff, mypy, existing application ports and infrastructure baseline predictor.

**Spec:** docs/superpowers/specs/2026-10-02-expansion-2022-one-day-validation-design.md

## Global Constraints

- The first walk-forward test year is 2022; training contains only 2019-2021 examples.
- A calculation may read only data effective and received at or before its as_of_time.
- Ability prediction never consumes current-race odds.
- Results and payouts are unavailable until the corresponding recommendation has been persisted.
- Raw observations, snapshots, predictions, and recommendations are append-only.
- Every persisted calculation carries data/snapshot lineage plus feature, model, and logic versions.
- A failed leak or version guard invalidates the entire backtest run.
- BUY and SKIP are equally valid recommendation outcomes.
- Use UTC for stored instants and Asia/Tokyo for calendar semantics.
- Do not add external enrichment or automate ticket purchase.
- Do not describe deterministic fixture metrics as actual 2022 performance or official ROI.

## Review Focus

- A fixture race with records received after its as_of_time must invalidate the run instead of being silently filtered; covered in Task 3 temporal negative test.
- A fixture feature containing current-race odds must invalidate before prediction; covered in Task 3 odds negative test.
- A recommendation that is returned but not persisted must not unlock results; covered in Task 3 persistence-gate test.
- A race with incomplete odds coverage must retain prediction metrics while withholding betting metrics; covered in Task 3 coverage test.
- Reordering fixture races or repeating the same seed must not change the ordered report; covered in Tasks 1 and 3 determinism tests.

---

### Task 1: Define and load the immutable one-day fixture

**Files:**
- Create: fixtures/validation/2022-one-day/fixture.json
- Create: packages/infrastructure/src/keiba_infrastructure/validation_fixture.py
- Test: tests/unit/test_2022_validation_fixture.py

**Interfaces:**
- Consumes: TrainingExample, BacktestRace, ObservationRecord, and FeatureVector contracts.
- Produces: OneDayValidationFixture, ExpectedRecommendation, and load_one_day_validation_fixture(path: Path) -> OneDayValidationFixture.

- [ ] Step 1: Write the failing tests.

Load the fixture and assert literal values: fixture_version is 2022-one-day-v1, seed is 20220105, target date is 2022-01-05, training years are exactly 2019/2020/2021, race IDs are validation-2022-0105-r01 and validation-2022-0105-r02, and expected decisions contain both BUY and SKIP. Assert that feature values contain runner.gate but no odds, and that all source timestamps are no later than each race as_of_time. Assert that two loads have the same checksum.

- [ ] Step 2: Run the focused tests to verify they fail.

Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_2022_validation_fixture.py -q

Expected: FAIL because the fixture file, loader, and public types do not yet exist.

- [ ] Step 3: Implement the fixture contract and loader.

Create frozen dataclasses for fixture metadata and expected recommendation. Parse JSON with explicit validation for version, seed, target date, UTC timestamps, non-empty IDs, and the exact 2019-2021 training window. Construct TrainingExample rows, BacktestRace values, runner FeatureVectors, and temporal ObservationRecords without copying odds into ability feature values. Compute the checksum from canonical JSON bytes and retain it on the returned fixture.

The JSON must contain two chronological 2022 races, one expected BUY and one expected SKIP, complete outcome/payout payloads, and at least one race with incomplete odds coverage.

- [ ] Step 4: Run the focused tests to verify they pass.

Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_2022_validation_fixture.py -q

Expected: all fixture contract tests pass.

- [ ] Step 5: Commit.

    git add fixtures/validation/2022-one-day/fixture.json packages/infrastructure/src/keiba_infrastructure/validation_fixture.py tests/unit/test_2022_validation_fixture.py
    git commit -m "feat: add 2022 one-day validation fixture contract"

### Task 2: Expose the fixture through the backtest input boundary

**Files:**
- Modify: packages/infrastructure/src/keiba_infrastructure/validation_fixture.py
- Test: tests/unit/test_2022_validation_fixture.py

**Interfaces:**
- Consumes: OneDayValidationFixture from Task 1.
- Produces: OneDayValidationInputProvider implementing BacktestInputProvider with training_examples(years) and races(test_year).

- [ ] Step 1: Write the failing tests.

Assert that the provider returns only requested training years, exposes the 2022 races in chronological order, rejects unsupported test years, and does not mutate the loaded fixture when callers reorder returned tuples.

- [ ] Step 2: Run the focused tests to verify they fail.

Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_2022_validation_fixture.py -q

Expected: FAIL because OneDayValidationInputProvider does not yet exist.

- [ ] Step 3: Implement the provider.

Return immutable tuples. Filter training examples by the requested year tuple while preserving deterministic example order, return only the fixture races for test_year 2022, and raise a clear ValueError for any other year. Keep the provider independent of JRA-VAN and behind the existing application protocol.

- [ ] Step 4: Run the focused and related tests.

Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_2022_validation_fixture.py tests/unit/test_backtest_contracts.py -q

Expected: all tests pass.

- [ ] Step 5: Commit.

    git add packages/infrastructure/src/keiba_infrastructure/validation_fixture.py tests/unit/test_2022_validation_fixture.py
    git commit -m "feat: expose one-day validation through backtest input port"

### Task 3: Exercise the full one-day walk-forward validation

**Files:**
- Create: tests/integration/test_2022_one_day_validation.py
- Modify: tests/integration/conftest.py only if a shared fixture path helper is needed

**Interfaces:**
- Consumes: OneDayValidationInputProvider, BacktestOrchestrator, GateStrengthBaseline, and the Task 1 expected recommendation map.
- Produces: an executable validation scenario whose BacktestRunResult is the evidence artifact for the one-day slice.

- [ ] Step 1: Write the failing tests.

Build test-only adapters for the existing service protocols. The trainer must call the real GateStrengthBaseline.fit and adapt its predict(feature_vectors) method to the orchestrator's predict(race) contract. The recommendation adapter must return the fixture's expected BUY/SKIP decision by prediction.race_id. The test-only store and result reader must record event order and enforce ResultAccessCapability; the metrics adapter must return prediction metrics always and betting metrics only when every race has complete odds coverage.

Assert that a run with test_years=(2022,) succeeds, has fold-2022, requests training years exactly (2019, 2020, 2021), represents both BUY and SKIP, persists each recommendation before its result, reports two prediction results, and withholds betting metrics because one race has incomplete odds.

Add negative tests for a future received timestamp and current-race odds in a feature vector, asserting INVALID and no prediction/result event. Add a replay test that runs the same fixture twice and compares ordered race IDs, artifact IDs, guard IDs, prediction metrics, and fixture checksum.

- [ ] Step 2: Run the focused tests to verify they fail.

Run: .\.venv\Scripts\python.exe -m pytest tests/integration/test_2022_one_day_validation.py -q

Expected: FAIL because the one-day scenario and its fixture-backed adapters do not yet exist.

- [ ] Step 3: Implement the test-only scenario adapters.

Keep persistence, result, and metrics doubles in the test file or a test support module. Do not add test-only cleanup or state methods to production classes. Reuse the production baseline predictor and application orchestrator; do not duplicate orchestration or gate logic in the test.

- [ ] Step 4: Run focused and repository-wide verification.

Run:

    .\.venv\Scripts\python.exe -m pytest tests/integration/test_2022_one_day_validation.py -q
    .\.venv\Scripts\python.exe -m pytest
    .\.venv\Scripts\python.exe -m ruff check .
    .\.venv\Scripts\python.exe -m mypy packages

Expected: focused tests pass, then the full suite, Ruff, and mypy pass without warnings or failures.

- [ ] Step 5: Commit.

    git add tests/integration/test_2022_one_day_validation.py
    git commit -m "test: verify 2022 one-day walk-forward validation"

### Task 4: Record the expansion slice in source-of-truth documents

**Files:**
- Modify: docs/ROADMAP.md
- Modify: docs/PROGRESS.md
- Modify: docs/LOGIC_CATALOG.md
- Test: tests/unit/test_2022_validation_documentation.py

**Interfaces:**
- Consumes: accepted fixture and integration-test symbols from Tasks 1-3.
- Produces: current documentation identifying the one-day validation slice, its deterministic-only limitation, and its validation evidence.

- [ ] Step 1: Write the failing documentation contract tests.

Assert that the roadmap includes the one-day expansion exit criteria, progress identifies the current branch/slice and explicitly says no real-world 2022 performance is claimed, and the Logic Catalog contains stable BACKTEST-004 evidence referencing the fixture provider and integration test.

- [ ] Step 2: Run the documentation tests to verify they fail.

Run: .\.venv\Scripts\python.exe -m pytest tests/unit/test_2022_validation_documentation.py -q

Expected: FAIL because the new documentation references do not yet exist.

- [ ] Step 3: Update the three source-of-truth documents.

Add the first Expansion slice to the roadmap, mark deterministic one-day validation as the current handoff in progress, and add BACKTEST-004 with stable module and test references. Keep wording explicit that the fixture is not BASE-JV and incomplete odds coverage prevents official betting metrics.

- [ ] Step 4: Run documentation and full verification.

Run the documentation tests, then rerun the full Python suite, Ruff, and mypy after the documentation change.

- [ ] Step 5: Commit.

    git add docs/ROADMAP.md docs/PROGRESS.md docs/LOGIC_CATALOG.md tests/unit/test_2022_validation_documentation.py
    git commit -m "docs: record 2022 one-day validation slice"

## Final review checklist

- [ ] git diff --check origin/main...HEAD is clean.
- [ ] The fixture remains deterministic across repeated loads and runs.
- [ ] No ability-stage input contains current-race odds.
- [ ] No result/payout is visible before recommendation persistence.
- [ ] BUY and SKIP are both exercised.
- [ ] Incomplete odds coverage is reported separately from prediction metrics.
- [ ] The full Python suite, Ruff, and mypy are green.
- [ ] No actual 2022 performance or ROI claim is made.
