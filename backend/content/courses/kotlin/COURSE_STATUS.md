# Course status: Kotlin

- Course slug: `kotlin`
- Authoring status: `draft`
- Source syllabus: `Kotlin.pdf` (43 pages)
- Module count: 26
- Lesson count: 271
- Exercise count: 30
- Project briefs: 9 (eight staged projects plus one capstone)
- Lesson knowledge-check sets: 271 (813 protected questions)
- Final assessment question pool: 48 protected questions (28 concept checks, 10 code traces, 10 design/debug scenarios)
- Visual assets: 297 included SVG diagrams (one overview per module and one concept visual per lesson)

## Status and limitations

Content structure, stable IDs, file references, SVG paths, and the project's filesystem validation are intended for validation before import. The content remains draft and must not be treated as technically reviewed/published solely because structural validation passes. Code snippets are marked `static-validation`; several need project dependencies or a target-specific build. No live Kotlin execution runner, live exam runner, certificate issuance, deployment, database import, or production behavior was tested by this generator.

## Next steps

1. Run `python scripts/validate_course_content.py --course-slug kotlin` from `backend/`.
2. Run `python scripts/import_course_files.py --course-slug kotlin` for a database-free dry run.
3. After technical review, apply as draft using `python scripts/import_course_files.py --course-slug kotlin --apply`. Do not use `--publish` while authored statuses remain draft.
4. Run code examples in a target-appropriate local project, especially Modules 17–26.
