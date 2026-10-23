# Java curriculum review notes

**Review date:** 2026-10-11  
**Source:** `Java.pdf` (69 pages)  
**Status:** Draft; not approved for publication.

## Coverage preserved

- Section B: all 32 modules and lesson numbers 1–336; lesson titles and listed subtopics are copied into separate, ordered JSON lesson files.
- Section C: all 16 beginner, 16 intermediate, and 16 advanced named practice exercises (48 total) are represented as individual exercise files with separate repository-only solution files.
- Section D: nine progressive projects plus the Java Business Operations Platform capstone are represented as 10 individual project briefs with 100-point rubrics and separate protected design notes.
- Section E: all eight optional specialization tracks and their topic lists are kept separate from the mandatory Java SE learning path.
- Sections F and G: the six-stage progression, prerequisite relationships, estimated 150–250 hour core workload, coverage checks, and publication cautions are reflected in the course metadata and review notes.

## Version and technical decisions

1. **Java 25 LTS is the core baseline**, consistent with the PDF. The official Oracle Java SE support roadmap identifies Java 25 as LTS; support terms differ by distribution and must be checked for a real deployment.
2. **Java 27 is not treated as the default learning/runtime baseline.** Oracle's JDK 27 release notes state that JDK 27 GA was published on 15 September 2026 and list primitive types in patterns, `instanceof`, and `switch` as the fifth preview (JEP 532). Lesson 335 is labeled preview-only and includes version-specific instructions.
3. The PDF has two staged entries about pattern matching with `instanceof` (lessons 61 and 126). Both are preserved to avoid omitting numbered syllabus coverage; the first introduces the flow-control use, while the second treats language-feature rules and scope.
4. Java code is **not a browser-executable language** in the current CodeLeaf lesson UI. Examples use `run_mode: server-runner` to denote code requiring a real JDK or a separately isolated runner. No unsafe runner was added to FastAPI. A production runner still needs isolation, process/time/memory limits, filesystem and network controls, and an explicit deployment boundary.
5. The repository's current importer supports only `choice`, `exact_text`, and `contains_all` exercise grading modes. Coding exercises therefore use server-side required-token smoke checks plus task-specific acceptance rubrics; those checks are not represented as semantic proof or full hidden-test infrastructure.
6. The course API can serve published lesson content and local SVG assets through existing generic routes. Since the content model already supports a separate course folder, no Java-specific API route, schema migration, or deployment configuration change is necessary for this patch.

## Visual review

The supplied PDF was rendered across all 69 pages. The main curriculum is text-led; pages 60–61 include project mock-up illustrations, and the overview page includes a designed summary panel. CodeLeaf visuals in this package are newly authored SVG teaching diagrams and do not reuse those screenshots.

## Source references checked

- Learn Java: https://dev.java/learn/
- Java SE 25 API: https://docs.oracle.com/en/java/javase/25/docs/api/index.html
- Java SE 25 specifications: https://docs.oracle.com/en/java/javase/25/docs/specs/index.html
- Oracle Java SE Support Roadmap: https://www.oracle.com/java/technologies/java-se-support-roadmap.html
- JDK 27 Release Notes: https://www.oracle.com/java/technologies/javase/27all-relnotes.html
- Java SE 25 Security Guide: https://docs.oracle.com/en/java/javase/25/security/

