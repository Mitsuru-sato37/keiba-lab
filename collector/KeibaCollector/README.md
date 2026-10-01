# KeibaCollector

This is the thin Windows x64 `.NET 8` shell at the JV-Link boundary. It reads
and validates the versioned collector envelope on standard input and writes a
validated envelope to standard output. The shell deliberately does not call
JV-Link yet; that adapter remains isolated behind this process boundary.

JRA-VAN credentials and use keys must be supplied only by a future local
configuration mechanism. They must never be committed, logged, or included in
fixtures. This process never automates a betting ticket or purchase.

Build on a Windows machine with the .NET 8 SDK:

```text
dotnet build KeibaCollector.csproj -c Release
dotnet run --project KeibaCollector.csproj -- --self-check
```
