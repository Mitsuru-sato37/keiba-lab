# Phase 2 JRA-VAN adapter implementation plan

## Tasks

1. Add failing tests for the provider batch contract, deterministic fixture
   batches, collector JSON round-trip, checksum validation, and fail-closed
   malformed input.
2. Extend the application observation contract with provider record type/key
   and an immutable batch/request abstraction.
3. Implement the fixture provider against the batch contract while retaining
   the existing deterministic behavior.
4. Implement the collector JSON envelope parser/serializer with typed errors.
5. Update repository mapping so provider record type/key are not discarded.
6. Update source-of-truth docs and progress ledger.
7. Run focused tests, full Python/TypeScript checks, inspect the diff, commit,
   and push the phase branch.

## Verification

- Provider contract tests pass without JRA-VAN or JV-Link.
- Negative tests prove malformed collector data never becomes a batch.
- Existing temporal, append-only, result-gate, and web checks remain green.
- Ruff, mypy, and formatting remain clean.

