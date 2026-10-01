# Logic Catalog

Status: Current Source of Truth
Last updated: 2026-09-25

Logic IDs are stable semantic identifiers. Behavior-changing revisions create
a new version under the same ID unless the responsibility itself changes.

| Logic ID | Responsibility | Required evidence |
|---|---|---|
| DATA-001 | Point-in-time observation eligibility | Temporal boundary tests |
| SNAP-001 | Immutable race snapshot construction | Membership/checksum tests |
| FEAT-001 | Core Feature v1 orchestration | Feature lineage and fixture tests |
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
