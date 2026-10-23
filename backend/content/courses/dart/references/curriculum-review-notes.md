# Dart curriculum review notes

**Status:** Draft; no lessons are marked published. Review date: 2026-10-19.

## Source coverage

The supplied `Dart(1).pdf` was inspected across all 27 pages, including the curriculum list, exercise/project tables, TaskFlow capstone, learning-path diagram/text, specialist tracks, and coverage matrix. All 28 source modules and consecutively numbered lessons 1–297 are represented. The source's 26 practical exercises and 14 projects (13 staged projects plus TaskFlow capstone) are represented in separate files. The PDF's page-22 TaskFlow screenshot is treated as context only; no third-party screenshot or brand artwork was copied. Original SVG diagrams were created for every module and lesson.

## Explicit scope decisions and corrections

- **Flutter boundary preserved:** Dart language integration in Flutter projects is included; a complete Flutter UI course (widgets, rendering, navigation, and state-management frameworks) is out of scope, matching the PDF overview.
- **Version-sensitive examples:** Official docs consulted on 2026-10-19 included a Dart 3.13.3-era documentation snapshot. `course.json` therefore describes a Dart 3.13.x-era learning baseline as a checked snapshot, not as an everlasting SDK pin. Re-check the currently stable release and validate all examples before publishing.
- **Modern language features:** Records, patterns, and class modifiers are taught with the Dart 3 language-version boundary noted. Exercise and lesson content should still be checked against the chosen package SDK constraints.
- **Browser interop:** `package:web` / modern JS interop are positioned as the current path to check against official docs; older `dart:html` material should be labeled legacy where encountered. WebAssembly and JavaScript outputs have different compatibility constraints and must not be presented as interchangeable.
- **Compilation commands:** The curriculum distinguishes `dart run`, `dart compile`, and build workflows; exact targets and commands must be verified against the stable SDK selected at publication.
- **Platform differences:** `dart:io`, isolates, and FFI are not universal to all Dart targets. Relevant content carries platform notes and must be tested on intended targets.
- **Third-party packages:** `package:test`, `package:http`, `package:path`, Shelf, serializers, and lint packages are optional technology choices, not silently pinned to unverified versions. Review maintenance, SDK compatibility, license, docs, and security before introduction.
- **Exercise grading:** The schema's `contains_all` grader checks required strings and cannot prove semantics. All coding tasks state that actual behavior needs local tests and/or human review. CodeLeaf's API process is not used to execute learner-provided Dart.
- **Exam/certificate boundary:** The exam blueprint and question bank are draft curriculum assets; this does not assert that a runtime exam workflow or certificate issuance exists. Certificates require a separate backend-verified passing result.
- **Validation limits:** The build environment used to prepare this patch has no Dart executable. JSON/content/SVG and Python/API checks can be run here, but code snippets have not been compiled, formatted, analyzed, or run by the Dart SDK.

## Publication gates

1. Install the intended stable Dart SDK and record `dart --version`.
2. From this content, run `dart format .`, `dart analyze .`, and relevant `dart test` suites in each starter/package that supports execution.
3. Validate web-specific examples in the web toolchain and native FFI examples only on documented supported targets.
4. Review every generated learning check for instructional accuracy and every exercise rubric for meaningful semantic assessment.
5. Import in dry-run mode first, inspect the report, and only publish after review.


## Official documentation cross-check (2026-10-19)

- The official [async/await guide](https://dart.dev/libraries/async/async-await) states that the docs reflect Dart 3.13.3 and was last updated 2026-02-02; this was the dated documentation baseline used here, not a guarantee that a particular SDK is installed.
- [Records](https://dart.dev/language/records) and [class modifiers](https://dart.dev/language/class-modifiers) require language version 3.0 or later for these modern language features.
- The [Pub workspace guide](https://dart.dev/tools/pub/workspaces) documents workspace support beginning with Dart 3.6 and workspace glob patterns requiring Dart 3.11 or later.
- The [package:web migration guide](https://dart.dev/interop/js-interop/package-web) describes `package:web` as the longer-term browser API path replacing deprecated `dart:html`; it explains the Wasm compatibility boundary through `dart:js_interop`.

These version/tooling facts can change. Re-verify the stable SDK release and package versions immediately before publishing.
