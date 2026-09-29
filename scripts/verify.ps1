$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot '..\.uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot '..\.uv-python'

function Invoke-Checked([string]$Name, [scriptblock]$Command) {
  Write-Host "== $Name =="
  & $Command
  if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
}

Invoke-Checked 'Ruff format' { uv run ruff format --check src tests }
Invoke-Checked 'Ruff lint' { uv run ruff check src tests }
Invoke-Checked 'mypy' { uv run mypy src/keiba_lab }
Invoke-Checked 'pytest' { uv run pytest --cov=keiba_lab --cov-report=term-missing }
Invoke-Checked 'Web tests' { pnpm --dir apps/web test }
Invoke-Checked 'Web typecheck' { pnpm --dir apps/web typecheck }
Invoke-Checked 'Web lint' { pnpm --dir apps/web lint }
Invoke-Checked 'Web build' { pnpm --dir apps/web build }

uv --version
node --version
pnpm --version
if (Get-Command docker -ErrorAction SilentlyContinue) {
  Invoke-Checked 'Docker Compose validation' { docker compose -f infra/compose.yaml config --quiet }
} else { Write-Warning 'Docker unavailable; compose runtime validation was not run.' }
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue) -or -not (dotnet --list-sdks)) {
  Write-Warning '.NET SDK unavailable; .NET 8 is required for the Phase 2 collector.'
}
