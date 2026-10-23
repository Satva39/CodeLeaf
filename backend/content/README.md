# CodeLeaf course content repository

Keep every technology in its own folder. Do not put all languages into one shared lesson file.

```text
backend/content/courses/<course-slug>/
├── course.json
├── modules/
│   └── <sequence>-<module-slug>/
│       ├── module.json
│       ├── lessons/
│       │   └── <sequence>-<lesson-slug>.json
│       └── exercises/
│           └── <sequence>-<exercise-slug>.json
├── projects/
│   └── <project-slug>.json
└── exams/
    └── exam-blueprint.json
```

- `course.json` is the course metadata and ordered list of module file paths.
- Each `module.json` lists its lesson files in order.
- Each lesson is its own JSON file and lists its exercise files.
- Exercise answer keys and grading rules stay in the backend content repository and are not sent to browsers.
- Keep lesson IDs/slugs stable after publication; changing a filename does not mean a learner should lose progress.
- Draft content is the default. Use the importer `--publish` option only after reviewing accuracy, licensing, accessibility and grading.
- XP rules are configured by the backend. Do not choose different XP amounts in each content file: each completed lesson and each correctly completed exercise has 20 base XP; Max and Full Access apply their server-side 50% boost.

Import a course from the `backend` directory:

```powershell
python scripts/import_course_files.py --course-slug html
```

Dry-run by default. Preview all checks first. To write draft rows:

```powershell
python scripts/import_course_files.py --course-slug html --apply
```

To publish approved content:

```powershell
python scripts/import_course_files.py --course-slug html --apply --publish
```

Production must use the reviewed database migration and a backed-up database. Never put API keys, user secrets, or private assessment keys in frontend files.
