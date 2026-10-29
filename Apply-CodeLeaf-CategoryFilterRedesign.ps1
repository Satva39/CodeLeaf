param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$homePath = Join-Path $resolvedRoot 'frontend\src\pages\HomePage.jsx'
$cssPath = Join-Path $resolvedRoot 'frontend\src\styles\home.css'

foreach ($path in @($homePath, $cssPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Could not find required CodeLeaf file: $path"
    }
}

$home = [System.IO.File]::ReadAllText($homePath)

# Add only the two icons used by the compact category filter.
if ($home -notmatch '(?m)^\s*SlidersHorizontal,\s*$') {
    $importPattern = '(?m)^  ArrowRight,\s*$'
    if ($home -notmatch $importPattern) {
        throw 'Could not find the expected lucide-react icon import in HomePage.jsx.'
    }
    $importRegex = [System.Text.RegularExpressions.Regex]::new($importPattern)
    $home = $importRegex.Replace(
        $home,
        "  ArrowRight,`r`n  ChevronDown,`r`n  SlidersHorizontal,",
        1
    )
}

$newFilter = @'
        <div className="course-category-filter" role="group" aria-label="Filter courses by category">
          <div className="course-category-filter__label">
            <SlidersHorizontal size={16} aria-hidden="true" />
            <span>Filter by category</span>
          </div>
          <label className="course-category-filter__select">
            <span className="sr-only">Course category</span>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              aria-label="Filter courses by category"
            >
              <option value="All">All categories</option>
              {categories.slice(1).map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <ChevronDown size={16} aria-hidden="true" />
          </label>
          <div className="course-category-filter__result" aria-live="polite">
            <strong>{courses.length}</strong>
            <span>{courses.length === 1 ? "course" : "courses"}</span>
          </div>
          {category !== "All" && (
            <button
              type="button"
              className="course-category-filter__clear"
              onClick={() => setCategory("All")}
            >
              Clear filter
            </button>
          )}
        </div>
'@

if ($home -notmatch 'className="course-category-filter"') {
    $oldPattern = '(?s)<div className="category-tabs">\s*\{categories\.map\(\(c\) => \(\s*<button\s+key=\{c\}\s+onClick=\{\(\) => setCategory\(c\)\}\s+className=\{category === c \? "active" : ""\}\s*>\s*\{c\}\s*</button>\s*\)\)\}\s*</div>'
    $categoryRegex = [System.Text.RegularExpressions.Regex]::new($oldPattern)
    $newHome = $categoryRegex.Replace($home, [System.Text.RegularExpressions.MatchEvaluator]{ param($match) $newFilter.TrimEnd() }, 1)
    if ($newHome -eq $home) {
        throw 'Could not find the expected category-tabs block. No source files were changed.'
    }
    $home = $newHome
}

# Remove the older CSS-only category chip patch if it exists; those styles target the retired markup.
$css = [System.IO.File]::ReadAllText($cssPath)
$oldStart = '/* CODELEAF_CATEGORY_TABS_POLISH_START */'
$oldEnd = '/* CODELEAF_CATEGORY_TABS_POLISH_END */'
$startIndex = $css.IndexOf($oldStart, [System.StringComparison]::Ordinal)
if ($startIndex -ge 0) {
    $endIndex = $css.IndexOf($oldEnd, $startIndex + $oldStart.Length, [System.StringComparison]::Ordinal)
    if ($endIndex -lt 0) {
        throw 'Found the old category CSS marker without its closing marker. Restore home.css from backup before retrying.'
    }
    $endIndex += $oldEnd.Length
    if ($endIndex -lt $css.Length -and $css[$endIndex] -eq "`r") { $endIndex++ }
    if ($endIndex -lt $css.Length -and $css[$endIndex] -eq "`n") { $endIndex++ }
    $css = $css.Remove($startIndex, $endIndex - $startIndex)
}

$filterStart = '/* CODELEAF_CATEGORY_FILTER_REDESIGN_START */'
$filterEnd = '/* CODELEAF_CATEGORY_FILTER_REDESIGN_END */'
$startIndex = $css.IndexOf($filterStart, [System.StringComparison]::Ordinal)
if ($startIndex -ge 0) {
    $endIndex = $css.IndexOf($filterEnd, $startIndex + $filterStart.Length, [System.StringComparison]::Ordinal)
    if ($endIndex -lt 0) {
        throw 'Found the category filter redesign start marker without its closing marker.'
    }
    $endIndex += $filterEnd.Length
    if ($endIndex -lt $css.Length -and $css[$endIndex] -eq "`r") { $endIndex++ }
    if ($endIndex -lt $css.Length -and $css[$endIndex] -eq "`n") { $endIndex++ }
    $css = $css.Remove($startIndex, $endIndex - $startIndex)
}

$cssPatch = @'
/* CODELEAF_CATEGORY_FILTER_REDESIGN_START */
/* A compact, accessible filter replaces the long wrapping category list. */
.course-category-filter {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  min-width: 0;
  margin: 0 0 18px;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel);
}
.course-category-filter__label {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  flex: 0 0 auto;
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}
.course-category-filter__label svg {
  color: var(--mint);
  flex: 0 0 auto;
}
.course-category-filter__select {
  position: relative;
  display: flex;
  align-items: center;
  flex: 0 1 360px;
  min-width: 220px;
  max-width: 100%;
}
.course-category-filter__select select {
  appearance: none;
  width: 100%;
  min-width: 0;
  min-height: 42px;
  padding: 0 42px 0 13px;
  color: var(--text);
  background: var(--panel-soft);
  border: 1px solid var(--line);
  border-radius: 10px;
  font: inherit;
  font-size: 13px;
  line-height: 1.35;
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
}
.course-category-filter__select select:hover {
  border-color: rgba(39, 214, 160, 0.42);
}
.course-category-filter__select select:focus-visible {
  outline: 2px solid var(--mint);
  outline-offset: 2px;
  border-color: var(--mint);
}
.course-category-filter__select select option {
  color: var(--text);
  background: var(--panel);
}
.course-category-filter__select > svg {
  position: absolute;
  right: 13px;
  color: var(--muted);
  pointer-events: none;
}
.course-category-filter__result {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-height: 32px;
  margin-left: auto;
  padding: 0 11px;
  color: var(--muted);
  background: var(--panel-soft);
  border: 1px solid var(--line);
  border-radius: 999px;
  font-size: 12px;
  white-space: nowrap;
}
.course-category-filter__result strong {
  color: var(--text);
  font-variant-numeric: tabular-nums;
}
.course-category-filter__clear {
  min-height: 34px;
  padding: 0 12px;
  color: var(--mint);
  background: var(--mint-wash);
  border: 1px solid rgba(39, 214, 160, 0.22);
  border-radius: 9px;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.18s ease, border-color 0.18s ease;
}
.course-category-filter__clear:hover {
  background: rgba(39, 214, 160, 0.14);
  border-color: rgba(39, 214, 160, 0.48);
}
.course-category-filter__clear:focus-visible {
  outline: 2px solid var(--mint);
  outline-offset: 2px;
}
@media (max-width: 640px) {
  .course-category-filter {
    align-items: stretch;
    gap: 10px;
    padding: 12px;
  }
  .course-category-filter__label {
    width: 100%;
  }
  .course-category-filter__select {
    flex: 1 1 100%;
    width: 100%;
    min-width: 0;
  }
  .course-category-filter__result {
    margin-left: 0;
  }
  .course-category-filter__clear {
    flex: 1 1 auto;
  }
}
@media (prefers-reduced-motion: reduce) {
  .course-category-filter__select select,
  .course-category-filter__clear {
    transition: none;
  }
}
/* CODELEAF_CATEGORY_FILTER_REDESIGN_END */
'@

$css = $css.TrimEnd() + "`r`n`r`n" + $cssPatch + "`r`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($homePath, $home, $utf8NoBom)
[System.IO.File]::WriteAllText($cssPath, $css, $utf8NoBom)
Write-Host 'Applied compact Home page course-category filter.' -ForegroundColor Green
Write-Host 'The selected category state and course filtering logic are preserved.' -ForegroundColor Cyan
