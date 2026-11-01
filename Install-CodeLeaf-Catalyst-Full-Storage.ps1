[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$BackendRoot = Join-Path $ProjectRoot 'backend'
$PackageRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$Required = @(
    'app\config.py',
    'app\models.py',
    'app\main.py',
    'scripts\import_course_files.py',
    '.env.example',
    'alembic\versions\0010_catalyst_stratus_archive_storage.py',
    'app\storage\catalyst_stratus.py',
    'scripts\migrate_portfolio_archives_to_stratus.py'
)
foreach ($relative in $Required) {
    $path = Join-Path $BackendRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required existing CodeLeaf file is missing: $path. No project files were changed."
    }
}

$Installer = Join-Path $PackageRoot 'install_course_content_patch.py'
if (-not (Test-Path -LiteralPath $Installer -PathType Leaf)) {
    throw "Patch installer is missing: $Installer"
}

Write-Host "Applying CodeLeaf lesson + project ZIP storage patch..." -ForegroundColor Cyan
python $Installer --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    throw "Patch installer failed with exit code $LASTEXITCODE. Review its output; it is designed to stop on source mismatches."
}

Write-Host "Patch installation finished. Review git diff and run the documented tests before committing." -ForegroundColor Green
