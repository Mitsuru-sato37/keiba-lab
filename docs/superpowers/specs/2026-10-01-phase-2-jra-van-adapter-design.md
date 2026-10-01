# Phase 2 JRA-VAN adapter design

## Goal

Introduce a typed provider boundary that lets the analytical core consume
deterministic observations now and JV-Link collector output later, without
requiring a JRA-VAN subscription in tests or development.

## Contract

- A provider returns an immutable `ObservationBatch` with a batch identity,
  provider metadata, collection time, and zero or more `ObservationRecord`s.
- Each record has an explicit provider record type and natural key in addition
  to its temporal fields and payload.
- The collector import envelope is JSON with an explicit schema version,
  batch ID, provider/version metadata, collection time, and record list.
- The importer validates required fields, UTC timestamps, unique record IDs,
  and payload checksums before producing the application batch.
- Invalid input fails closed with a structured import error and produces no
  partial batch.
- Fixture output is deterministic for a seed and fixture version.

## Non-goals

- No JV-Link COM calls, credentials, login, or Windows-specific code in the
  Python core.
- No database promotion or scheduling in this slice; the existing append-only
  repository remains the persistence boundary.
- No external enrichment.

## Invariants preserved

- All stored/transported instants are UTC.
- Temporal eligibility remains an explicit repository query concern.
- Provider data carries source/version metadata for lineage.
- A malformed or partially valid collector payload is rejected as a whole.

