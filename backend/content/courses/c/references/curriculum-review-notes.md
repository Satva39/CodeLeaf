# C curriculum source review and technical notes

## Source inspection

- Reviewed all 28 pages of `C.pdf`, including its text-heavy module outlines, tables/illustrations, practical exercises, projects, advanced-specialization section, learning path and quality checklist. The curriculum outline is on PDF pages 2–17; the exercises and projects appear in the later pages. Original diagrams in this package replace source-page artwork.
- Section B supplies 38 modules and 445 consecutively numbered top-level topics; subtopics such as 1.1 and 44.1 remain attached to their parent lesson. All 445 numbered topics have individual draft lesson JSON files.
- Section C contributes 42 practice prompts. Section D contributes 15 project briefs plus the capstone, represented as 16 individual draft project files.
- Sections E–G are retained as cross-cutting requirements: specialist applications, staged learning progression, and coverage/quality review. They are not fabricated as extra PDF modules because Section B already defines the ordered 38-module curriculum.

## Standards and corrections

1. C23 publication: the PDF states C23 was published as ISO/IEC 9899:2024. This matches the standards/compiler documentation checked for this package. Compiler support remains feature-by-feature; course examples generally use C17 syntax for portability and avoid assuming every implementation supports every C23 feature.
2. Language versus implementation: OS APIs, hardware registers, ABI behavior, compiler flags, `-lm`, threads and build tools are platform/toolchain specific. They are taught as conditional/specialist topics, not portable ISO C guarantees.
3. Concurrency: `volatile` alone does not provide inter-thread synchronization or atomicity. The course does not recommend it as a substitute for atomic or lock-based designs.
4. Serialized data: writing a raw structure object to disk/network is not a portable binary format because padding, representations, endianness and versioning may differ. The course includes byte-level format design instead.
5. `realloc` and input APIs: check returned pointers and size arithmetic, define ownership/failure behavior, and do not rely on non-portable edge-case assumptions.
6. C does not use the C++ One Definition Rule as a general language model. The PDF topic about one-definition concepts is preserved by teaching translation units, linkage, external definitions, and duplicate/undefined-symbol behavior without importing the C++ ODR wholesale.

## Draft status and execution model

All lessons, exercises, projects, assessments and visuals are draft for human review. The current CodeLeaf lesson UI does not execute C. Examples are marked `static-validation` and must be compiled in a local environment or an explicitly isolated runner. The current importer validates knowledge-check question files but does not create a live exam service. No frontend, API, schema, migration, deployment manifest, package manifest or gamification code needed changing for this content-only patch.

## Review steps before publication

- Review every lesson explanation/code/output and all quiz distractors.
- Compile relevant snippets with the target compiler(s), checking warnings and platform assumptions.
- Test exercise solution code and replace token-only smoke checks with a proper isolated runner if/when the platform supports it.
- Confirm answer-key and project-solution files remain repository-only.
- Only mark records published after technical/editorial review; run importer with `--apply --publish` only in an intended environment after setting all desired statuses to `published`.
