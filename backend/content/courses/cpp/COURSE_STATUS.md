# C++ course status

- Status: **draft — review required**
- Source PDF: `C++.pdf` (65 pages)
- PDF curriculum coverage: 21 modules, 239 core numbered lessons, all captured subtopics
- Practice: 45 Section C coding exercise briefs (15 beginner, 15 intermediate, 15 advanced), each with a separate protected reference-solution JSON file
- Projects: 13 project briefs (12 staged projects plus the capstone), each with a C++20 starter source and README under `projects/starters/`, plus separate repository-only reference design notes
- Knowledge checks: 239 question sets × 3 questions = 717 questions, each in a separate file; answer keys are filtered by the existing backend API
- Final assessment: one exam blueprint with a separate question-file index
- Visuals: 21 module overview SVGs + 239 distinct lesson SVGs = 260 assets; see `ASSET-CHECKLIST.md`
- Runtime baseline: C++20 lesson examples and 13 project starter programs compile-checked with GCC 14.2; C++11/14/17 foundations retained; C++23 features version-labelled; C++26 status/availability clearly qualified
- Execution: CodeLeaf lesson page shows example output but does not run C++ learner code. The existing exercise grader supports only basic static graders, so the 45 coding exercises **must remain draft until proper isolated execution or human review is available**. Protected reference solutions were syntax/type-checked with GCC 14.2: 44 passed, and one JSON example was skipped because `nlohmann/json.hpp` is an external, non-bundled dependency.
- Integration: course/lesson content follows the existing importer; project briefs and starter downloads use the existing course-project API/page with a safe explicit-file allowlist. No schema migration or hosting/deployment change is included.
- Final exam/certificate: the exam blueprint is planning metadata only and remains draft; this patch does not add a C++ exam submission/verification or certificate issuance flow. Treat C++ certification as pending until the backend verifies a passing course-specific assessment.

## Authoritative next steps

1. Run `python scripts/validate_course_content.py --course-slug cpp` from `backend/`.
2. Run `python scripts/validate_cpp_course_examples.py --jobs 8` from `backend/` with a C++20-capable `g++` or `clang++` installed. This also checks all project starter paths and compiles their `main.cpp` files.
3. Run `python scripts/validate_cpp_exercise_solutions.py --jobs 6` to syntax-check protected reference solutions; supply `nlohmann/json.hpp` separately before optionally using `--check-external`.
4. Run `python scripts/test_cpp_project_starter_api.py` to smoke-test the project/starter API against isolated in-memory SQLite.
5. Run `python scripts/test_course_api_contract.py` and `python scripts/test_knowledge_check_api.py` for the existing API/security/XP/streak regressions.
6. Run `python scripts/import_course_files.py --course-slug cpp` as a dry run; no database write occurs without `--apply`.
7. After reviewer sign-off, consider `--apply` to import draft records into a development database. Do not use `--publish` before all relevant content statuses and the exercise grading path have been approved.
