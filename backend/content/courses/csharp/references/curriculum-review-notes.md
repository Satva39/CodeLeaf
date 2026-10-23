# C# curriculum review notes

**Source of truth:** `C#(1).pdf`, 50 pages, inspected as rendered page contact sheets and extracted text on 2026-10-11. Sections A through G were reviewed. The topic titles, subtopics, exercise objectives, eight staged projects, capstone, roadmap, optional tracks, and quality-check topics were retained in `syllabus-map.json`, modules, lessons, assessments, and project files.

## Source-derived scope

- Section B: 25 modules and 195 numbered lessons, each retaining its original source syllabus number and all enumerated subtopics.
- Section C: 30 practical exercises, linked to a relevant anchor lesson.
- Section D: 8 staged projects plus the separately described Modular Business Management Platform capstone (9 project artifacts total).
- Section E: optional application-development tracks, specialized language topics, runtime/performance topics, and legacy/migration topics are recorded as separate tracks rather than mandatory beginner prerequisites.
- Section F: the course metadata and module prerequisites follow the seven-stage learning path in the PDF.
- Section G: the existing assessment plan maps to language fundamentals, type-system/OOP, modern language features, practical development, advanced topics, and project practice.

## Technical checks and clarifications

1. The PDF baseline is C# 14 and .NET 10. Microsoft's C# 14, language versioning, and .NET 10 documentation were checked on 2026-10-11. C# 14 examples are labeled where material; examples are not claimed to compile against older targets.
2. Use the target framework to select the supported default language version. Avoid setting `LangVersion` to `latest` in a reproducible build, because it can vary by compiler installation.
3. The PDF's optional tracks are not folded into core prerequisites. ASP.NET Core, desktop, .NET MAUI, Unity, ML.NET, EF Core, and Roslyn topics require their own framework/runtime dependencies and are best pursued after the related core concepts.
4. C# snippets use `static-validation` because CodeLeaf currently has no C# execution sandbox; the lesson page displays a reference output rather than executing learner code. Framework-specific, database-provider, test-framework, unsafe, and source-generator examples require an appropriately configured local project.
5. The course status remains `draft`. Knowledge-check and project solution files are repository-side content, with API contracts intended to keep solution/answer-key fields from public lesson and project responses. Do not publish before content review, local compilation, assessment review, and project acceptance tests.

## Review notes / exclusions

- No core PDF topic was intentionally excluded. Advanced and specialized items from Section E are held in `references/specialist-tracks.json`, as the PDF recommends.
- Estimated workload (140 hours) is a CodeLeaf planning estimate, not a number stated by the PDF; it includes lessons, practice, guided projects, testing, and review.
- Exercise grader configs currently use the existing repository's `contains_all` token-check capability. That capability is not a compiler or runtime and is explicitly identified as a smoke check, not proof of code correctness. A separately isolated C# runner would be needed for actual server-side code execution.
- Project starter files are scaffolds, not complete finished applications. The protected project reference files are architecture/solution outlines and should be expanded into compiled reference implementations before a project is published.
