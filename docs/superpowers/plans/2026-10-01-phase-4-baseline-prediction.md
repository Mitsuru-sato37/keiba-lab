# Phase 4 Baseline Prediction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implement a deterministic, walk-forward-safe baseline prediction contract that trains the 2022 fold only on 2019-2021 data and persists immutable prediction lineage.

**Architecture:** Add immutable application contracts for training examples, walk-forward manifests, runner predictions, and race-level prediction snapshots. Implement a small gate-strength baseline in the analytical infrastructure layer, keeping odds out of the ability path and storing model-specific training metadata inside the existing prediction artifact JSON. Add a repository adapter over the existing append-only prediction_snapshots table, then update the current specifications and progress handoff.

**Tech Stack:** Python 3.12, dataclasses, SQLAlchemy, Alembic-managed schema, pytest, Ruff, mypy, SQLite integration fixtures.

**Spec:** docs/superpowers/specs/2026-10-01-phase-4-baseline-prediction-design.md

## Global Constraints

- The first walk-forward test year is 2022. Train only on 2019-2021 before generating any 2022 prediction.
- A calculation may read only data effective and received at or before its as_of_time.
- Ability prediction never consumes current-race odds.
- Raw observations, snapshots, predictions, and recommendations are append-only.
- Every persisted calculation carries data/snapshot lineage plus feature, model, and logic versions.
- A failed leak or version guard invalidates the entire backtest run.
- Use UTC for stored instants and Asia/Tokyo for JRA calendar semantics.
- Keep prediction generation separate from later betting-policy replay.
- Do not add external enrichment to the BASE-JV path.
- Never automate ticket purchase.
- Write tests before implementation and include negative leak tests.

## Review Focus

- An empty or incomplete training set must fail closed instead of silently producing a prior; pinned by test_manifest_rejects_missing_training_year in Task 1.
- A race with one runner must still produce valid top-2/top-3 probabilities; pinned by test_one_runner_prediction_is_coherent in Task 2.
- An unseen or missing gate must use the documented training-wide prior and uncertainty; pinned by test_unseen_gate_uses_training_prior in Task 2.
- Mixed race feature metadata must be rejected rather than silently combining snapshots; pinned by test_prediction_rejects_mixed_feature_context in Task 2.
- Repeating an identical prediction must not update an existing row or create a second row with the same immutable ID; pinned by test_prediction_repository_is_append_only in Task 3.

---

### Task 1: Training and prediction application contracts

Files:
- Create: packages/application/src/keiba_application/predictions.py
- Modify: packages/application/src/keiba_application/errors.py
- Test: tests/unit/test_prediction_contracts.py

Interfaces:
- Consumes: FeatureVector from keiba_application.snapshots and UtcInstant from keiba_domain.time_values.
- Produces: TrainingExample, TrainingManifest.create(...), RunnerPrediction, and PredictionSnapshot for Tasks 2 and 3; TrainingLeakError and PredictionInvariantError for Tasks 1 and 2.

- [ ] Step 1: Write the failing contract tests

  Add tests for:

  - TrainingManifest.create accepting a 2022 test year with exactly the 2019, 2020, and 2021 training years and sorting example IDs deterministically.
  - rejecting a 2022 training example, a missing training year, an empty example set, and a feature-version mismatch with TrainingLeakError.
  - generating the same manifest checksum from the same inputs regardless of example input order.
  - constructing a RunnerPrediction only when all probability values are in [0, 1], win <= top2 <= top3, and the race-level win values sum to one when validating a PredictionSnapshot.

- [ ] Step 2: Run the contract tests to verify the expected failure

  Run: ./.venv/Scripts/python.exe -m pytest tests/unit/test_prediction_contracts.py -q --basetemp tmp/pytest-contracts -p no:cacheprovider

  Expected: FAIL because the new module and errors do not yet exist.

- [ ] Step 3: Implement the immutable contracts

  In keiba_application.predictions:

  - Define frozen, slotted dataclasses with explicit types. TrainingExample contains example_id, race_id, runner_id, race_year, feature_version_id, features, and boolean won, top2, and top3 labels.
  - Define TrainingManifest.create(manifest_id, test_year, training_years, examples, feature_version_id, model_version_id, logic_version_id). Require test_year >= 2022, exact contiguous years 2019..test_year-1, at least one example in every training year, no example year at or after test_year, and matching feature versions. Store sorted example IDs and a SHA-256 checksum of the canonical manifest fields.
  - Define RunnerPrediction with raw and constrained win/top-2/top-3 probabilities, ranking score, uncertainty, and disagreement.
  - Define PredictionSnapshot with deterministic ID, race/as-of/data lineage, feature/model/logic versions, training manifest ID, model manifest checksum, optional calibration version, and an ordered tuple of runner predictions. Validate one race context and probability invariants in __post_init__.
  - Add TrainingLeakError and PredictionInvariantError to errors.py.

