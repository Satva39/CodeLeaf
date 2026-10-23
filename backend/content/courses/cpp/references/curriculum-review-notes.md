# C++ curriculum review notes

**Source:** `C++.pdf`, 65 pages; reviewed 2026-10-11.  
**Course slug:** `cpp`  
**Disposition:** 21 modules and all 239 numbered lessons represented in order; 45 Section C exercises and 13 Section D project briefs represented as separate files. All generated material remains draft pending human technical review.

## Source coverage reviewed

- Section A: overview, audience, prerequisites, learning outcomes, and standard policy.
- Section B: all 21 modules, lessons 1–239, and each listed subtopic.
- Section C: beginner, intermediate, and advanced practical-exercise banks (15 each).
- Section D: 12 staged projects and the modular inventory/order capstone.
- Section E: specialization guidance and additional professional topics.
- Section F: learning path and prerequisite/dependency recommendations.
- Section G: coverage checklist, quality criteria and lesson-authoring template.

## Corrections and clarifications

1. **“What Does C++ Stand For?”** is preserved as a lesson subtopic because it appears in the PDF, but the course corrects the premise in its explanation: C++ is not an acronym with an official expanded phrase. The name alludes to applying the C increment operator to C.
2. **Published standard baseline.** ISO lists ISO/IEC 14882:2024 as the published C++ standard (Edition 7, published October 2024). The course example baseline is C++20 for practical portability, with C++11/14/17 foundations retained and C++23 features version-labelled. This is a teaching baseline, not a claim that C++20 is the newest published standard.
3. **C++26.** The next ISO/IEC DIS 14882 revision remained under development as of 2026-10-11. C++26 topics are treated as status-aware exploratory material. They must not be described as universally available; check the actual feature support of the compiler and standard library.
4. **Support tables.** Compiler acceptance is not uniform across front end, standard library and platform. References direct maintainers to official GCC/MSVC/Clang documentation and the feature-by-feature compiler-support matrix.
5. **Unsafe/legacy practices.** Manual `new`/`delete`, C-style casts, unchecked indexing, obsolete compiler-specific headers and non-standard console functions are presented as topics to understand or compatibility concerns, not default recommendations for new code.
6. **Conceptual examples for specialist areas.** The lesson examples on GUI, networking, database access, serialization, build systems and module interfaces demonstrate portable design ideas unless a concrete third-party/platform dependency is stated. They are not full production integrations.

## Content status and limitations

- All course, module, lesson, exercise, solution, project and knowledge-check files are marked `draft`.
- Lesson examples are C++20-compatible standalone programs except the explicitly commented module-interface fragment, which is still wrapped in a compilable illustrative host program. This does not prove semantic correctness; compile and review the source, and run lesson examples locally.
- The existing CodeLeaf exercise grader supports only `choice`, `exact_text`, and `contains_all`. The 45 coding exercises use a required-token smoke check and state that the check is not behavioral proof. **Do not publish those exercises as automatically verified coding tasks** until a separate isolated C++ runner or reviewed manual-grading workflow exists.
- Knowledge-check answer keys remain repository-side and the existing backend API returns prompts/options without answer keys until grading.
- No database migrations or deployment changes are required by the content patch. Do not import into a production database until the course review and isolated-runner decision are complete.

## Review items before publishing

1. Run the content validator and the sample compiler check on the target development machine.
2. Have a qualified C++ reviewer check standards claims, examples and all project rubrics.
3. Validate lesson rendering in CodeLeaf with draft preview enabled; confirm SVG alt text and the asset endpoint work for `cpp`.
4. Replace smoke-only coding graders with isolated C++ execution or human-reviewed submissions before enabling exercise rewards.
5. Publish only after each intended course/module/lesson/exercise/question status is approved.
