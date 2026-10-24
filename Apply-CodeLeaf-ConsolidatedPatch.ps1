[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$ManifestPath = Join-Path $PSScriptRoot 'PATCH-MANIFEST.json'
$PayloadRoot = Join-Path $PSScriptRoot 'patch-files'

if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'frontend/package.json') -PathType Leaf)) {
    throw "ProjectRoot does not look like CodeLeaf (frontend/package.json not found): $ProjectRoot"
}
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot 'backend/app/main.py') -PathType Leaf)) {
    throw "ProjectRoot does not look like CodeLeaf (backend/app/main.py not found): $ProjectRoot"
}
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw "Manifest missing: $ManifestPath" }
if (-not (Test-Path -LiteralPath $PayloadRoot -PathType Container)) { throw "Patch payload missing: $PayloadRoot" }

$Manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$CopyPaths = @($Manifest.modified_files) + @($Manifest.added_files)
$RemovePaths = @($Manifest.remove_files)
$AllPaths = @($CopyPaths) + @($RemovePaths)
$BackupRoot = Join-Path $env:USERPROFILE ("CodeLeaf-Consolidated-Backup-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))

foreach ($RelativePath in $AllPaths) {
    if ([string]::IsNullOrWhiteSpace($RelativePath)) { throw 'Manifest contains an empty path.' }
    if ([System.IO.Path]::IsPathRooted($RelativePath) -or $RelativePath -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Unsafe path in manifest: $RelativePath"
    }
}
foreach ($RelativePath in $CopyPaths) {
    $LocalPath = $RelativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $SourcePath = Join-Path $PayloadRoot $LocalPath
    if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
        throw "Patch payload is missing a declared file: $RelativePath"
    }
}

New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null

foreach ($RelativePath in $CopyPaths) {
    $LocalPath = $RelativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $SourcePath = Join-Path $PayloadRoot $LocalPath
    $DestinationPath = Join-Path $ProjectRoot $LocalPath
    if (Test-Path -LiteralPath $DestinationPath -PathType Leaf) {
        $BackupPath = Join-Path $BackupRoot $LocalPath
        New-Item -ItemType Directory -Path (Split-Path -Parent $BackupPath) -Force | Out-Null
        Copy-Item -LiteralPath $DestinationPath -Destination $BackupPath -Force
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $DestinationPath) -Force | Out-Null
    Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
}

foreach ($RelativePath in $RemovePaths) {
    $LocalPath = $RelativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $DestinationPath = Join-Path $ProjectRoot $LocalPath
    if (Test-Path -LiteralPath $DestinationPath -PathType Leaf) {
        $BackupPath = Join-Path $BackupRoot $LocalPath
        New-Item -ItemType Directory -Path (Split-Path -Parent $BackupPath) -Force | Out-Null
        Copy-Item -LiteralPath $DestinationPath -Destination $BackupPath -Force
        Remove-Item -LiteralPath $DestinationPath -Force
        Write-Host "Removed leftover patch artifact (a backup was saved): $RelativePath"
    }
}

Write-Host ''
Write-Host 'CodeLeaf consolidated source files were copied.' -ForegroundColor Green
Write-Host "Backup of overwritten/removed files: $BackupRoot" -ForegroundColor Cyan
Write-Host 'No environment secrets, node_modules, course content folders, or database data were changed by this installer.'
Write-Host 'Next: review git status and run the tests listed in INSTALL-INSTRUCTIONS.txt.'
