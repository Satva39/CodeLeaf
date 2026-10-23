# GitHub Actions Course Status

- **Status:** draft; not published.
- **Source:** `Github Actions.pdf` (47 pages). The rendered page contact sheet and extracted text were reviewed; `pdfimages -list` reported no embedded raster images. The PDF is a text-first curriculum blueprint, not a finished tutorial set.
- **Core syllabus:** 21 modules, all 162 numbered lessons and their extracted subtopics.
- **Optional syllabus:** 6 specialist lessons mapped from Section E; these are sequence 163–168 in CodeLeaf while retaining source labels E1–E6.
- **Practice:** 46 exercises (the 28 Section C exercises, 6 optional-track exercises, and 12 supplementary skill drills).
- **Projects:** 11 (10 source projects plus the source capstone).
- **Knowledge checks:** 168 lesson question sets, 3 questions each (504 questions).
- **Final assessment:** 1 exam blueprint with a separate 60-question protected bank.
- **Visuals:** 22 original SVG module-overview diagrams plus 12 lesson/course-level concept diagrams (34 SVGs total).
- **Course files are separate:** each module, lesson, exercise, protected solution, question set, project, reference index, and manifest is its own JSON file where supported by the existing importer.

## Integration

The existing CodeLeaf importer and API already support directory-based courses, separate lesson files, protected knowledge checks, project starter metadata, SVG assets, and database upserts. No frontend, backend route, schema, migration, dependency, hosting, or environment-file changes are required for this content package.

## Publication gate

All authored content remains `draft`. Review examples and feature availability against the actual repository, runner, plan, and GitHub Enterprise Server version before changing status values. Importing the draft records does not make the course public. Do not issue a certificate solely because this content package exists; exam verification and persistence must be handled by the platform.
