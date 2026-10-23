# Go course status

**State:** DRAFT — generated content is complete at the file-structure level but has not been editorially approved for publication.

## Counts

- Modules: 25
- Lessons: 270
- Exercises: 35
- Projects: 10
- Final exam blueprint: 1 (4 protected question files)
- Per-lesson knowledge checks: 270 sets, 810 questions
- Original SVG visuals: 44 including the course roadmap

## Remaining review before publication

1. Run `python scripts/validate_course_content.py --course-slug go` and the importer dry-run from `backend/`.
2. Verify/compile examples with Go 1.27.2 and a supported OS toolchain, with special attention to Go 1.27 generic methods, version-sensitive JSON/UUID APIs, command snippets, and driver-dependent SQL.
3. Human-review the correctness of lesson-level prose, multiple-choice answer keys, exercise solutions, project starters, source alignment, and keyboard/screen-reader presentation.
4. Test authenticated API delivery and knowledge-check privacy against a non-production database after validation.
5. Only after review, change course/module/lesson/exercise/project/assessment status values in a deliberate publication workflow and import with `--apply --publish`.

No Go runtime compile, production database import, frontend build, external service, live database, or deployment test is claimed by this package.
