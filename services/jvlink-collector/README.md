# JV-Link Collector Boundary

Phase 0 does not require JV-Link, JRA-VAN credentials, a .NET SDK, or a Data Lab subscription.

Phase 2 will provide a Windows x64 .NET 8 adapter behind this boundary. It will emit versioned BASE-JV import batches and will not write analytical tables directly. The Python core remains runnable against deterministic fixtures.

## Import contract

The collector hands the application an immutable `ImportBatch` containing a
provider name, contract version, batch ID, UTC receipt time, provider natural
keys, payload checksums, and records. Batches are staged, then explicitly
promoted. Promotion is idempotent; changed content under an existing batch ID
is rejected, and failed batches are never eligible for temporal reads.

The current reference implementation is
`keiba_lab.providers.import_contract.ImportBatchStore`. It is a Python
contract test seam, not a JV-Link connection. The future .NET 8 x64 process
must implement this application-level contract without writing analytical
tables directly.
