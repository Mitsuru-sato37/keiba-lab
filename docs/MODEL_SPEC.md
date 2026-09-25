# Model Specification

Status: Current Source of Truth
Last updated: 2026-09-25

## Objectives

Compare at least three model families:

1. a simple, interpretable baseline;
2. a probability model, initially CatBoost;
3. a race-group ranking model, initially CatBoost ranking with an appropriate
   grouped objective.

LightGBM compatibility is retained as an experiment, not an initial runtime
dependency. Neural networks and a dedicated trifecta model are excluded from
v1.

## Core Feature v1

Begin with roughly 50-100 reproducible features covering:

- race/course, surface, distance, direction, class, and field size;
- gate, horse number, sex, age, carried weight;
- jockey and trainer identity/basic historical aggregates;
- previous 1/3/5 starts: finish, margin, time, final 3F, passing positions;
- normalized prior performance and opponent/race level;
- days since last race and changes in distance, surface, course, class, weight;
- comparable-condition, surface, distance, and course history;
- recent-form, relative final-3F, and relative pace-position trends.

Historical odds and popularity are stored but excluded from the Core Ability
Model. Pedigree, sale price, training, richer jockey/trainer aggregates, and
human-authored pace/style features require individual ablation evidence.

## Prediction contract

For each runner, persist:

- win, top-2, and top-3 probability;
- ranking score;
- uncertainty and disagreement measures;
- model, feature, calibration, and logic versions;
- input snapshot and calculation timestamp.

Post-processing must ensure within tolerance:

- race win probabilities sum to 1;
- for each horse, `win <= top2 <= top3`;
- probabilities remain in `[0, 1]`.

Raw outputs are retained alongside calibrated/constrained outputs. Calibration
is fitted only on periods available before the evaluated period.

## Day-of update layer

Weather, track condition, scratches, jockey changes, body weight, and other
available day-of facts update the ability estimate through a separately
versioned layer. Missing day-of facts are explicit inputs to reliability and
SKIP decisions. Odds remain outside this layer.

## Simulation

Virtual races consume immutable horse predictions and uncertainty parameters.
Initial simulation does not embed complex human pace rules. It produces win,
quinella, exacta, wide, trio, and trifecta combination probabilities.

Simulation uses deterministic seeds for reproducibility. It starts with a
configured batch size and continues in batches until documented convergence
criteria, a maximum sample count, or a time budget is reached. Persist sample
count, seed, convergence diagnostics, and uncertainty intervals.

## Adoption criteria

A feature family, model, calibration, blend, or simulation enhancement is
adopted only when predefined prediction metrics improve stably across future
walk-forward periods without unacceptable betting-risk degradation. Final
2025 test results cannot be used to retune the candidate evaluated on 2025.
