# Phase 0 Project Skeleton Design

Status: Approved conversational design; implementation target for Phase 0.

## Goal

Create a deterministic, locally testable application skeleton for the keiba-lab
pipeline without requiring JRA-VAN membership, JV-Link, credentials, or a live
PostgreSQL instance.

## Scope

Phase 0 establishes the boundaries that later phases depend on:

- a Python analytical core and FastAPI application;
- a TypeScript/Vite web shell;
- typed domain contracts for identifiers, versions, instants, and health state;
- configuration and structured logging with safe defaults;
- a provider boundary that can later host JV-Link or deterministic fixtures;
- PostgreSQL and Alembic development entry points without Phase 1 schema design;
- deterministic fixture and test conventions;
- reproducible quality commands for local development and CI.

## Non-goals

Phase 0 does not implement the JRA-VAN adapter, database entities, temporal
repositories, feature generation, prediction, betting, backtesting, or ticket
purchase. It must not introduce external enrichment or expose result/payout
access before recommendation persistence.

## Proposed repository layout

```text
apps/
  api/                 FastAPI composition root and HTTP routes
  web/                 Vite + React TypeScript shell
packages/
  domain/              Stable Python contracts and value objects
  application/         Phase 0 services and ports
  infrastructure/      Configuration, logging, and fixture adapters
tests/
  unit/                Pure domain and application tests
  integration/         API boundary tests
fixtures/
  golden-race/         Small deterministic, versioned fixture set
alembic/               Migration environment, no business schema yet
docker-compose.yml     Optional local PostgreSQL service
pyproject.toml         uv project, pytest, Ruff, and mypy configuration
package.json           workspace commands
pnpm-workspace.yaml    web package workspace declaration
```

The exact package names may be adjusted to fit tooling, but the dependency
direction remains domain -> application -> infrastructure/API. The domain
does not import FastAPI, SQLAlchemy, JV-Link, or environment-specific code.

## Contracts and invariants

- Stored instants are timezone-aware UTC values; JRA calendar semantics remain
  `Asia/Tokyo`.
- IDs and version identifiers are explicit typed values rather than arbitrary
  strings at public boundaries.
- Provider ports return observations plus source metadata; they do not expose
  Windows/JV-Link types to the core.
- Health reports distinguish process readiness from optional dependency status.
- Fixture outputs are stable for a fixed fixture version and seed.
- Phase 0 creates no calculation artifact that could be mistaken for a
  prediction or recommendation.

## API surface

The initial HTTP surface is intentionally small:

- `GET /health/live` returns a process-liveness response.
- `GET /health/ready` returns a readiness response for configured local
  dependencies and never requires JRA-VAN.

The endpoint response is JSON with a stable `status` field and a versioned
application identifier. No prediction or result route exists in Phase 0.

## Configuration and logging

Configuration loads environment variables through a typed settings object,
uses local-safe defaults, and rejects malformed URLs/time zones at startup.
Logs are structured, omit secrets, use UTC timestamps, and include a component
name plus request correlation when an HTTP request exists.

## Verification strategy

Tests cover domain value validation, UTC/Tokyo conversion, deterministic
fixture output, configuration defaults and secret redaction, health responses,
and the absence of a live JRA-VAN dependency. Quality commands run formatting,
linting, type checking, unit tests, and the web build. PostgreSQL is exercised
only through an explicit optional service check; the default test command stays
deterministic and offline.

## Acceptance criteria

1. A clean checkout can install the locked Python and TypeScript dependencies.
2. The default test and quality commands pass without JRA-VAN or PostgreSQL.
3. The API health endpoints respond locally with stable JSON.
4. A deterministic fixture test produces identical output for the same seed.
5. README and `docs/PROGRESS.md` document exact setup, commands, completed
   work, and the next Phase 1 target.

