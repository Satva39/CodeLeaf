# Go curriculum review notes

- Source: `Go.pdf`, 59 pages. All pages were text-extracted and visually reviewed in four contact sheets.
- Section B: 25 modules and 270 main lesson topics mapped into one JSON file per lesson, with source syllabus number and subtopics retained.
- Section C: 35 practical exercises (15 beginner, 10 intermediate, 10 advanced) mapped to relevant lessons.
- Section D: 9 guided projects and one capstone mapped to separate project files with starter scaffolds and protected reference outlines.
- Sections E-F: advanced/specialized topics are marked advanced/elective where appropriate; the seven-stage roadmap follows the supplied learning sequence.
- Section G: status remains `draft` pending human technical/editorial review, Go runtime verification, accessibility review, and publication decision.

## Version-specific checks and distinctions

The PDF identifies Go 1.27.2 (released 2026-10-08) as the baseline current point release on its 2026-10-10 snapshot. The official Go release history confirms that version/date. The Go 1.27 release notes and language specification confirm generic methods are a Go 1.27 feature; interface methods still cannot declare their own type parameters or be implemented by generic methods. The official Go 1.27 release notes also list `encoding/json/v2`, the standard `uuid` package, and an experimental `simd` package.

`simd`, `unsafe`, cgo, assembly, deep reflection, and advanced cryptographic/SIMD topics are not prerequisites for the core learner path and are classified as elective or advanced. The examples require review against the installed toolchain, especially Go 1.27-only syntax; no runtime, deployment, or database operation is claimed to have been executed during package generation.

## Source coverage and implementation decisions

- All 270 main topics are retained as separate draft lesson files. Subtopics from the PDF are saved on each lesson and represented in lesson content.
- The PDF recommends progressive projects: calculator, task manager, text/log analyzer, REST service, inventory backend, concurrent file processor, production backend, distributed job processor, developer toolkit, and the Go Application Platform capstone. All ten are represented as draft starter outlines.
- The actual CodeLeaf course importer already supports `course.json`, module files, per-lesson files, exercise/solution files, knowledge checks, project files, references, and SVG asset validation. The generic course API/catalog uses the slug, so no frontend/backend route or schema change is necessary for content integration.
- All course content, modules, lessons, exercises, solutions, projects, assessment files, and visual asset manifest entries remain `draft`; running the import with `--publish` does not override authored draft status.
- XP, progress, streak, and subscription reward fields are not authored in any course file; platform gamification remains backend-owned.
- Browser iframe preview is not treated as a Go execution runtime. Go examples are `server-runner` or `static-validation`, and learner code execution requires a separate isolated runner.

## Technical corrections / editorial flags

- The PDF's Go 1.27 references are marked version-specific rather than described as portable to older toolchains. Generic-method examples explicitly require Go 1.27+.
- Go 1.27 SIMD APIs are described as experimental and unstable, not as a recommended production default.
- SQL placeholder syntax is driver-specific; examples warn against concatenating untrusted values and direct learners to parameterized arguments.
- Fuzzing and the race detector are described as complementary checks: fuzzing explores generated inputs, while `-race` only detects races along exercised runtime paths.
- The course references official Go documentation and package references checked on 2026-10-17; release-specific material should be rechecked before publishing.
