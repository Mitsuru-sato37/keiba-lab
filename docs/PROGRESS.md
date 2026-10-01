# Progress

Status: Current handoff
Last updated: 2026-10-01

## Current phase

Phase 0 — Project skeleton.

The product, data, model, betting, backtest, architecture, logic catalog, and roadmap specifications already exist. Implementation has not yet established the application skeleton in this repository.

## Completed

- Product specification defined.
- Architecture specification defined.
- Data, model, betting, and backtest specifications defined.
- Logic catalog defined.
- Multi-phase roadmap defined.
- Codex/Git workflow rules defined in `AGENTS.md`.

## Next implementation target

Implement Phase 0 from `docs/ROADMAP.md` without changing the product semantics:

- locked Python and TypeScript environments;
- repository/application layout;
- typed domain contracts;
- configuration and logging;
- health endpoint(s);
- PostgreSQL development setup;
- deterministic fixture conventions;
- unit-test and quality-command layout suitable for CI.

## Constraints

- Do not require JRA-VAN membership, use key, JV-Link installation, or login for Phase 0.
- Keep the Windows/JV-Link boundary behind a provider interface.
- Preserve all temporal, lineage, leak-prevention, and reproducibility invariants in `AGENTS.md`.
- Never automate ticket purchase.

## Handoff rule

Before stopping work, update this file with what was completed, what remains, the branch name, and any blocked item that requires user input or an external credential.
