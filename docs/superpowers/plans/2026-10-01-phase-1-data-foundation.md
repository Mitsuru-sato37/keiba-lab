# Phase 1 Data Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the Phase 1 append-only, lineage-aware, point-in-time data foundation and prove it with migration and temporal repository tests.

**Architecture:** SQLAlchemy tables define the shared contract; Alembic owns schema creation. Repositories require explicit UTC `as_of_time` values and enforce the same append-only/result-gate rules before database access. SQLite tests provide deterministic coverage while PostgreSQL-compatible trigger branches remain in the migration.

**Tech Stack:** Python 3.12, SQLAlchemy, Alembic, SQLite test database, PostgreSQL 16 development service, pytest, Ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-10-01-phase-1-data-foundation-design.md`, `docs/DATA_SPEC.md`, `docs/ARCHITECTURE.md`, and `AGENTS.md`.

## Global Constraints

- A calculation may read only data effective and received at or before its `as_of_time`.
- Raw observations, snapshots, predictions, and recommendations are append-only.
- Every persisted calculation carries data/snapshot lineage plus feature, model, and logic versions.
- Results and payouts are unavailable until the corresponding recommendation has been persisted.
- Use UTC for stored instants and `Asia/Tokyo` for JRA calendar semantics.
- Do not add external enrichment to BASE-JV.

## Review Focus

- A record received after `as_of_time` must not be returned; temporal negative test in `tests/integration/test_temporal_repository.py`.
- A record effective after `as_of_time` must not be returned; same test module.
- A superseded record must disappear only after `effective_to`; same test module.
- An UPDATE/DELETE of immutable artifacts must fail at repository and database-trigger levels; `tests/integration/test_append_only.py`.
- A result before recommendation persistence must fail; `tests/integration/test_result_gate.py`.

---

### Task 1: Add SQLAlchemy contracts and migration test harness

**Files:** `packages/infrastructure/src/keiba_infrastructure/db.py`, `tests/integration/test_migration_roundtrip.py`

- [ ] Write a failing migration test that upgrades a clean SQLite database and asserts the foundation table names.
- [ ] Run the test and observe failure because the migration/tables are absent.
- [ ] Add declarative metadata, a SQLAlchemy engine/session factory, and migration test configuration without opening a live database at import time.
- [ ] Run the harness test; it should still fail only because the migration is not created.

### Task 2: Create the Phase 1 Alembic migration

**Files:** `alembic/versions/0001_phase1_data_foundation.py`, `alembic/env.py`

- [ ] Extend the migration test to assert required columns and non-null lineage columns.
- [ ] Implement tables, primary/foreign keys, decision check constraint, indexes for temporal eligibility, and dialect-specific append-only triggers.
- [ ] Run the migration roundtrip test; expect all table/column assertions to pass.
- [ ] Run Ruff and mypy on the migration and database module.

### Task 3: Implement temporal observation repository

**Files:** `packages/application/src/keiba_application/errors.py`, `packages/infrastructure/src/keiba_infrastructure/repositories.py`, `tests/integration/test_temporal_repository.py`

- [ ] Write failing tests for received/effective future records, superseded records, and eligible boundary records.
- [ ] Run them and observe missing repository behavior.
- [ ] Implement `TemporalObservationRepository.add()` and `eligible_as_of(as_of_time: UtcInstant)` with explicit timestamp predicates.
- [ ] Run the temporal tests, Ruff, and mypy.

### Task 4: Enforce append-only artifacts and recommendation result gate

**Files:** `packages/infrastructure/src/keiba_infrastructure/repositories.py`, `tests/integration/test_append_only.py`, `tests/integration/test_result_gate.py`

- [ ] Write failing tests for repository update/delete rejection, database-trigger rejection, and result insertion before recommendation persistence.
- [ ] Implement `RecommendationRepository`, `ResultRepository`, and append-only guard behavior with `RecommendationNotPersistedError`.
- [ ] Run the focused tests and the full Python suite.

### Task 5: Update specifications and handoff

**Files:** `docs/DATA_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/LOGIC_CATALOG.md`, `docs/PROGRESS.md`, `README.md`

- [ ] Document the Phase 1 table/lineage/trigger contract and add Logic IDs `DATA-002`, `TRACE-002`, and `LEAK-004` implementation references.
- [ ] Document exact migration/test commands and that PostgreSQL runtime validation remains optional when Docker is unavailable.
- [ ] Run the full Python/Web verification and `git diff --check`.

