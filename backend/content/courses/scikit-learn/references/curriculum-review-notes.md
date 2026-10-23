# Curriculum source and correction log

## Source coverage

- Inspected the complete 65-page `Scikit.pdf`, including the overview, all 18 curriculum modules, 188 numbered lesson topics and their listed subtopics, practical exercises, projects/capstone, specialist-track guidance, suggested learning stages, and the curriculum quality check.
- The course preserves the 18 modules, ordered topic numbering 1–188, the Section C 30 practical exercises, Section D 10 named projects plus the separate capstone, and the specialist options in Section E. No numbered Section B topic was omitted or renumbered; the supplied syllabus's topic and subtopic coverage is preserved in `references/syllabus-index.json`. All authored lessons, exercises, projects, assessments, and visuals are draft.
- Lesson explanations, code examples, diagram artwork, structured exercise scaffolds, rubrics, and protected reviewer guides are original CodeLeaf authoring; they are not copied from other learning platforms.

## Version assumptions and items requiring review

- The PDF identifies Scikit-learn 1.9.1 as released in September 2026. Official stable documentation was checked on 2026-10-20 and identifies the 1.9.1 documentation. The available local smoke-test environment may install an earlier version; therefore passing local tests does not by itself certify every new 1.9.1 API.
- Review all API names and constructor parameters against the version used to publish demonstrations. In particular, metadata routing, callbacks/training instrumentation, Array API interoperability, threshold tuning, output configuration, histogram gradient boosting behavior, and model export formats are version sensitive.
- Preserve the PDF's note that `IterativeImputer` has documented experimental status where applicable; do not promote an experimental API to a stable prerequisite without checking the installed-version docs.
- The PDF describes forecasting-related applications but warns against treating Scikit-learn as a dedicated forecasting system. Lessons cover time-aware splitting and workflows, not a full specialized forecasting course.
- The PDF lists image feature extraction and external export/interoperability concepts as specialist topics. Scikit-learn is not a deep-neural-network framework; those integration boundaries remain explicit.
- Model-persistence guidance emphasizes that untrusted pickle/joblib artifacts can execute code during load and that cross-version loading is not a supported guarantee. The course says to load trusted artifacts only and validate compatibility.

## Assessment, execution and product boundaries

- Code examples use `static-validation`: they run locally with Python in the learner's environment. The current CodeLeaf stack was inspected and does not provide a secure general-purpose Python runner. Do not run arbitrary learner code in the FastAPI process or production web container.
- The server-side grader supports only the existing `choice`, `exact_text`, and `contains_all` modes. Practical coding exercises use a basic keyword submission gate and require human review; the grader does not execute submitted code. Do not publish them as fully automated code assessments.
- Knowledge-check answer keys and exercise/project reference solutions are kept in repository-only content files. Review API response filtering before publication; the existing project endpoint strips grader and solution content from learner-facing exercise lists.
- Fixed base XP and plan boosts remain controlled by CodeLeaf backend logic. No course-authored XP override is present. No application source, database migration, frontend, deployment file, or dependency manifest is changed by this patch.

## Verification record

The package is generated for the existing directory-based importer. The validation command is filesystem-only. The importer dry run should be run from `backend/`; use `--apply` only after inspecting the report and configuring the intended database. Do not pass `--publish` until human review has approved content and assessment behavior.
