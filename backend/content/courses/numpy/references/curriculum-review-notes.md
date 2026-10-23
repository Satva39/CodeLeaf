# NumPy curriculum review notes

## Review scope and source of truth

- Reviewed the complete 46-page `NumPy(1).pdf` text layer and the page renderings supplied with the document, including the course overview, complete curriculum, exercises, projects, specialist tracks, learning roadmap, prerequisites, and quality-review material.
- Preserved the PDF's numbered learning sequence: **220 topics across 22 modules**. The PDF's topic numbers and supplied subtopic lists are recorded in `references/full-syllabus.json`; module and lesson files link back to the original numbering.
- Captured the PDF's **40 exercises** and **10 projects** in separate files. Added a lesson-level question set for each of the 220 topics (three questions per set) and one final exam blueprint.
- The source PDF is a curriculum blueprint rather than full lesson text. Explanations, runnable snippets, exercises, projects, questions, and diagrams in this course are original teaching material that expands the supplied outline; they are not presented as verbatim material from the PDF.

## Technical clarifications and publishing review items

1. **Version baseline.** The official NumPy news page was checked on 2026-10-13 and listed NumPy 2.5.4 as the latest patch release in the 2.5 line on 2026-10-10. The reference baseline is the stable NumPy 2.5 documentation. The available validation runtime is NumPy 2.3.5, so version-dependent snippets should be checked again in a NumPy 2.5 environment before publication.
2. **Homogeneous arrays and structured records.** Ordinary numeric ndarrays typically use one dtype for their elements. Structured dtypes provide named fields and field-specific dtypes for record-like data. Lessons should not imply that a plain numeric ndarray stores arbitrary Python values without trade-offs.
3. **Modern random APIs.** Teach `np.random.default_rng()` and `Generator` first for new code. `RandomState` is retained for understanding and maintaining legacy code, not as the default for new projects.
4. **Polynomial APIs.** Prefer the `numpy.polynomial` package for new polynomial work. Legacy polynomial APIs belong in compatibility/migration context.
5. **Uninitialized memory.** `np.empty()` allocates uninitialized storage. Every element must be assigned before it is read; observed memory values are not meaningful defaults.
6. **Linear algebra.** For solving a square linear system, demonstrate `np.linalg.solve(A, b)` rather than explicitly computing `inv(A) @ b` as the default approach. Check singularity, conditioning, dimensions, and residuals when relevant.
7. **Floating-point comparisons.** Binary floating-point cannot represent every decimal exactly. Teach `np.isclose`/`np.allclose` with tolerances where approximate equality is the intended question.
8. **NumPy 2.x compatibility.** The course calls out type-promotion and compiled-extension/API compatibility changes introduced in NumPy 2.0. Maintainers should review the official migration guide before upgrading compiled dependencies.
9. **Untrusted files.** NumPy examples that load common numeric data should use safe defaults; for `.npy` inputs from untrusted sources, use `allow_pickle=False` unless object deserialization is explicitly required and trusted.
10. **Specialist scope.** C API, F2PY, Cython/compiled interoperability, strides, and Array API portability are included as advanced/specialist material. They should not block learners who only need the core numerical-computing path.
11. **Execution boundaries.** CodeLeaf's current app does not provide an isolated general-purpose Python execution service. Examples are marked `static-validation` and provide local run instructions; do not imply that the production FastAPI process executes learner code. A separately isolated runner would require explicit timeouts, memory/CPU limits, filesystem and network policy, and deployment isolation.
12. **Gamification.** Course files deliberately contain no per-lesson or per-exercise XP overrides. The existing platform importer owns the exercise's 20 base XP rule; account-plan multipliers and idempotent reward behavior remain server responsibilities.

## Scope accounting

- Excluded PDF topics: **none**. Headings, numbering, and the listed subtopics from all 220 syllabus entries are preserved in the full-syllabus reference and each corresponding lesson.
- Normalizations: markup/spacing artifacts in the extracted PDF, such as `ndarray` spacing, are cleaned in UI titles; API names are formatted as code where appropriate. These editorial changes do not remove a syllabus item.
- The PDF's conceptual syllabus remains the authority for coverage. Technical clarifications above are review notes and should be checked as part of an expert review before marking any content published.

## Official sources checked

See `references/reference-index.json` for the source list and date checked. Important sources include:

- NumPy stable documentation: https://numpy.org/doc/stable/
- NumPy release news: https://numpy.org/news/
- NumPy 2.0 migration guide: https://numpy.org/devdocs/numpy_2_0_migration_guide.html
- Broadcasting: https://numpy.org/doc/stable/user/basics.broadcasting.html
- Random sampling: https://numpy.org/doc/stable/reference/random/index.html
- Linear algebra: https://numpy.org/doc/stable/reference/routines.linalg.html

**Status:** all course items remain `draft` pending human technical, instructional, accessibility, and rendering review.
