# Phase 2 JV-Link Boundary Preparation

## Scope

Define a versioned, idempotent import-batch contract and deterministic promotion tests. This slice does not connect to JV-Link, require credentials, install .NET, or write analytical tables directly.

## Acceptance

- Import batches carry provider, contract version, batch ID, records, checksums, and received time.
- A batch can be promoted once; duplicate promotion is idempotent and changed content under the same ID is rejected.
- Failed batches are never eligible for temporal reads.
- The future Windows x64 .NET 8 collector boundary is documented without live integration.
