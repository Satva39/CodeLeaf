[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path $ProjectRoot).Path
$BackendRoot = Join-Path $ProjectRoot 'backend'
$MainPath = Join-Path $BackendRoot 'app\main.py'
$ConfigPath = Join-Path $BackendRoot 'app\config.py'
$EnvExamplePath = Join-Path $BackendRoot '.env.example'
$LocalEnvPath = Join-Path $BackendRoot '.env'
$DiagnosticRoutePath = Join-Path $BackendRoot 'app\diagnostic_routes.py'
$DiagnosticTestPath = Join-Path $BackendRoot 'scripts\test_catalyst_diagnostic.py'
$RunnerSource = Join-Path $PSScriptRoot 'backend\scripts\run_catalyst_archive_migration.py'
$RunnerTarget = Join-Path $BackendRoot 'scripts\run_catalyst_archive_migration.py'
$RequiredSupportFiles = @(
    'scripts\audit_neon_storage.py',
    'scripts\migrate_portfolio_archives_to_stratus.py',
    'scripts\test_catalyst_stratus_adapter.py',
    'scripts\test_migration_repeatability.py',
    'scripts\test_portfolio_zip_upload.py'
)

foreach ($required in @($MainPath, $ConfigPath, $EnvExamplePath, $RunnerSource)) {
    if (-not (Test-Path $required -PathType Leaf)) {
        throw "Required file not found: $required. No cleanup was applied."
    }
}
foreach ($relative in $RequiredSupportFiles) {
    $required = Join-Path $BackendRoot $relative
    if (-not (Test-Path $required -PathType Leaf)) {
        throw "Required migration support file not found: $required. No cleanup was applied."
    }
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupRoot = Join-Path $env:TEMP "CodeLeaf-Catalyst-OneGo-Backup-$timestamp"
New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

function Save-Backup([string]$Path) {
    if (Test-Path $Path -PathType Leaf) {
        $relative = $Path.Substring($ProjectRoot.Length).TrimStart('\')
        $destination = Join-Path $backupRoot $relative
        $parent = Split-Path $destination -Parent
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
        Copy-Item -LiteralPath $Path -Destination $destination -Force
    }
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

# Back up all source files that this installer may edit or delete.
foreach ($path in @($MainPath, $ConfigPath, $EnvExamplePath, $DiagnosticRoutePath, $DiagnosticTestPath, $RunnerTarget)) {
    Save-Backup $path
}

# Remove exactly the temporary router import and registration; preserve all other routes.
$main = [System.IO.File]::ReadAllText($MainPath)
$importLine = '(?m)^\s*from \.diagnostic_routes import router as diagnostic_router\s*\r?\n'
$registerLine = '(?m)^\s*app\.include_router\(diagnostic_router\)\s*\r?\n'
$main = [regex]::Replace($main, $importLine, '')
$main = [regex]::Replace($main, $registerLine, '')
Write-Utf8NoBom $MainPath $main

# Remove only the temporary Settings field; leave other secrets/configuration intact.
$config = [System.IO.File]::ReadAllText($ConfigPath)
$config = [regex]::Replace($config, '(?m)^\s*catalyst_diagnostic_token\s*:\s*[^\r\n]*\r?\n', '')
Write-Utf8NoBom $ConfigPath $config

# Remove the obsolete placeholder and local token line, if present. Backups were made above.
$envExample = [System.IO.File]::ReadAllText($EnvExamplePath)
$envExample = [regex]::Replace($envExample, '(?m)^\s*CATALYST_DIAGNOSTIC_TOKEN=.*(?:\r?\n|$)', '')
Write-Utf8NoBom $EnvExamplePath $envExample
if (Test-Path $LocalEnvPath -PathType Leaf) {
    $localEnv = [System.IO.File]::ReadAllText($LocalEnvPath)
    $localEnv = [regex]::Replace($localEnv, '(?m)^\s*CATALYST_DIAGNOSTIC_TOKEN=.*(?:\r?\n|$)', '')
    Write-Utf8NoBom $LocalEnvPath $localEnv
}

# Delete the temporary route and its route-only tests.
foreach ($path in @($DiagnosticRoutePath, $DiagnosticTestPath)) {
    if (Test-Path $path -PathType Leaf) {
        Remove-Item -LiteralPath $path -Force
    }
}

# Install the one-run copy + verification orchestrator.
if ([System.IO.Path]::GetFullPath($RunnerSource) -ne [System.IO.Path]::GetFullPath($RunnerTarget)) {
    Copy-Item -LiteralPath $RunnerSource -Destination $RunnerTarget -Force
}
else {
    Write-Host "Migration runner already exists in the target folder. Skipping copy." -ForegroundColor Gray
}

# Verify no temporary endpoint/token references remain in backend source/docs.
$patterns = @('diagnostic_routes', 'CATALYST_DIAGNOSTIC_TOKEN', 'catalyst_diagnostic_token', 'X-Catalyst-Diagnostic-Token', '/api/diagnostics/catalyst-stratus')
$remaining = Get-ChildItem -Path $BackendRoot -Recurse -File | Where-Object {
    $_.FullName -notmatch '[\\/](__pycache__|\.venv|venv|node_modules)[\\/]'
} | Select-String -SimpleMatch -Pattern $patterns -ErrorAction SilentlyContinue
if ($remaining) {
    $remaining | ForEach-Object { Write-Host ("REMAINING: " + $_.Path + ":" + $_.LineNumber + ": " + $_.Line.Trim()) -ForegroundColor Yellow }
    throw "Temporary diagnostic references remain. Review them before deployment. Backups are in: $backupRoot"
}

Push-Location $BackendRoot
try {
    Write-Host "Running Python syntax checks..." -ForegroundColor Cyan
    & python -m py_compile app\main.py app\config.py app\storage\catalyst_stratus.py app\storage\catalyst_smoke_test.py scripts\run_catalyst_archive_migration.py
    if ($LASTEXITCODE -ne 0) { throw "Python syntax check failed. Backup: $backupRoot" }

    foreach ($test in @('scripts\test_catalyst_stratus_adapter.py', 'scripts\test_migration_repeatability.py', 'scripts\test_portfolio_zip_upload.py')) {
        Write-Host "Running $test ..." -ForegroundColor Cyan
        & python $test
        if ($LASTEXITCODE -ne 0) { throw "Test failed: $test. Backup: $backupRoot" }
    }
}
finally {
    Pop-Location
}

Write-Host "`nTemporary diagnostic cleanup and migration runner installation completed." -ForegroundColor Green
Write-Host "Backup copies: $backupRoot"
Write-Host "Next, review git diff, commit and deploy the cleanup. Then run the migration runner from backend/."
