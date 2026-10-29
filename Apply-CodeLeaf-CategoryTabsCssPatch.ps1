param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$cssPath = Join-Path $resolvedRoot 'frontend\src\styles\home.css'
if (-not (Test-Path -LiteralPath $cssPath -PathType Leaf)) {
    throw "Could not find frontend CSS file: $cssPath"
}

$startMarker = '/* CODELEAF_CATEGORY_TABS_POLISH_START */'
$endMarker = '/* CODELEAF_CATEGORY_TABS_POLISH_END */'
$content = [System.IO.File]::ReadAllText($cssPath)
$start = $content.IndexOf($startMarker, [System.StringComparison]::Ordinal)
if ($start -ge 0) {
    $end = $content.IndexOf($endMarker, $start + $startMarker.Length, [System.StringComparison]::Ordinal)
    if ($end -lt 0) {
        throw 'Found the category CSS start marker but not its end marker. Restore home.css from backup before retrying.'
    }
    $end += $endMarker.Length
    if ($end -lt $content.Length -and $content[$end] -eq "`r") { $end++ }
    if ($end -lt $content.Length -and $content[$end] -eq "`n") { $end++ }
    $content = $content.Remove($start, $end - $start)
}

$cssPatch = @'
/* CODELEAF_CATEGORY_TABS_POLISH_START */
/* Keep the Home page's large category list compact and visually consistent. */
.category-tabs {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 9px;
  min-width: 0;
  max-width: 100%;
  margin-bottom: 18px;
  padding: 3px 3px 10px;
  overflow-x: auto;
  overflow-y: hidden;
  overscroll-behavior-inline: contain;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: var(--line) transparent;
}
.category-tabs::-webkit-scrollbar {
  height: 5px;
}
.category-tabs::-webkit-scrollbar-track {
  background: transparent;
}
.category-tabs::-webkit-scrollbar-thumb {
  background: var(--line);
  border-radius: 999px;
}
.category-tabs button {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  min-width: 0;
  max-width: min(100%, 285px);
  min-height: 38px;
  padding: 8px 13px;
  color: var(--muted);
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 999px;
  font-size: 12.1px;
  font-weight: 600;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
  transition:
    color 0.18s ease,
    background-color 0.18s ease,
    border-color 0.18s ease,
    transform 0.18s ease;
}
.category-tabs button:hover {
  color: var(--text);
  background: var(--panel-soft);
  border-color: rgba(39, 214, 160, 0.35);
  transform: translateY(-1px);
}
.category-tabs button:focus-visible {
  outline: 2px solid var(--mint);
  outline-offset: 2px;
}
.category-tabs button.active {
  color: var(--mint);
  background: var(--mint-wash);
  border-color: rgba(39, 214, 160, 0.4);
  box-shadow: inset 0 0 0 1px rgba(39, 214, 160, 0.06);
  font-weight: 800;
}
@media (prefers-reduced-motion: reduce) {
  .category-tabs {
    scroll-behavior: auto;
  }
  .category-tabs button {
    transition: none;
  }
  .category-tabs button:hover {
    transform: none;
  }
}
/* CODELEAF_CATEGORY_TABS_POLISH_END */
'@

$updated = $content.TrimEnd() + "`r`n`r`n" + $cssPatch + "`r`n"
[System.IO.File]::WriteAllText($cssPath, $updated, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Applied Home category filter CSS to: $cssPath" -ForegroundColor Green
Write-Host 'No components, pricing, checkout, or entitlement code was modified.' -ForegroundColor Cyan
