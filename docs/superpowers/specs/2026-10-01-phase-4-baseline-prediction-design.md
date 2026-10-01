# Phase 4 baseline prediction design

## Goal

Add the first walk-forward-safe prediction contract on top of the immutable
Phase 3 feature artifacts. The slice must prove that a 2022 test prediction
can be trained only from 2019-2021 data, produces coherent probabilities, and
persists complete model and input lineage.

## Shared understanding

- The first walk-forward test year is 2022.
- A 2022 model trains only on 2019, 2020, and 2021 examples.
- Current-race odds are never an input to ability prediction.
- Predictions are immutable artifacts; a newer model creates a new artifact.
- This phase is a deterministic baseline contract, not the final CatBoost
  implementation and not a betting or ticket-purchase feature.

## Training contract

`TrainingManifest` describes one walk-forward training window and contains the
test year, the exact training years, training example identifiers, feature
version, model version, and logic version. Its validation rules are:

- the first supported test year is 2022;
- the training years for a test year are exactly 2019 through the year before
  the test year;
- no training example may have a year greater than or equal to the test year;
- every training example must use the manifest's feature version.

An invalid manifest raises a dedicated training-leak error. The error is a
run-invalidating condition and is not converted into an empty training set.

## Baseline model

The initial model is `MODEL-BASE-001`, a deterministic, interpretable gate
strength baseline:

1. Training examples contain a race year, race/runner identifiers, Core Feature
   v1 values, and historical win/top-2/top-3 labels.
2. For each gate, calculate a binary Laplace-smoothed win rate
   `(gate_wins + 1) / (gate_starts + 2)` from only the manifest's training
   examples. Missing or unusable gate values use the training-wide smoothed
   prior `(all_wins + 1) / (all_starts + 2)`.
3. At prediction time, use only the feature vector and the trained gate
   statistics. Odds fields or odds records cause an `OddsLeakError`.
4. Normalize the non-negative gate scores within each race into win
   probabilities. When no usable score exists, use the uniform race prior.
5. For a race with `n > 1` runners, derive top-k probabilities as
   `min(1, win + (1 - win) * (k - 1) / (n - 1))`; a one-runner race has 1.0
   for every top-k probability. This distributes the remaining probability
   uniformly across the other runners and guarantees `win <= top2 <= top3`.

The baseline emits raw and constrained probability values (identical for this
slice), a ranking score equal to the gate score, an uncertainty value defined
as `1 / sqrt(gate_starts + 1)` (or 1.0 for an unknown gate), and a zero
disagreement value because no second model is present.
Calibration is not applied in this slice; its version is therefore explicitly
absent rather than fabricated.

## Prediction artifact

Each race-level `PredictionSnapshot` contains:

- an immutable prediction snapshot ID;
- race ID, as-of time, and source data snapshot ID;
- one prediction per runner with win/top-2/top-3 probabilities, ranking score,
  uncertainty, disagreement, and raw probability values;
- feature, model, and logic version IDs;
- the training manifest ID and model manifest checksum.

The prediction repository writes to the existing append-only
`prediction_snapshots` table and flushes without updating existing rows.

## Validation and persistence tests

The phase must include tests for:

- the exact 2019-2021 training window for the 2022 fold;
- rejection of a 2022 training example and non-contiguous training years;
- deterministic training and prediction from the same inputs;
- probability bounds, race-level win normalization, and top-k ordering;
- rejection of odds in the ability prediction path;
- persistence of prediction, feature, data, model, logic, and training lineage;
- append-only behavior when a second model version predicts the same race.

## Specification updates in this phase

- `docs/MODEL_SPEC.md` gains the baseline training and prediction contract.
- `docs/DATA_SPEC.md` gains the Phase 4 prediction persistence contract.
- `docs/LOGIC_CATALOG.md` records the implementation and validation references
  for `MODEL-BASE-001`.
- `docs/PROGRESS.md` moves the current handoff to Phase 4 and records the
  verified acceptance evidence.

## Non-goals

- CatBoost or another external model dependency.
- Probability calibration fitting.
- A grouped ranking model.
- Backtest fold orchestration and result reveal gates.
- Odds, expected value, betting policy, or automatic ticket purchase.
