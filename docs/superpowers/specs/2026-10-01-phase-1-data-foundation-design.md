# Phase 1 Data Foundation Design

Status: Implementation target for Phase 1.

## Goal

Provide the first persistent data foundation for point-in-time race analysis:
raw observations, immutable snapshots, version records, calculation lineage,
recommendations, and gated results.

## Scope

- SQLAlchemy table contracts shared by the application and Alembic.
- A clean Alembic migration that creates the Phase 1 foundation schema.
- Temporal observation queries requiring an explicit `as_of_time`.
- Append-only database guards for raw observations, snapshots, predictions,
  and recommendations.
- Required lineage/version columns on calculation artifacts.
- A result repository that refuses access/persistence before a recommendation
  exists for the race.
- SQLite-backed deterministic tests; PostgreSQL remains the development target
  and is checked through dialect-compatible migration branches.

## Non-goals

This phase does not implement JRA-VAN, normalized race/horse business logic,
features, prediction models, betting policy, or the Sites UI. It creates the
storage contracts those phases consume.

## Tables

- `raw_observations`: source/receipt/effective timestamps, provider identity,
  payload checksum, and ingestion batch.
- `data_snapshots`: immutable point-in-time membership manifests.
- `feature_snapshots`: immutable derived feature artifacts with source snapshot
  and feature version.
- `prediction_snapshots`: immutable prediction artifacts with source snapshot,
  feature, model, and logic versions.
- `recommendations`: immutable BUY/SKIP decisions with complete lineage.
- `results`: isolated actual-result records linked to a persisted recommendation.
- `model_versions`, `feature_versions`, `logic_versions`: version registry.

All calculation and recommendation lineage columns are non-null. Timestamps
are stored as timezone-aware values by the application contract and normalized
to UTC before persistence.

## Temporal and append-only rules

An observation is eligible at `as_of_time` only when `received_timestamp` and
`effective_from` are at or before it, and `effective_to` is null or after it.
Repository methods require `as_of_time`; there is no unbounded eligibility
method.

SQLite and PostgreSQL migration branches install database triggers that abort
UPDATE/DELETE on immutable artifact tables. The repository also rejects such
operations before they reach the database, producing the same domain error.

## Result gate

`ResultRepository.add` requires an existing recommendation for the same race.
Missing recommendation raises `RecommendationNotPersistedError`. This is a
storage capability boundary, not a UI convention.

## Verification

Tests run migrations against a clean SQLite database, verify expected tables,
exercise temporal positive/negative boundaries, assert append-only triggers,
check required lineage columns, and prove the result gate. PostgreSQL-specific
syntax is represented in the migration and validated by static migration tests
when a PostgreSQL service is unavailable.

