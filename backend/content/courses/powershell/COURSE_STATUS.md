# Course generation status — PowerShell

- **Status:** draft; not approved for learner publication.
- **Syllabus:** 26 modules, 286 numbered lessons, 20 practical exercises, 12 named projects plus capstone.
- **Knowledge checks:** 286 separate sets × 3 questions each = 858 lesson questions. Final assessment bank: 30 additional questions.
- **Visuals:** 26 module overview diagrams and 286 lesson diagrams = 312 included SVG files. See `ASSET-CHECKLIST.md` and `assets/asset-manifest.json` for complete per-file details.
- **Backend integration:** the existing importer, validator and API/catalog entry points are reused. No schema, migration, app code, dependency, Vercel, Render or Docker changes are included in this patch.
- **Execution testing:** no `pwsh` or Windows PowerShell runtime was available in the generation environment. Example execution, Pester, PSScriptAnalyzer and live database behavior are not claimed as tested.
- **Required before publication:** install/use the targeted PowerShell runtime, validate the snippets and expected results; review assessment quality, answer keys and protected solution outlines; execute Pester/static analysis and test the course through the current importer/database flow.
