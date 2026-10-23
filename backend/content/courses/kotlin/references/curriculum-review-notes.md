# Kotlin curriculum review notes

## Source scope

- Source: `Kotlin.pdf` (43 pages), including Sections A–G and the four specialization paths.
- Parsed syllabus: 26 modules and 271 numbered lessons. The numbered decimal subtopics are retained in each lesson file.
- Exercises retained from Section C: 30. Projects retained from Section D: eight staged projects plus the Study and Learning Planner capstone (nine briefs total).
- Visual review: all 43 pages were rendered and checked in a contact sheet; extracted text was scanned section by section. The PDF is primarily a text syllabus and course-planning document; embedded brand/reference thumbnails do not define the curriculum semantics.

## Verified/version-sensitive facts

- Official Kotlin release history was checked on 2026-10-17 and records Kotlin 2.4.21 as released on 2026-10-08. Version references in this course are snapshots; re-check before publication.
- The official Kotlin language feature page lists context parameters as stable since Kotlin 2.4.0. The context-parameters guide describes explicit context arguments as Experimental, so these are treated as distinct maturity states.
- Official component stability guidance labels Kotlin/Wasm Beta in this snapshot; the relevant lessons advise rechecking maturity and target support.
- Jetpack Compose is described by Android Developers as the recommended modern toolkit for native Android UI. Ktor examples follow the official server and test guides.
- Kotlin serialization format libraries have their own versioning; JSON support is stable in the referenced guide while some other formats are experimental.

## Corrections, qualifications, and exclusions

- No numbered syllabus topics were intentionally excluded or renumbered. Modules 1–22 are treated as the core course; Modules 23–26 remain optional specialization tracks, matching the source recommendation.
- The PDF's claim that Kotlin 2.4.21 was the latest release in the 2.4 line was cross-checked against the official release history on 2026-10-17. This is a time-stamped statement, not a perpetual guarantee.
- Lesson examples that require a JVM, Gradle plugin, coroutines, reflection, serialization, Android, Ktor, or multiplatform toolchain are labelled static references and list their required project type/dependencies. CodeLeaf's browser lesson view does not execute these snippets.
- The exam blueprint and project solution files are draft content. The current CodeLeaf importer stores the normal lesson/exercise records, but protected knowledge-check files and a live exam runner must remain server-side; the blueprint does not claim that online assessment persistence/certificate issuance is ready.
- Existing course import logic awards the platform-defined exercise base XP and does not accept course-authored XP overrides. No gamification, authentication, XP, streak, certificate, or global API code was changed in this patch. Those existing areas require their own regression test run when changing platform behavior.

## Required publishing review

1. Review every code example against the compiler and platform versions selected by the publishing team.
2. Run the repository validator, then run course import in dry-run mode. Apply only after reviewing all content.
3. Review protected answer keys/question files and confirm the serving API never exposes them.
4. Do not publish the course merely to make it visible. Promote only individually reviewed items from `draft` to `published`, then import with the repository's publish workflow.
5. For Kotlin execution, use a separate isolated runner with resource/time limits; never execute learner-submitted code in the FastAPI process or production web container.
