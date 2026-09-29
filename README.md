# keiba-lab

個人用 JRA 競馬予想・検証アプリの基盤です。Phase 0 は Python ドメイン/API、React シェル、PostgreSQL 開発サービス、JV-Link 境界を整備します。

## Setup

Windows 11 では Python 3.12、uv、Node.js 24、pnpm 11、PowerShell 7.3+ を用意してください。

```powershell
uv python install 3.12
uv sync --all-groups
pnpm --dir apps/web install
```

PostgreSQL は任意で `docker compose -f infra/compose.yaml up -d` から起動できます。API は `uv run uvicorn keiba_lab.api.main:app --reload`、Web は `pnpm --dir apps/web dev` です。

## Verification

```powershell
pwsh -File scripts/verify.ps1
```

Docker はこの開発環境では未検出、.NET ホストは存在するが SDK 未導入（2026-09-25 確認）でした。どちらも Phase 0 の必須検証ではありません。Phase 2 では .NET 8 SDK が必要です。

## Repository map

- `src/keiba_lab`: domain contracts, settings, API
- `apps/web`: React/TypeScript shell
- `infra`: local services
- `services/jvlink-collector`: future Windows JV-Link adapter boundary
- `docs`: current specifications and roadmap
