# Progress

Status: Current handoff
Last updated: 2026-10-01

## Current phase

Phase 1 — Database schema and migrations.

Phase 0 implementation is complete. Phase 1 implementation is in progress in
the writable shared checkout, subject to the Git/Docker environment limits.

## Completed

- Product specification defined.
- Architecture specification defined.
- Data, model, betting, and backtest specifications defined.
- Logic catalog defined.
- Multi-phase roadmap defined.
- Codex/Git workflow rules defined in `AGENTS.md`.
- Python/TypeScript project configuration and the React/Vite web shell.
- Domain contracts for versions, UTC instants, health status, and observations.
- Typed local settings, secret-redacting logging, and deterministic fixture provider.
- FastAPI `/health/live` and `/health/ready` endpoints.
- Optional PostgreSQL Docker Compose and empty Alembic migration environment.
- Synthetic `golden-race-v1` fixture metadata and fixture tests.
- Phase 1 SQLAlchemy contracts and Alembic foundation migration.
- Temporal observation eligibility repository with boundary tests.
- Database/repository append-only guards.
- Recommendation-before-result persistence gate.

## Next implementation target

Phase 2 — JRA-VAN adapter interface, beginning with the deterministic fixture
provider and collector import contract. No JRA-VAN credentials are required
for the fixture portion.

## Constraints

- Do not require JRA-VAN membership, use key, JV-Link installation, or login for Phase 0.
- Keep the Windows/JV-Link boundary behind a provider interface.
- Preserve all temporal, lineage, leak-prevention, and reproducibility invariants in `AGENTS.md`.
- Never automate ticket purchase.

## Handoff rule

Before stopping work, update this file with what was completed, what remains, the branch name, and any blocked item that requires user input or an external credential.

## Current handoff details

- Intended branch: `codex/phase-1-data-foundation`.
- Environment limitation: this checkout's `.git` metadata is read-only, so
  branch creation, commit, and push could not be performed by the agent; the
  working tree remains on `main` with uncommitted Phase 0 and Phase 1 changes.
- Environment limitation: Docker CLI is not installed; compose structure is
  covered by offline YAML tests.
- No user input or external credential is currently required.

## Verified commands

- `uv run pytest -q`: 23 passed.
- `uv run ruff format --check .`: passed.
- `uv run ruff check .`: passed.
- `uv run mypy packages apps tests`: passed.
- `pnpm test -- --run`: 1 passed.
- `pnpm build`: passed.
- `docker compose config`: unavailable because Docker is not installed.
- Phase 1 SQLite migration, temporal, append-only, and result-gate tests: passed.
