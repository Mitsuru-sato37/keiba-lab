# keiba-lab

JRA race prediction and recommendation research/development project.

The repository is currently at **Phase 0: Project skeleton**. The specifications are already defined; implementation should proceed from those specifications rather than redesigning the product from scratch.

## Codex entry point

Before implementation, read:

1. `AGENTS.md`
2. `docs/PRODUCT_SPEC.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DATA_SPEC.md`
5. `docs/MODEL_SPEC.md`
6. `docs/BETTING_SPEC.md`
7. `docs/BACKTEST_SPEC.md`
8. `docs/LOGIC_CATALOG.md`
9. `docs/ROADMAP.md`
10. `docs/PROGRESS.md`

The current specification in `docs/` is authoritative. Files under `docs/history/` are design history only.

## Current development phase

Phase 0 establishes the repository skeleton, locked Python/TypeScript environments, typed contracts, configuration/logging, health endpoints, PostgreSQL development setup, fixtures, tests, and CI-ready quality commands.

Do not require JV-Link credentials for Phase 0. Core development must remain runnable against deterministic fixtures.

## Multi-PC development

GitHub is the shared source of truth.

Initial setup:

```powershell
git clone https://github.com/Mitsuru-sato37/keiba-lab.git
cd keiba-lab
```

At the start of each session:

```powershell
git status
git fetch origin
git switch main
git pull --ff-only
```

Create a `codex/<topic>` branch for a coherent phase or vertical slice. Before moving to another PC, commit and push the branch. On the other PC, fetch and switch to the same branch.

Do not use uncommitted local files as the only copy of important work.
