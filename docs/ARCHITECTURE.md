# Architecture

Status: Current Source of Truth
Last updated: 2026-09-25

## Architectural choice

Use a modular monorepo with a Python analytical core, FastAPI, React with
TypeScript, PostgreSQL, and a thin Windows x64 .NET collector for JV-Link.
Parquet and DuckDB are permitted as reproducible analytical extracts, never as
an untracked second source of truth.

The .NET collector is a deliberate refinement of the initial technology list.
JV-Link is a Windows COM boundary and its documented development environments
are Microsoft-centric. Isolating it avoids coupling unsupported Python COM
behavior to the analytical pipeline. All downstream behavior remains Python.

## Logical components

```text
JRA-VAN / deterministic fixture
        |
Provider adapter (.NET JV-Link collector or fixture provider)
        |
Raw append-only observations
        |
Normalizer -> Snapshot Manager -> Feature Engine
                                  |
                Prediction + Calibration + Ranking
                                  |
                          Simulation Engine
                                  |
                         Odds / EV Engine
                                  |
                           Betting Engine
                                  |
                          Money Allocation
                                  |
                    Recommendation + Trace Store
                                  |
                    FastAPI -> React Web UI

Result/Payout repository is isolated until recommendation persistence.
Backtest orchestrator drives the same application services with an as-of clock.
```

## Deployment boundary

- `collector`: Windows 11 host process, .NET 8 x64, JV-Link installed locally.
- `api` and `worker`: CPython processes; initially run on the same Windows host.
- `web`: local React application served separately during development and as
  static assets in a packaged deployment.
- `postgres`: local PostgreSQL instance or container. JV-Link itself is not
  placed in a Linux container.

The collector communicates through a stable application-level import contract,
not direct access to analytical tables. Initial operation may invoke a local
CLI/import spool; an HTTP service is unnecessary until scheduling requires it.

## Module boundaries

- Domain contracts contain identifiers, enums, value objects, and invariants.
- Provider ports expose raw observations and source metadata.
- Repositories enforce temporal queries and append-only artifact persistence.
- Pipeline stages accept explicit artifact IDs and an injected as-of clock.
- Training creates immutable model artifacts and training manifests.
- Backtest orchestration controls reveal order; stages cannot access results
  through a shared unrestricted session.
- Explanation reads persisted traces and never recomputes or fabricates them.
- Phase 1 persistence is defined by SQLAlchemy contracts and Alembic
  migrations. Temporal repositories require an explicit as-of instant, while
  append-only and recommendation/result gates are enforced in both code and
  the database.

## Technology decisions

- Python environment/package management: `uv` with a locked project.
- Python quality: `pytest`, type checking, and lint/format checks configured in
  the initial skeleton.
- Database migrations: Alembic; application code never creates production
  schema implicitly.
- Web: React, TypeScript, Vite, and a generated API client once the OpenAPI
  contract stabilizes.
- JavaScript package management: `pnpm` with a lockfile.
- IDs: UUIDv7-compatible values where ordering helps; external JRA keys remain
  explicit natural-key columns.
- Stored instants: timezone-aware UTC; race calendar/date calculations use
  IANA zone `Asia/Tokyo`.

Exact dependency versions are selected and locked during skeleton creation.

## Reliability and error handling

- Collector imports are idempotent by provider record identity and source
  version, but retain changed observations as new records.
- A partially imported batch is not promoted to an eligible snapshot.
- Pipeline stages persist status (`pending`, `running`, `succeeded`, `failed`,
  `invalid`) and structured errors.
- Retries must not create duplicate logical artifacts.
- Manual correction creates a new observation/snapshot; it never edits history.
- Failed leak/version guards mark the complete backtest run `invalid`.

## Security and secrets

- JRA-VAN credentials or use keys never enter Git, fixtures, logs, or database
  exports.
- Secrets are provided through local environment/config facilities excluded
  from version control.
- The initial app binds locally by default and has no external authentication
  surface.

## Rejected initial approaches

- All-Python JV-Link integration: fast to prototype but depends on an
  unsupported/fragile COM path.
- Microservices and message brokers: operational cost without an initial
  single-user scaling need.
- SQLite as the system database: possible for a demo, but PostgreSQL better
  supports concurrent collector/API/worker activity and temporal querying.