- [ ] Step 4: Run the contract tests to verify they pass

  Run: ./.venv/Scripts/python.exe -m pytest tests/unit/test_prediction_contracts.py -q --basetemp tmp/pytest-contracts -p no:cacheprovider

  Expected: PASS with all contract tests passing.

- [ ] Step 5: Commit the contract unit

  git add packages/application/src/keiba_application/predictions.py packages/application/src/keiba_application/errors.py tests/unit/test_prediction_contracts.py
  git commit -m "feat: add walk-forward prediction contracts"

### Task 2: Deterministic gate-strength baseline

Files:
- Create: packages/infrastructure/src/keiba_infrastructure/baseline_prediction.py
- Test: tests/unit/test_baseline_prediction.py

Interfaces:
- Consumes: TrainingExample, TrainingManifest, PredictionSnapshot, RunnerPrediction, and TrainingLeakError from Task 1; FeatureVector from Phase 3.
- Produces: GateStrengthBaseline.fit(manifest, examples) -> TrainedGateStrengthBaseline and TrainedGateStrengthBaseline.predict(feature_vectors) -> PredictionSnapshot for Task 3 and future backtest work.

- [ ] Step 1: Write the failing baseline tests

  Add deterministic fixture helpers and tests for:

  - fitting only the manifest example IDs and rejecting an example outside the manifest;
  - the exact binary Laplace rates (wins + 1) / (starts + 2) and the training-wide fallback prior;
  - deterministic prediction IDs and values from identical inputs;
  - win probabilities summing to one, all probabilities staying in [0, 1], and win <= top2 <= top3 for every runner;
  - one-runner top-k probabilities being 1.0;
  - missing or unseen gates using the training-wide prior and 1 / sqrt(gate_starts + 1) uncertainty (1.0 for unknown gates);
  - a feature vector containing an odds key raising OddsLeakError;
  - feature vectors from different races, snapshots, as-of times, or feature versions raising PredictionInvariantError.

- [ ] Step 2: Run the baseline tests to verify the expected failure

  Run: ./.venv/Scripts/python.exe -m pytest tests/unit/test_baseline_prediction.py -q --basetemp tmp/pytest-baseline -p no:cacheprovider

  Expected: FAIL because the baseline module does not yet exist.

- [ ] Step 3: Implement the minimal baseline

  In baseline_prediction.py:

  - Define stable IDs BASELINE_MODEL_VERSION_ID = baseline-gate-v1 and BASELINE_LOGIC_VERSION_ID = MODEL-BASE-001-v1.
  - GateStrengthBaseline.fit verifies the manifest IDs and feature versions, rejects odds-looking feature keys, counts starts/wins per integer runner.gate, computes the exact smoothed gate and overall priors, and returns an immutable trained model with a canonical manifest checksum.
  - TrainedGateStrengthBaseline.predict requires at least one feature vector, verifies one race context, rejects odds keys, uses the gate score or overall prior, sorts runners by ID for stable output, normalizes scores into win probabilities, and applies the spec's top-k formula min(1, win + (1 - win) * (k - 1) / (n - 1)) for n > 1 and 1.0 for n == 1.
  - Set ranking_score to the gate score, uncertainty to 1 / sqrt(gate_starts + 1) (or 1.0 for the overall prior), disagreement to 0.0, and raw values equal to constrained values. Generate the prediction ID from race/as-of/data snapshot/model version/training manifest checksum.

- [ ] Step 4: Run the baseline tests to verify they pass

  Run: ./.venv/Scripts/python.exe -m pytest tests/unit/test_baseline_prediction.py -q --basetemp tmp/pytest-baseline -p no:cacheprovider

  Expected: PASS with all baseline tests passing.

- [ ] Step 5: Run the combined application/model tests

  Run: ./.venv/Scripts/python.exe -m pytest tests/unit/test_prediction_contracts.py tests/unit/test_baseline_prediction.py -q --basetemp tmp/pytest-phase4-unit -p no:cacheprovider

  Expected: PASS with no failures.

- [ ] Step 6: Commit the baseline unit

  git add packages/infrastructure/src/keiba_infrastructure/baseline_prediction.py tests/unit/test_baseline_prediction.py
  git commit -m "feat: add deterministic gate strength baseline"

### Task 3: Immutable prediction persistence

Files:
- Create: packages/infrastructure/src/keiba_infrastructure/predictions.py
- Test: tests/integration/test_prediction_persistence.py

Interfaces:
- Consumes: PredictionSnapshot from Task 1, SQLAlchemy Session, and existing PredictionSnapshot schema from keiba_infrastructure.schema.
- Produces: PredictionSnapshotRepository.add(snapshot), update(...), and delete(...) for Phase 5 backtest and Phase 6 Golden Race work.

