# PowerShell course validation report

**Run date:** 2026-10-20  
**Content status:** draft  
**Scope:** new PowerShell course content only; no application, schema, migration, dependency, frontend, or deployment configuration was changed.

## Course inventory

- 26 modules and 286 lessons, checked against the numbered curriculum in the supplied 55-page PDF.
- 20 practical exercises and 13 project briefs (12 projects plus the named capstone).
- 286 lesson knowledge-check sets with 3 questions each (858) plus 30 final-assessment questions: 888 questions total.
- 1 final-exam blueprint and 5 specialist learning tracks.
- 312 original SVG visuals (26 module overviews and 286 lesson diagrams). Every file is inventoried in `ASSET-CHECKLIST.md` and `assets/asset-manifest.json`.

## Checks

| Check | Result | Evidence / limitation |
|---|---|---|
| PDF syllabus inventory | PASS | Parsed 26 module headings and lesson numbers 1–286 in order; generated lesson titles and captured subtopics match the parsed syllabus records. |
| JSON, IDs, references, grader schema, asset paths and SVG XML | PASS | `python scripts/validate_course_content.py --course-slug powershell` returned successfully with no findings. |
| Importer validation | PASS (dry run only) | `python scripts/import_course_files.py --course-slug powershell` reported 26 modules, 286 lessons, 20 exercises, 13 projects, 888 questions and 312 visuals. It confirmed no database changes were made. |
| Additional path / answer-key / asset audit | PASS | Custom structural check reported zero errors; all 312 manifest paths exist, SVGs parse, quiz answer keys match an option, and all 312 assets are in the checklist. |
| SVG visual review | PASS with shortened labels | Rendered samples were reviewed and card spacing/connector overlap was corrected. The diagrams are original sequence/roadmap visuals; they are not substitutes for running the PowerShell examples. |
| Backend Python syntax | PASS | `python -m compileall -q app scripts` completed with exit code 0. This does not validate runtime/database behavior. |
| Repository-wide pytest collection | BLOCKED / FAILED BEFORE TEST EXECUTION | `python -m pytest -q` encountered 21 collection errors in existing unrelated DSA starter tests (duplicate imported module name `test_starter`) and SciPy starter tests (`ModuleNotFoundError: src.main`). No PowerShell course test was reported failing. |
| Frontend build | BLOCKED | `npm run build` could not start Vite because frontend dependencies are absent in the extracted working tree (`vite: not found`). This patch changes no frontend source. |
| PowerShell snippet execution, Pester, PSScriptAnalyzer | NOT RUN | Neither `pwsh` nor Windows PowerShell was installed in the generation environment. Code examples are labeled `static-validation`; runtime output must be confirmed locally before publication. |
| Database apply, migrations, live API/progress/XP integration, deployment | NOT RUN | The patch is content-only; the importer was run without `--apply`. No production database or deployment was touched. |

## Before publication

1. Review snippets and expected outputs in PowerShell 7.6 LTS; check any Windows PowerShell 5.1 compatibility note separately.
2. Run Pester tests and PSScriptAnalyzer in a PowerShell-enabled environment; verify admin/remoting examples only on an authorized lab system.
3. Have a PowerShell subject-matter reviewer verify knowledge checks, answers, lesson explanations, and the protected reference-solution outlines. All content remains draft.
4. Re-run the course validator and importer dry run. Only apply/import or publish after review; follow the existing CodeLeaf importer and publication controls.
