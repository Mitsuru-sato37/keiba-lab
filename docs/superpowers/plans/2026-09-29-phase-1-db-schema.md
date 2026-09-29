# Phase 1 Database Schema and Migration Plan

## Goal

Establish the append-only PostgreSQL schema and temporal repository seam required by the current data specification, with deterministic SQLite-backed contract tests when PostgreSQL is unavailable locally.

## Scope and assumptions

- This slice creates schema/migration foundations; it does not decide bankroll limits, betting thresholds, or live JV-Link credentials.
- SQLAlchemy 2 and Alembic are the application/migration boundary.
- Stored instants are UTC-aware at the Python boundary; PostgreSQL uses `timestamptz`.
- Every persisted analytical artifact carries snapshot, feature, model, calibration, and logic lineage where applicable.
- Historical records are append-only: no update/delete repository methods are exposed.

## Tasks

1. Add failing schema contract tests for required tables, lineage columns, append-only repository behavior, and as-of eligibility boundaries.
2. Add SQLAlchemy metadata and typed table definitions for raw observations, normalized race/runner data, snapshots, predictions, recommendations, versions, and backtest runs.
3. Add Alembic configuration and an initial migration; keep application startup from creating schema implicitly.
4. Implement a temporal repository with explicit `as_of_time`, eligibility predicates, and immutable insert methods.
5. Run focused tests, full verification, and migration SQL inspection. Document PostgreSQL runtime status separately from SQLite contract coverage.

## Acceptance criteria

- Required entity/lifecycle distinctions from `docs/DATA_SPEC.md` remain visible in the schema.
- Eligibility requires received/effective timestamps at or before `as_of_time`, no prior supersession, and promoted batch status.
- Inserted observations and recommendations cannot be overwritten through repository APIs.
- Missing lineage or non-UTC instants fail validation before persistence.
- Alembic migration is deterministic and does not run implicitly during API import.
