# Ruby curriculum source review

## Source coverage

- Reviewed all 55 PDF pages through extracted text; checked numbered lesson headings and syllabus subtopics across Sections A–G. Visual pages containing embedded material were also inspected: page 1 course overview; pages 28 and 33 reference badges/version-sensitive Ruby Box notes; pages 48–49 project progression; page 52 learning-path cards; and page 55 final recommendations and official references. The project progression, staged roadmap, experimental-topic caveats, and review recommendations are reflected in the course. Source badges and PDF screenshots were not copied into course assets; original accessible SVG teaching diagrams were authored instead.
- The generated lesson map contains all **304** numbered topics across **28** modules and preserves the source sequence and extracted subtopic lists. Section C contributes **28** practical exercises; Section D contributes **12** projects including the capstone.
- The PDF is a curriculum blueprint rather than a complete set of worked lessons. Explanations, examples, checks, starter files, and solution outlines in this patch are original authored content, not claimed to have been present in the PDF.

## Version and technical notes

- The PDF says Ruby 4.0.7 was latest stable as of 2026-10-10. This was re-checked against the official Ruby 4.0.7 release announcement, which dates the release to 2026-09-15. The official news archive also lists Ruby 4.1.0-preview1 on 2026-10-12; it remains a preview and is not the stable course baseline.
- Ruby Box, ZJIT, Ractors, alternative runtimes, RubyVM interfaces, and native extension/FFI behavior are kept as advanced, optional, version/runtime-sensitive topics. Verify current release notes and platform compatibility before publishing those lessons. Examples do not require these experimental topics in the core learning path.
- The PDF calls out YJIT/ZJIT and Ruby Box as specialist/experimental material. They are retained but explicitly not required for beginner progression.
- Rails, Sinatra, Rack, SQL drivers, CLI packaging, and deployment are presented as ecosystem/specialization topics after core Ruby; they are not represented as syntax features built into the language. Framework-specific examples require declared gems and are draft.
- Security lessons stress parameterized queries, validation, secret management, bounded retries/timeouts, safe file operations, and no arbitrary evaluation. Database examples that require sqlite3 identify it as an external gem dependency.

## Publication status and platform limitations

- Course, modules, lessons, exercises, solutions, questions, and projects are **draft**. They are not to be published until their code examples and solution outlines are run/reviewed by a qualified reviewer.
- The existing importer and validator are reused without changing database schema or platform XP logic. Every course-authored file omits XP overrides. Platform XP rules stay server-side.
- Knowledge check answer keys remain in repository-side question files. Existing API code returns prompts/options to learners and grades selections server-side; do not expose those question files via a public static file host.
- Ruby QA run on the available Ruby 3.3.8 runtime: all 304 lesson snippets passed syntax parsing with `ruby -c`; 173 snippets in Modules 1–16 were also executed without runtime exceptions, while one intentional monkey-patch example was skipped. Functional execution was not performed for all later I/O, external-gem, database, network, concurrency, or version-specific examples. The course baseline is Ruby 4.0.7; repeat full example validation on that target runtime. The existing platform has no isolated Ruby runner; do not execute learner code in FastAPI.
- Static token checks for the 28 coding exercises are intentionally described as smoke checks only. They do not execute Ruby and should not be treated as proof of correctness. The tasks remain draft.

## Corrections/exclusions

- No numbered syllabus lesson or Section C/D exercise/project was intentionally omitted.
- The stable baseline wording is date-stamped and distinguishes the October 2026 Ruby 4.1 preview from stable Ruby 4.0.7. Avoid describing preview or experimental features as production-stable.
- Original PDF screenshots and small badges were not copied into the course; original SVG teaching visuals were authored instead to keep the patch self-contained, scalable, and accessibility-labelled.
- Ruby Box is covered conceptually as an optional isolated-definition environment and is not presented as a mandatory or universally available production feature.
