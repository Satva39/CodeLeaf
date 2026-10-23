# Bootstrap course patch — validation report

## Generated inventory

- Course slug: `bootstrap`
- State: `draft`
- Curriculum baseline: Bootstrap 5.3.8, matching the supplied 37-page PDF
- Modules: 12
- Lessons: 161
- Exercises: 23
- Project briefs: 10 (including a capstone)
- Protected lesson knowledge-check sets: 161
- Protected knowledge-check questions: 483
- Final-exam blueprint: 1
- Local SVG diagrams: 31
- JSON files in the course tree: 406

The 161 numbered core syllabus topics from the supplied PDF are represented in sequence. The course also carries practical projects, a learning roadmap, source references, and review notes. All generated course records are marked draft. Bootstrap 4 migration and Bootstrap 6 alpha content are treated as non-core/optional rather than production-baseline instructions.

## Checks run

| Check                                        | Result | Evidence / scope                                                                                                                                                                          |
| -------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CodeLeaf course content validator            | PASS   | `validate_course_content.py --course-slug bootstrap`; validated 12 modules, 161 lessons, 23 exercises, 10 projects, 483 protected questions, 31 SVGs, and 406 JSON files.                 |
| Importer dry run                             | PASS   | `import_course_files.py --course-slug bootstrap`; importer explicitly reported `DRY RUN ONLY` and `No database changes made`.                                                             |
| JSON/reference/relationship/asset validation | PASS   | CodeLeaf validator confirmed referenced files, IDs, relationships, graders, asset paths, and SVG XML.                                                                                     |
| Additional quiz/exercise integrity scan      | PASS   | 161 question sets / 483 questions; answer keys point to existing options; no duplicate options; 23 example solutions satisfy their configured grading markers; no XP override keys found. |
| Syllabus coverage scan                       | PASS   | All 161 numbered PDF topics are mapped in the ordered course and lessons.                                                                                                                 |
| SVG XML parse scan                           | PASS   | All 31 SVG files parsed.                                                                                                                                                                  |
| JavaScript syntax checks                     | PASS   | `node --check` succeeded for 17 extracted JS code/inline-script samples. This is a syntax check, not a browser runtime test.                                                              |
| ZIP integrity and patch inventory            | PASS   | `unzip -t` completed with no errors; archive paths were checked to start at repository-root-relative `backend/` plus the two patch documents.                                             |

## Not run / limitations

- No `--apply` import or database write was performed. There was no DB schema change in this patch.
- No full backend test suite, migration test, frontend production build, browser screenshot/runtime check, assistive-technology audit, Sass compilation, live CDN/SRI check, or production deployment was run.
- Existing XP idempotency, streak, authorization, payment, and certificate logic were not changed or newly tested by this content-only patch. The content contains no XP reward overrides; the existing platform remains authoritative.
- The JavaScript syntax pass does not prove that every snippet behaves correctly in every browser or in a Bootstrap-loaded page. Review and execute examples in the intended lesson runtime before publication.
- Publication remains a human decision. Recheck official Bootstrap release notes and documentation immediately before publishing because version information can change.

## Exact Windows PowerShell commands

From the repository root:

```powershell
Set-Location .\backend
python scripts\validate_course_content.py --course-slug bootstrap
python scripts\import_course_files.py --course-slug bootstrap
```

The second command is a dry run. After content review and confirmation that the configured database is the intended target, to import draft records:

```powershell
python scripts\import_course_files.py --course-slug bootstrap --apply
```

Only after a separate human content/accessibility review, to publish the course:

```powershell
python scripts\import_course_files.py --course-slug bootstrap --apply --publish
```

Do not use `--apply` or `--publish` merely to test the patch; they have persistent effects.

## Official references embedded in course content

The reference index points to the official Bootstrap 5.3 docs for introduction, grid, breakpoints, containers, utilities, components, forms/validation, JavaScript, accessibility, Sass/customization, color modes, Vite, migration, Bootstrap Icons, releases, and license. Baseline release metadata is sourced from the provided curriculum and should be rechecked before publication.
