# Data Specification

Status: Current Source of Truth
Last updated: 2026-09-25

## Data-source policy

JRA-VAN Data Lab / JV-Link is the primary source. The baseline dataset is named
`BASE-JV`. External data, if later approved, is isolated as a versioned
enrichment layer such as `ENRICH-<source>` and evaluated against BASE-JV.
Scraping is not an architectural dependency.

## Temporal fields

Every raw observation and derived snapshot carries enough metadata to answer
what was knowable at a prediction time:

- `source_timestamp`: time asserted by the source;
- `received_timestamp`: time the application obtained the record;
- `effective_from`: earliest time the fact may be used;
- `effective_to`: optional supersession time;
- `snapshot_id`: immutable snapshot identifier;
- `provider`, `provider_record_type`, and provider natural key;
- payload/content checksum and ingestion batch ID.

An artifact is eligible at `as_of_time` only if both `received_timestamp` and
`effective_from` are at or before `as_of_time`, it was not superseded before
that time, and its batch was successfully promoted.

## Storage layers

1. `raw_*`: lossless provider records and receipt metadata.
2. `normalized`: typed race, runner, participant, event, and market facts.
3. `snapshots`: immutable point-in-time views and membership manifests.
4. `features`: immutable feature values plus complete lineage.
5. `predictions`, `simulations`, `bet_candidates`, `recommendations`: immutable
   analytical artifacts.

## Core entities

- `race`, `runner`, `horse`, `horse_history`, `training`
- `race_event` for scratches, jockey changes, weather/track changes, and other
  time-varying facts
- `odds_snapshot` with bet type, combination, observed time, source, and odds
- `feature_snapshot`, `prediction_snapshot`, `simulation_result`
- `bet_candidate`, `recommendation`, `recommendation_item`
- `result`, `payout`
- `model_version`, `feature_version`, `logic_version`
- `backtest_run`, fold, guard result, metric, and artifact manifest
- `logic_trace`, trace input/output, and reason code

Schema implementation may normalize these further but may not collapse their
distinct lifecycle or lineage.

## Feature query contract

Conceptually:

```text
generate_features(race_id, horse_id, as_of_time, feature_version)
```

The query layer requires `as_of_time`; there is no unbounded convenience read
for pipeline code. It returns feature values, source artifact IDs, eligibility
timestamps, and missingness/data-quality flags.

## Results isolation

Results and payouts use a separate repository interface. During a replay its
access capability is withheld until all recommendation artifacts for the race
are durably stored. This is enforced structurally and checked by `LEAK-004`.

## Historical odds limitations

Historical point-in-time odds coverage is recorded per race, bet type, and
decision point. A run with insufficient historical odds may produce prediction
quality metrics but must not claim live-equivalent betting ROI. Coverage and
assumptions are part of every betting evaluation report.

## Golden Race selection

The Golden Race is the chronologically earliest eligible JRA race in 2022
available in the normalized BASE-JV dataset, ordered by post time and then
canonical race ID. A fixture with the same contract is used before live data is
available.

## Phase 1 persistence contract

The first migration creates `raw_observations`, `data_snapshots`,
`feature_snapshots`, `prediction_snapshots`, `recommendations`, `results`, and
the `model_versions`, `feature_versions`, and `logic_versions` registries.
Calculation artifacts carry non-null snapshot/data lineage and the applicable
feature, model, and logic version identifiers. Raw observations, snapshots,
predictions, and recommendations are protected by database append-only
triggers as well as repository guards.

The temporal repository requires an explicit `as_of_time` and applies both
`received_timestamp <= as_of_time` and `effective_from <= as_of_time`, while
excluding records whose `effective_to` is at or before the requested time.
Results reference a persisted recommendation and cannot be inserted through
the repository before that recommendation exists.

## Phase 2 collector import contract

Provider collection is represented as an immutable `ObservationBatch` with a
batch ID, provider/version, UTC collection time, and records. The collector
JSON envelope uses schema version `jra-van-observation-batch/v1`. Every record
includes provider record type/key, temporal timestamps, a JSON payload, and a
SHA-256 checksum of the canonical payload.

The importer validates the schema version, required identifiers, UTC-only
timestamps, unique record IDs, payload shape, and checksums before returning a
batch. Any invalid record rejects the whole envelope; no partial batch is
available to persistence. The deterministic fixture provider implements the
same batch port without JRA-VAN credentials.

Promoted batches are recorded in the immutable `ingestion_batches` table with
provider/version, collection time, record count, and content checksum. A
batch ID may be promoted once; a repeated identical promotion is idempotent,
while reuse with different metadata or content is rejected. Raw records store
the promoted batch ID as their ingestion lineage.

## Phase 3 snapshot and feature contract

`RaceSnapshotBuilder` constructs one immutable race snapshot from exactly one
race observation and one or more runner observations. The snapshot stores its
explicit `as_of_time`, member observation IDs, runner membership, and a
deterministic content checksum. A record received, effective, or superseded
after the requested time is a temporal leak and invalidates construction; it is
not silently excluded.

The Core Feature v1 registry (`core-feature-v1`) emits one feature vector per
runner with `race_id`, `runner_id`, `as_of_time`, data-snapshot ID,
feature-version ID, logic-version ID, source observation IDs, and explicit
missing-field names. Its initial fields are race distance, field size, turf
surface, gate, horse number, age, carried weight, and days since last race.
Ability feature generation rejects odds fields and odds record types. Odds and
market value belong to a later, separate stage.

## Phase 4 baseline prediction contract

The baseline prediction path accepts a validated training manifest and
immutable feature vectors. The 2022 test fold trains only on 2019-2021
examples; a test-year or incomplete training manifest is a run-invalidating
training leak.

Each persisted prediction stores the relational data snapshot, feature,
model, and logic version lineage. Its immutable JSON payload retains
training_manifest_id, model_manifest_checksum, optional
calibration_version_id, and runner-level raw/constrained probabilities,
ranking score, uncertainty, and disagreement. Prediction snapshots are
append-only and a newer model version creates a new artifact rather than
updating an earlier prediction.
