[CmdletBinding()]
param(
    [switch]$RunProductionSmoke,
    [string]$FrontendUrl = $env:CODELEAF_FRONTEND_URL,
    [string]$BackendUrl = $env:CODELEAF_BACKEND_URL
)

$ErrorActionPreference = 'Continue'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $ProjectRoot 'backend'
$FrontendRoot = Join-Path $ProjectRoot 'frontend'
$Failures = @()

if (-not (Test-Path -LiteralPath $BackendRoot -PathType Container)) { throw "Backend folder not found: $BackendRoot" }
if (-not (Test-Path -LiteralPath $FrontendRoot -PathType Container)) { throw "Frontend folder not found: $FrontendRoot" }

$Python = Join-Path $BackendRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { $Python = 'python' }

Write-Host '=== Backend compile ===' -ForegroundColor Cyan
Push-Location $BackendRoot
try {
    & $Python -m compileall -q app scripts alembic
    if ($LASTEXITCODE -ne 0) { $Failures += 'Backend compileall' }

    $BackendTests = @(
        'scripts/check_alembic_heads.py',
        'scripts/check_repository_hygiene.py',
        'scripts/test_phase1_config.py',
        'scripts/test_auth_lifecycle.py',
        'scripts/test_course_api_contract.py',
        'scripts/test_course_import_safety.py',
        'scripts/test_dynamic_diagram_compatibility.py',
        'scripts/test_knowledge_check_api.py',
        'scripts/test_phase3_catalog_contract.py',
        'scripts/test_migration_repeatability.py',
        'scripts/test_phase2_content_routes.py',
        'scripts/test_phase2_exam_api.py',
        'scripts/test_payment_security.py',
        'scripts/test_analytics_summary_api.py',
        'scripts/test_phase5_contract.py',
        'scripts/test_phase5_diagrams.py',
        'scripts/test_review_rating_policy.py',
        'scripts/test_review_queue_api.py',
        'scripts/test_runner_config_status.py',
        'scripts/test_smtp_delivery.py'
    )
    foreach ($TestPath in $BackendTests) {
        if (Test-Path -LiteralPath $TestPath -PathType Leaf) {
            Write-Host "=== Backend: $TestPath ===" -ForegroundColor Cyan
            & $Python $TestPath
            if ($LASTEXITCODE -ne 0) { $Failures += $TestPath }
        }
    }
} finally {
    Pop-Location
}

Push-Location $FrontendRoot
try {
    $FrontendTests = @(
        'scripts/test_course_catalog_filters.mjs',
        'scripts/test_api_cache.mjs',
        'scripts/test_api_client.mjs',
        'scripts/test_api_proxy.mjs',
        'scripts/test_auth_ui_contract.mjs',
        'scripts/test_course_overview_cta.mjs',
        'scripts/test_review_queue.mjs',
        'scripts/test_phase3c_personal_learning.mjs',
        'scripts/test_learning_path.mjs',
        'scripts/test_phase2_content_consistency.mjs',
        'scripts/test_reference_details.mjs',
        'scripts/test_lesson_live_examples.mjs',
        'scripts/test_phase5_routes.mjs',
        'scripts/test_runner_status_ui.mjs',
        'scripts/test_ui_polish.mjs'
    )
    foreach ($TestPath in $FrontendTests) {
        if (Test-Path -LiteralPath $TestPath -PathType Leaf) {
            Write-Host "=== Frontend: $TestPath ===" -ForegroundColor Cyan
            & node $TestPath
            if ($LASTEXITCODE -ne 0) { $Failures += $TestPath }
        }
    }
    Write-Host '=== Vite production build ===' -ForegroundColor Cyan
    & npm run build
    if ($LASTEXITCODE -ne 0) { $Failures += 'npm run build' }
} finally {
    Pop-Location
}


$RunnerRoot = Join-Path $ProjectRoot 'runner_service'
if (Test-Path -LiteralPath (Join-Path $RunnerRoot 'test_runner_service.py') -PathType Leaf) {
    Push-Location $RunnerRoot
    try {
        Write-Host '=== Isolated runner tests ===' -ForegroundColor Cyan
        & $Python -m unittest -v test_runner_service.py
        if ($LASTEXITCODE -ne 0) { $Failures += 'runner_service/test_runner_service.py' }
    } finally {
        Pop-Location
    }
}

if ($RunProductionSmoke) {
    if ([string]::IsNullOrWhiteSpace($FrontendUrl) -or [string]::IsNullOrWhiteSpace($BackendUrl)) {
        Write-Warning 'Production smoke checks skipped. Set CODELEAF_FRONTEND_URL and CODELEAF_BACKEND_URL first.'
    } else {
        $SmokeChecks = @(
            @{ Name = 'Render readiness'; Url = $BackendUrl.TrimEnd('/') + '/api/ready'; Kind = 'ready' },
            @{ Name = 'Vercel proxied readiness'; Url = $FrontendUrl.TrimEnd('/') + '/api/ready'; Kind = 'ready' },
            @{ Name = 'Vercel course catalog'; Url = $FrontendUrl.TrimEnd('/') + '/api/courses'; Kind = 'catalog' }
        )
        foreach ($Check in $SmokeChecks) {
            try {
                $Response = Invoke-WebRequest -Uri $Check.Url -Method Get -UseBasicParsing -TimeoutSec 35
                if ($Response.StatusCode -lt 200 -or $Response.StatusCode -ge 300) { throw "Unexpected HTTP status $($Response.StatusCode)" }
                $Payload = $Response.Content | ConvertFrom-Json
                if ($Check.Kind -eq 'ready' -and $Payload.status -ne 'ready') { throw 'Readiness response did not report status=ready.' }
                if ($Check.Kind -eq 'catalog' -and $null -eq $Payload.items) { throw 'Catalog response did not contain items.' }
                Write-Host "PASS: $($Check.Name)" -ForegroundColor Green
            } catch {
                Write-Host "FAIL: $($Check.Name) - $($_.Exception.Message)" -ForegroundColor Red
                $Failures += $Check.Name
            }
        }
    }
}

Write-Host "`nVerification summary: $($Failures.Count) failed check(s)." -ForegroundColor Cyan
if ($Failures.Count -gt 0) {
    foreach ($Failure in $Failures) { Write-Host " - $Failure" -ForegroundColor Red }
    exit 1
}
Write-Host 'All executed checks passed.' -ForegroundColor Green
