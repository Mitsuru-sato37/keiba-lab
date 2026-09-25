# keiba-lab implementation guide

## Source of Truth

- Current requirements live in `docs/*_SPEC.md`, `docs/ARCHITECTURE.md`,
  `docs/LOGIC_CATALOG.md`, and `docs/ROADMAP.md`.
- `docs/history/` records design history. It explains decisions but never
  overrides a current specification.
- Any behavioral change must update the relevant specification in the same
  change as the code.

## Non-negotiable invariants

1. The first walk-forward test year is 2022. Train only on 2019-2021 before
   generating any 2022 prediction.
2. A calculation may read only data effective and received at or before its
   `as_of_time`.
3. Ability prediction never consumes current-race odds.
4. Results and payouts are unavailable until the corresponding recommendation
   has been persisted.
5. Raw observations, snapshots, predictions, and recommendations are
   append-only. Never overwrite a historical prediction with a newer model.
6. Every persisted calculation carries data/snapshot lineage plus feature,
   model, and logic versions.
7. A failed leak or version guard invalidates the entire backtest run.
8. BUY and SKIP are equally valid recommendation outcomes. Distinguish a
   market-value SKIP from an unreliable-prediction state.

## Engineering rules

- Keep the Windows/JV-Link boundary behind a provider interface. Core domain,
  model, and backtest code must run against deterministic fixtures without a
  JRA-VAN subscription.
- Prefer small modules with explicit typed contracts and dependency injection.
- Use UTC for stored instants and `Asia/Tokyo` for JRA calendar semantics.
- Keep prediction generation separate from betting-policy replay so betting
  variants can be evaluated without retraining.
- Add or update Logic IDs and validation references for material behavior.
- Do not add external enrichment to the BASE-JV path. Enrichment must remain an
  optional, versioned layer with a reproducible BASE-JV comparison.
- Never automate ticket purchase.

## Required verification

- Write tests before implementation for features and bug fixes.
- Include temporal-boundary and negative leak tests for data-access changes.
- Use deterministic seeds for simulations in tests and persist production
  seeds with results.
- Run the narrowest relevant tests first, then the repository-wide suite.
- Do not claim backtest performance when historical odds coverage is
  insufficient; report prediction metrics and odds-coverage limitations
  separately.
