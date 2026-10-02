# Logic Catalog

Status: Current Source of Truth
Last updated: 2026-10-02

Logic IDs are stable semantic identifiers. Behavior-changing revisions create
a new version under the same ID unless the responsibility itself changes.

| Logic ID | Responsibility | Required evidence |
|---|---|---|
| DATA-001 | Point-in-time observation eligibility | Temporal boundary tests |
| SNAP-001 | Immutable as-of race snapshot construction | Temporal boundary, membership, and checksum tests |
| FEAT-001 | Core Feature v1 values, missingness, and orchestration | Feature lineage and fixture tests |
| MODEL-BASE-001 | Simple baseline prediction | Walk-forward prediction metrics |
| MODEL-WIN-001 | Win/top-2/top-3 probability model | Calibration and constraint tests |
| MODEL-RANK-001 | Race-group ranking model | Group isolation and ranking metrics |
| CAL-001 | Probability calibration/constraint projection | No-future-fit and invariant tests |
| UPDATE-001 | Day-of information update layer | As-of and missing-data tests |
| SIM-001 | Adaptive virtual-race simulation | Seed/replay and convergence tests |
| EV-001 | Conservative odds and EV calculation | Numerical boundary tests |
| BET-001 | Strategy candidate selection | Golden policy fixtures |
| MONEY-001 | 1/4 Kelly and safety-cap allocation | Rounding/cap/property tests |
| RECO-001 | Overall BUY/SKIP recommendation | Reason-code and persistence tests |
| TRACE-001 | Persisted Logic Explorer trace | Stage-link integrity tests |
| LEAK-001 | Post-time feature detection | Must-fail leak fixture |
| LEAK-002 | Test-year training contamination | Must-fail manifest fixture |
| LEAK-003 | Current-race odds in ability inputs | Must-fail schema/input fixture |
| LEAK-004 | Premature result/payout access | Capability/repository denial test |
| VERSION-001 | Required version presence | Must-fail persistence fixture |
| OPS-HEALTH-001 | Local process/readiness health reporting | API health contract tests |
| FIXTURE-001 | Deterministic synthetic observation replay | Seed/version equality tests |
| DATA-002 | Temporal raw observation eligibility query | Temporal repository boundary tests |
| TRACE-002 | Calculation lineage/version persistence contract | Migration column tests |
| DATA-003 | Collector envelope validation and whole-batch import | Contract round-trip and malformed-payload tests |
| FIXTURE-002 | Deterministic observation batch provider | Batch seed/version equality tests |
| DATA-004 | Idempotent observation batch promotion | Duplicate promotion and conflict tests |
| BACKTEST-001 | Walk-forward fold orchestration | Chronological order and expanding-window tests |
| BACKTEST-002 | Immutable backtest run and artifact manifests | Migration and append-only persistence tests |
| BACKTEST-003 | Recommendation-before-result capability gate | Partial-persistence denial test |
| BACKTEST-004 | Deterministic one-day 2022 validation harness | Replay, temporal/leak, BUY/SKIP, and odds-coverage tests |

## Phase 4 implementation references

MODEL-BASE-001 is implemented by
keiba_infrastructure.baseline_prediction.GateStrengthBaseline and
keiba_infrastructure.baseline_prediction.TrainedGateStrengthBaseline.
Validation evidence is in
tests/unit/test_baseline_prediction.py and
tests/integration/test_prediction_persistence.py.

The application contracts are in
keiba_application.predictions.TrainingManifest,
keiba_application.predictions.PredictionSnapshot, and
keiba_infrastructure.predictions.PredictionSnapshotRepository.

## Logic trace contract

Every material stage trace records:

- Logic ID and logic version;
- input artifact IDs and selected input values;
- applied judgment conditions and reason codes;
- output artifact IDs and values;
- next-stage identifiers;
- model and feature versions where applicable;
- calculation timestamp, duration, status, and error details;
- implementation reference and validation evidence reference.

The UI path is: displayed value -> trace -> Logic ID -> this catalog/current
specification -> implementation reference -> validation result.

Implementation references are added when code exists. They must use stable
module/symbol names rather than line numbers. Validation results point to test
IDs and, for experiments, immutable run IDs.

## Phase 6 implementation references

`SIM-001`, `EV-001`, `BET-001`, and `MONEY-001` are exercised by
`keiba_application.golden_race.GoldenRacePipeline` and the deterministic
Golden Race fixture. `TRACE-001` is persisted by
`keiba_infrastructure.repositories.GoldenRacePersistenceRepository` into
`CalculationArtifact` and `LogicTrace` records. Policy replay is implemented
by `keiba_application.golden_replay.PolicyReplay`; prediction and betting
evaluation separation is implemented by
`keiba_application.golden_replay.CoverageAwareEvaluator`.

Validation evidence is in `tests/unit/test_golden_race_contracts.py`,
`tests/unit/test_golden_race_pipeline.py`,
`tests/unit/test_golden_race_replay.py`,
`tests/integration/test_golden_race_persistence.py`,
`tests/integration/test_golden_race_result_gate.py`, and
`tests/integration/test_golden_race_end_to_end.py`.

## Phase 5 implementation references

`BACKTEST-001` is implemented by
`keiba_application.backtest_engine.BacktestOrchestrator` and its injected
ports. `BACKTEST-002` is implemented by
`keiba_infrastructure.schema.BacktestRun`, `BacktestFold`,
`BacktestGuardResult`, `BacktestArtifact`, and
`keiba_infrastructure.repositories.BacktestPersistenceRepository`.
`BACKTEST-003` is implemented by
`keiba_application.backtest_guards.RecommendationPersistenceGate` and
`ResultAccessCapability`.

Validation evidence is in `tests/unit/test_backtest_engine.py`,
`tests/unit/test_backtest_guards.py`, and
`tests/integration/test_backtest_persistence.py`.

## Expansion Slice 1 implementation references

The deterministic one-day validation fixture and input boundary are
implemented by
`keiba_infrastructure.validation_fixture.OneDayValidationInputProvider`.
The replayable runner is implemented by
`keiba_infrastructure.validation_runner.run_one_day_validation`.

Validation evidence is in
`tests/unit/test_2022_validation_fixture.py`,
`tests/integration/test_2022_one_day_validation.py`, and
`tests/unit/test_2022_validation_documentation.py`.
The fixture is synthetic and does not represent BASE-JV historical coverage;
incomplete odds coverage withholds betting metrics.
