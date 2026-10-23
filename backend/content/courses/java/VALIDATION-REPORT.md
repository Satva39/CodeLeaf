# Java course validation report

**Course status:** Draft; no content was published and no production deployment was attempted.

## Automated checks performed

| Check | Result | Evidence |
|---|---|---|
| CodeLeaf course-tree validator | PASS | `python scripts/validate_course_content.py --course-slug java` returned status `draft` and confirmed all referenced files, IDs, relationships, graders, asset paths, and SVG XML. |
| Existing importer dry run | PASS | `python scripts/import_course_files.py --course-slug java` validated 32 modules, 336 lessons, 48 exercises, 10 projects, 1,008 protected knowledge-check questions, and 368 visuals; it reported `DRY RUN ONLY` and no database changes. |
| JSON/reference/relationship checks | PASS | Included in the repository validator; 826 course JSON files were discovered. |
| SVG/XML and asset-reference checks | PASS | Included in the repository validator; all 368 referenced SVG files were present and parsed successfully. |
| Standalone lesson examples compiled | PASS with runtime limitation | 330 complete Java lesson examples compiled together with `javac 21.0.12.1`; zero compiler errors. The single JDK 27 preview-only lesson was deliberately excluded. This does not prove Java 25/27 behavior because those JDKs were not installed in the validation environment. |
| Protected exercise solution examples compiled | PASS with one intentional exclusion | 47 complete single-file Java reference implementations compiled together with JDK 21; zero compiler errors. The modular CLI solution contains separate `module-info.java` and `Main.java` files and was excluded from the single-file batch compiler. |
| Representative lesson runtime smoke tests | PASS | 20 examples ran successfully, including console input with sample input, arithmetic, strings, arrays, OOP, collections, streams, BigDecimal, HTTP request construction, concurrency, JDBC query construction, assertions, and runtime diagnostics. External service/database examples were not executed against a real service. |
| Reference-solution runtime smoke tests | PASS | 12 task-specific exercise reference implementations ran successfully, including input parsing, validation, strings, collections, arithmetic, concurrency utilities, and local checks. Network/JDBC/environment-dependent solutions were compiled but not run against live services. |
| XP overrides | PASS | No lesson/exercise XP overrides are authored; the existing platform controls base XP and server-side plan boosts. |
| Answer separation | PASS | Exercise solutions and knowledge-check answer keys reside in protected repository content files, not in learner-facing lesson files. Deployment/API response behavior was not live-tested. |

## Not run / not verified

- PostgreSQL import with `--apply`; the database was intentionally not modified.
- API behavior against a live database or deployment, frontend rendering, or production deployment.
- Any CodeLeaf-hosted isolated Java execution runner; this patch does not add one.
- Java 25 LTS or Java 27 preview execution. The available host JDK was Java 21.0.12.1.
- Real HTTP calls, JDBC connectivity against a configured database, or production performance measurements.
- Human subject-matter review of all 336 lessons and every reference solution. All content is therefore marked `draft` and should be reviewed before publication.

## Commands to repeat from the repository backend directory

```powershell
python scripts/validate_course_content.py --course-slug java
python scripts/import_course_files.py --course-slug java
```

The importer command above is a dry run. After reviewing the course and configuring the existing database environment, apply drafts only using `python scripts/import_course_files.py --course-slug java --apply`. Do not publish draft content until subject-matter review and isolated execution-based grading are in place.
