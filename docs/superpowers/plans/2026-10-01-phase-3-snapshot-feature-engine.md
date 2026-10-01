# Phase 3 snapshot and feature engine implementation plan

## Tasks

1. Add failing boundary, negative leak, odds-exclusion, missingness, and
   persistence-lineage tests.
2. Add typed snapshot/feature application contracts and structured errors.
3. Implement the race snapshot builder and Core Feature v1 registry.
4. Implement append-only data-snapshot and feature-snapshot repositories.
5. Add fixture records covering race, runner, future, and odds observations.
6. Update DATA, ARCHITECTURE, LOGIC, and PROGRESS source-of-truth documents.
7. Run SQLite and PostgreSQL migration checks, the full quality suite, inspect
   the diff, commit, and push the phase branch.

## Verification

- Boundary timestamp fixtures include records exactly at and after `as_of`.
- Future received/effective records fail with `TemporalLeakError`.
- Odds supplied to the ability feature path fail with `OddsLeakError`.
- Missing fields are explicit and deterministic.
- Persisted artifacts retain snapshot and feature-version lineage.
