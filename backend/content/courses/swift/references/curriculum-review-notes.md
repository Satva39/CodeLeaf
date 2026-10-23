# Swift curriculum review notes

**Source syllabus:** `Swift.pdf`, 51 pages; reference version Swift 6.4.
**Review date:** 2026-10-17.
**Status:** Draft. The content is not approved for publication.

## Coverage preserved

- All 22 numbered modules and all 261 lesson titles (numbered 1–261) were carried into individual files.
- The indented subtopics from each lesson were retained in that lesson's `syllabus_subtopics` field and in the module overview diagram.
- The PDF's 46 practical exercises are included as additional challenge files, alongside one linked practice activity per lesson.
- All 11 projects in Section D plus the StudyFlow capstone are represented as separate project JSON files.
- The learning-path, specialist track and final exam blueprint sections were preserved in course metadata and the assessment blueprint.

## Version facts verified

- The official Swift.org post states that Swift 6.4 was released on **2026-09-15**: https://www.swift.org/blog/swift-6.4-released/
- The official Swift language documentation currently presents the Swift 6.4 language reference: https://docs.swift.org/swift-book/documentation/the-swift-programming-language/
- Swift Testing is documented alongside XCTest; official Swift documentation describes Swift Testing as recommended for new tests while existing XCTest suites remain supported and can coexist. See https://www.swift.org/documentation/core-libraries/
- SwiftUI APIs and Apple-platform requirements are referenced to Apple Developer Documentation: https://developer.apple.com/documentation/swiftui

## Scope and caution notes

1. **Specialist/platform material stays optional.** Server-side Swift, Swift for WebAssembly, embedded targets, Android interop, C/C++ interoperability, and recent ownership/collection APIs depend on the precise toolchain, target and package/API support. The course flags these for target-specific verification rather than claiming universal availability.
2. **SwiftUI is not a cross-platform command-line framework.** The SwiftUI code blocks are explanatory and require a compatible Apple SDK. Command-line examples can be run locally with a compatible Swift toolchain.
3. **No Swift sandbox was added.** CodeLeaf's existing browser preview does not execute Swift. Code examples use `static-validation` mode and must be compiled/tested locally or through a separate isolated runner. Do not treat a shown expected output or a source-string exercise grader as execution proof.
4. **Assessment/exercise answers are protected repository files.** Do not expose question `answer_key` fields or project/exercise reference solutions through learner-facing routes. Existing APIs already filter lesson knowledge-check references and exercise solution fields; use the repository-only visibility flags and review endpoint serializers before enabling publication.
5. **Generated explanations need domain review.** The file structure, syllabus mapping and asset references are validated mechanically, but machine generation cannot replace a Swift expert compiling all 261 examples and checking each lesson’s completeness.

## Source-derived vs added material

- **Source-derived:** topic/module ordering, topic labels and subtopics, exercise challenge names, project names/objectives/features, specialization suggestions and the Swift 6.4 baseline from the PDF.
- **Official-doc verification:** release date, language docs, Swift Testing/XCTest positioning, and Apple SwiftUI / Swift server references linked from each lesson.
- **New CodeLeaf-authored material:** concise explanations, minimal examples, acceptance criteria, protected knowledge checks, SVG teaching diagrams, project starter files and the proposed assessment blueprint.

## Items to review before publication

- Compile command-line lesson examples using Swift 6.4 on the intended hosts; test Apple-only snippets in Xcode and package-based snippets in a Swift package.
- Review all question keys, exercise graders, project rubrics, translation/accessibility details and specialist-feature support.
- Only mark the course, modules, lessons, exercises, question files and projects as `published` after review. Then import with the reviewed migration/database and publication options.
