param(
    [string]$ProjectRoot = "E:\Code_Leaf"
)
$ErrorActionPreference = "Stop"
$project = [System.IO.Path]::GetFullPath($ProjectRoot)
$patchRoot = Join-Path $PSScriptRoot "patch-files"
$originalRoot = Join-Path $PSScriptRoot "original-files"
if (-not (Test-Path (Join-Path $project "frontend\src\pages\AuthPage.jsx"))) {
    throw "Could not find frontend\src\pages\AuthPage.jsx under '$project'. Pass -ProjectRoot with your CodeLeaf project folder."
}

function Get-NormalizedSha256([string]$Path) {
    $content = [System.IO.File]::ReadAllText($Path)
    $content = $content.Replace("`r`n", "`n").Replace("`r", "`n")
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($content)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant() }
    finally { $sha.Dispose() }
}

$relativeFiles = @(
    "frontend\src\pages\AuthPage.jsx",
    "frontend\src\styles\account.css",
    "frontend\scripts\test_auth_ui_contract.mjs"
)
foreach ($rel in $relativeFiles) {
    $sourceRelative = $rel.Replace("\", "/")
    $current = Join-Path $project $rel
    $expectedOriginal = Join-Path $originalRoot $rel
    $replacement = Join-Path $patchRoot $rel
    if (-not (Test-Path $current)) { throw "Required project file is missing: $current" }
    if (-not (Test-Path $replacement)) { throw "Patch file is missing: $replacement" }
    if ((Get-NormalizedSha256 $current) -ne (Get-NormalizedSha256 $expectedOriginal)) {
        throw "Safety stop: '$rel' differs from the patch baseline. No files were changed. Review or merge this patch manually instead of overwriting your local changes."
    }
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupRoot = Join-Path $PSScriptRoot ("backups\" + $timestamp)
foreach ($rel in $relativeFiles) {
    $current = Join-Path $project $rel
    $expectedOriginal = Join-Path $originalRoot $rel
    $replacement = Join-Path $patchRoot $rel
    $backup = Join-Path $backupRoot $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $backup) | Out-Null
    Copy-Item -LiteralPath $current -Destination $backup
    Copy-Item -LiteralPath $replacement -Destination $current -Force
}
Write-Host "CodeLeaf password visibility and resend-button patch applied." -ForegroundColor Green
Write-Host "Backup files: $backupRoot"
Write-Host "Next: run npm run test:auth-ui and npm run build from the frontend folder."
