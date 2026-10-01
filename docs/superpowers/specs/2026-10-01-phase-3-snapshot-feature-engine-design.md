# Phase 3 snapshot and feature engine design

## Goal

Create the first point-in-time race snapshot and a small, explicit Core
Feature v1 registry on top of the Phase 2 provider boundary.

## Snapshot contract

- `RaceSnapshotBuilder` accepts an explicit `as_of_time` and a bounded set of
  observations for one race.
- Every accepted observation must have `received_timestamp <= as_of_time` and
  `effective_from <= as_of_time`, and must not be superseded at that time.
- A future observation passed to the builder is a hard `TemporalLeakError`, not
  silently discarded. Callers must query the temporal repository first.
- A snapshot contains one race record, one or more runner records, a stable
  membership list, a content checksum, and source observation IDs.
- Odds records are not part of the ability snapshot and are rejected by the
  builder when supplied to this path.

## Core Feature v1 contract

- Feature version is `core-feature-v1`.
- Features are generated only from the immutable race snapshot.
- v1 includes explicit race/runner fields: distance, field size, turf flag,
  gate, horse number, age, carried weight, and days since last race.
- Missing values are returned as named missing fields; they are not silently
  imputed in this slice.
- Each feature vector retains race/runner IDs, data snapshot lineage,
  feature version, as-of time, source observation IDs, and values.

## Persistence

Data snapshots and feature snapshots are written through append-only
repositories using the existing Phase 1 tables. The snapshot ID and feature
version are required for every persisted feature vector.

## Non-goals

- No model training, calibration, current-race odds, or betting policy.
- No normalization of the complete JRA-VAN schema.
- No automatic ticket purchase.
