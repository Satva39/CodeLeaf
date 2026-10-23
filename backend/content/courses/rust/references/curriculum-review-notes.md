# Rust curriculum review notes

- Source PDF: `Rust.pdf` (21 pages), all pages text-extracted. Sections A–G were reviewed, including the complete 27-module syllabus, decimal subtopics, exercises, project list, learning path, specialization table, and references. The PDF includes some small screenshots/illustrations around its overview and project section; this patch creates original SVG teaching diagrams rather than copying those images.
- Coverage preserved: 27 modules, numbered lessons 1–322, decimal subtopics attached to their parent lesson, 30 practical exercises (10 beginner, 10 intermediate, 10 advanced), and 9 projects including the production inventory capstone.
- Version note: use edition 2024 and a maintained stable toolchain. The official Rust Book consulted during this run documents Rust 1.97.0 or later with edition 2024; the official release blog published Rust 1.99.1 on 2026-10-15. The course records 1.99.1 as the checked baseline for this run, not as an evergreen hard pin. Verify the latest supported version before publication. The 180-hour estimate is an author planning estimate; the source PDF does not specify a duration.
- Scope correction/clarification: Modules 1–20 remain the main learning journey but Module 20 (unsafe Rust/FFI) is explicitly marked advanced rather than required for every learner. Modules 21–27 are selectable professional/specialization tracks as recommended in PDF Section E and its final recommendation.
- Ecosystem correction/clarification: HTTP clients, database drivers, TLS, async runtimes, procedural-macro helpers, embedded HALs, and Rust/JavaScript bindings are ecosystem integrations, not Rust language features. Each lesson marks library-specific behavior as requiring versioned upstream documentation rather than claiming it is provided by `std`. For WebAssembly concepts, current generic host/browser guidance uses MDN Web Docs; the previously common Rust and WebAssembly Book landing page indicates that the book is no longer maintained, so it is not treated as the current authority for tool selection. The embedded guide is a specialist reference whose sample target/API versions must be checked against each chosen board.
- Safe/unstable classification: examples do not present nightly-only features as stable. Low-level lessons require explicit safety invariants and code review. `no_std`, WebAssembly, and FFI examples are static illustrations and require target-specific verification.
- Assessment status: all content is `draft`. Knowledge-check answer keys and exercise/project reference solution files remain in repository-side JSON, not in learner lesson content. The current backend has no secure arbitrary Rust code runner; coding tasks therefore use static-validation metadata and require local Cargo tests or human review.
- No existing course with slug `rust` was present in the source ZIP, so this patch introduces a new course without changing stable identifiers in other courses.
- No database schema migration or deployment configuration change was needed: the current importer supports file-based modules/lessons/exercises, the API loads knowledge checks/assets/projects from the course directory, and catalog visibility is controlled by the existing import/publication settings.

## Official references checked

- Rust Book: https://doc.rust-lang.org/stable/book/
- Rust Reference: https://doc.rust-lang.org/reference/
- Cargo Book: https://doc.rust-lang.org/cargo/
- Rust Edition Guide: https://doc.rust-lang.org/edition-guide/
- Rustdoc Book: https://doc.rust-lang.org/rustdoc/
- Clippy: https://doc.rust-lang.org/clippy/
- Rust 1.99.1 release announcement (2026-10-15): https://blog.rust-lang.org/2026/10/15/Rust-1.99.1/