- [ ] Step 1: Write the failing persistence tests

  Add an integration fixture that migrates the existing schema, inserts the required data/feature/model/logic version rows, and persists a baseline prediction. Assert that the stored JSON retains runner predictions, raw/constrained values, training manifest ID, and model manifest checksum alongside the relational lineage columns.

  Add tests named test_prediction_repository_is_append_only and test_prediction_repository_keeps_model_versions_separate that:

  - reject repository update/delete with AppendOnlyViolationError;
  - allow the same race to receive a distinct prediction from a different model version and preserve both rows;
  - reject a repeated identical immutable prediction ID through the database/repository rather than updating the first row.

- [ ] Step 2: Run the persistence tests to verify the expected failure

  Run: ./.venv/Scripts/python.exe -m pytest tests/integration/test_prediction_persistence.py -q --basetemp tmp/pytest-prediction-persistence -p no:cacheprovider

  Expected: FAIL because PredictionSnapshotRepository does not yet exist.

- [ ] Step 3: Implement append-only prediction persistence

  Add PredictionSnapshotRepository in the infrastructure layer. Serialize prediction values into canonical JSON under training_manifest_id, model_manifest_checksum, calibration_version_id, and runners. Populate the existing required race/as-of/data/feature/model/logic columns, set created_at in UTC, flush immediately, and expose update/delete methods that always raise AppendOnlyViolationError.

  Do not add a migration: the existing Phase 1/3 table already has the required relational lineage columns, while the baseline-specific manifest metadata belongs in the immutable JSON payload.

- [ ] Step 4: Run the persistence tests to verify they pass

  Run: ./.venv/Scripts/python.exe -m pytest tests/integration/test_prediction_persistence.py -q --basetemp tmp/pytest-prediction-persistence -p no:cacheprovider

  Expected: PASS with all persistence and append-only tests passing.

- [ ] Step 5: Commit the persistence unit

  git add packages/infrastructure/src/keiba_infrastructure/predictions.py tests/integration/test_prediction_persistence.py
  git commit -m "feat: persist immutable prediction snapshots"

### Task 4: Source-of-truth updates and phase handoff

Files:
- Modify: docs/MODEL_SPEC.md
- Modify: docs/DATA_SPEC.md
- Modify: docs/LOGIC_CATALOG.md
- Modify: docs/PROGRESS.md
- Test: tests/unit/test_phase4_documentation.py

Interfaces:
- Consumes: the implementation symbols and test names from Tasks 1-3.
- Produces: current documentation that identifies the Phase 4 baseline contract, its logic/version IDs, and the next Phase 5 target.

- [ ] Step 1: Write the failing documentation contract tests

  Add text-level tests asserting that the source-of-truth files mention:

  - MODEL-BASE-001, baseline-gate-v1, and the 2019-2021-only 2022 training rule;
  - the prediction JSON lineage fields and append-only behavior;
  - stable implementation references and the baseline/persistence validation test paths;
  - Phase 4 completed and Phase 5 as the next target in PROGRESS.md.

- [ ] Step 2: Run the documentation tests to verify the expected failure

  Run: ./.venv/Scripts/python.exe -m pytest tests/unit/test_phase4_documentation.py -q --basetemp tmp/pytest-phase4-docs -p no:cacheprovider

  Expected: FAIL because the current source-of-truth documents still describe Phase 3 as the active handoff.

- [ ] Step 3: Update the source-of-truth documents

  Add the exact baseline training/prediction rules from the Phase 4 design to MODEL_SPEC.md, add the prediction persistence contract to DATA_SPEC.md, add implementation and validation references for MODEL-BASE-001 to LOGIC_CATALOG.md, and update PROGRESS.md to record Phase 4 completion, verified commands, and Phase 5 as the next target. Preserve the project-wide leak and lineage invariants.

- [ ] Step 4: Run the documentation tests to verify they pass

  Run: ./.venv/Scripts/python.exe -m pytest tests/unit/test_phase4_documentation.py -q --basetemp tmp/pytest-phase4-docs -p no:cacheprovider

  Expected: PASS with all documentation assertions passing.

- [ ] Step 5: Commit the source-of-truth update

  git add docs/MODEL_SPEC.md docs/DATA_SPEC.md docs/LOGIC_CATALOG.md docs/PROGRESS.md tests/unit/test_phase4_documentation.py
  git commit -m "docs: record phase 4 baseline prediction handoff"

## Final verification

- [ ] Fetch origin/main and confirm the phase branch still starts from the synchronized merge commit before final verification.
- [ ] Run the full Python suite: ./.venv/Scripts/python.exe -m pytest -q --basetemp tmp/pytest-phase4-full -p no:cacheprovider.
- [ ] Run Ruff: ./.venv/Scripts/python.exe -m ruff check packages apps tests.
- [ ] Run mypy: ./.venv/Scripts/python.exe -m mypy packages apps tests.
- [ ] Run the web checks: pnpm test, pnpm build, and pnpm typecheck.
- [ ] Run git diff --check, inspect git status --short, and review the complete branch diff against origin/main.
- [ ] Push only after all listed checks pass; open the Phase 4 pull request at the acceptance checkpoint.
