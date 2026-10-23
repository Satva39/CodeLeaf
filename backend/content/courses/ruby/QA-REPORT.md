# Ruby course QA report

Checked on 2026-10-20 against the supplied `Ruby.pdf` and CodeLeaf repository ZIP.

## Validation that passed

- Source syllabus inventory: 28 modules and 304 consecutive numbered lessons retained; all 28 Section C exercises and 12 Section D projects represented.
- CodeLeaf course content validator: passed all manifest, file/path, ID uniqueness, lesson/module relationship, question set, exercise/solution, project rubric, SVG XML, and forbidden-XP-key checks.
- CodeLeaf importer in default dry-run mode: passed and reported 28 modules, 304 lessons, 28 exercises, and 12 projects. No database writes were made.
- Ruby parser smoke check: all 304 lesson Ruby snippets passed `ruby -c` with the available Ruby 3.3.8 runtime.
- Introductory runtime smoke check: 173 examples from Modules 1–16 ran under Ruby 3.3.8 without runtime exceptions; one example that intentionally reopens `String` was skipped. Dynamic year placeholders were treated as illustrative output, not literal output.
- Asset integrity: 333 local SVG files exist, are listed in the asset manifest, and passed XML/path validation. The module overview visual was additionally raster-rendered for a visual sanity check.
- XP/security content check: no course-authored XP override keys; answer keys and solution outlines remain in repository-side files; Ruby execution is explicitly marked unavailable in the current CodeLeaf playground.

## Counts

- 28 modules
- 304 lessons
- 28 exercises with protected solution-outline files
- 12 project briefs with starter files and protected reference-solution outlines
- 304 lesson knowledge-check sets × 3 questions = 912 questions
- 1 final-exam blueprint and 30 final-exam questions
- 942 total knowledge-check/final-exam questions
- 333 original SVG visuals (1 course roadmap, 28 module overviews, 304 lesson diagrams)

## Not run / not verified

- Full functional execution of all 304 examples was not performed. The later file/network/database/framework/concurrency/runtime-specific examples may require gems, local services, a version-specific runtime, or safe fixture setup.
- The target baseline in the course is Ruby 4.0.7. The available runner was Ruby 3.3.8, so review version-specific behavior on Ruby 4.0.7 before publication.
- No `--apply` database import, PostgreSQL migration, live API/catalog interaction, frontend build, deployment, payment, or production execution was performed.
- The current CodeLeaf playground only previews HTML/CSS/JavaScript. This patch does not add an isolated Ruby runner. Do not execute learner-supplied Ruby code inside FastAPI.
- The static required-token exercise grader is only a smoke check and does not compile or run Ruby; exercises remain draft pending technical review and an appropriate runner or human-review workflow.

## Reproducible local commands (Windows PowerShell)

From the Code_Leaf repository root:

```powershell
cd backend
python scripts\validate_course_content.py --course-slug ruby
python scripts\import_course_files.py --course-slug ruby
```

The import command above is dry-run only. After reviewing the drafts and configuring a non-production PostgreSQL connection privately, apply the draft data with:

```powershell
python scripts\import_course_files.py --course-slug ruby --apply
```

Do not use `--publish` before review. The importer writes course/module/lesson/exercise records; project briefs and exam files are stored as course files but are not yet imported into dedicated project/exam tables by the existing importer.

## Official references checked

- Ruby 4.0.7 release announcement: https://www.ruby-lang.org/en/news/2026/09/15/ruby-4-0-7-released/
- Ruby official news archive (includes the October 2026 preview announcement): https://www.ruby-lang.org/en/news/
- Ruby 4.0 documentation: https://docs.ruby-lang.org/en/4.0/
- RubyGems guides: https://guides.rubygems.org/
- Bundler guide: https://bundler.io/guides/getting_started.html
- Rails Getting Started guide: https://guides.rubyonrails.org/getting_started.html
