# Learning roadmap and prerequisite map

All modules and lessons are draft. The ten phases below organize the complete 168-topic syllabus into a practical progression; specialist topics can be revisited when a project requires them.

## Ten learning phases

### Phase 1 — Orientation and first documents
Learn serialization, format purpose, history, tooling, and first files.

**Modules:** Module 1: Introduction to JSON and YAML (lessons 1–8)

### Phase 2 — JSON grammar and values
Practice objects, arrays, primitive values, strict syntax, strings, Unicode, number rules, null, and errors.

**Modules:** Module 2: JSON Fundamentals (lessons 9–17), Module 3: JSON Strings, Numbers, and Data Types (lessons 18–27)

### Phase 3 — JSON modelling and processing
Design stable structures, parse/serialize files, inspect values, query documents, patch records, and reason about streaming.

**Modules:** Module 4: JSON Data Modeling and Design (lessons 28–36), Module 5: JSON Files, Command-Line Tools, and Processing (lessons 37–46)

### Phase 4 — Schema contracts and APIs
Define JSON Schema constraints and apply consistent payloads in frontend, backend, databases, events, logs, OpenAPI, and versioned APIs.

**Modules:** Module 6: JSON Schema and Validation (lessons 47–58), Module 7: JSON in Web Development and APIs (lessons 59–69)

### Phase 5 — YAML foundations and scalar types
Learn indentation, mappings/sequences, scalar styles, block strings, comments, document markers, and ambiguous values.

**Modules:** Module 8: Introduction to YAML Syntax (lessons 70–78), Module 9: YAML Values, Typing, and Scalar Semantics (lessons 79–90)

### Phase 6 — Advanced YAML and parser ecosystems
Study nested structures, anchors/aliases, tags, multiple documents, directives, and safe parser/library usage.

**Modules:** Module 10: Advanced YAML Structures (lessons 91–103), Module 11: YAML Parsers, Editors, and Language Ecosystems (lessons 104–112)

### Phase 7 — Interoperability and conversion
Compare formats, convert in both directions, test round trips, detect duplicate keys, and document loss of comments/types/presentation.

**Modules:** Module 12: JSON and YAML Comparison and Interoperability (lessons 113–123)

### Phase 8 — Configuration, integration, and security
Apply files to API descriptions, CI/CD, infrastructure, applications, deployment, and secure input handling.

**Modules:** Module 13: Real-World Configuration and Specification Integration (lessons 124–133), Module 14: Security, Reliability, and Data Integrity (lessons 134–142)

### Phase 9 — Quality and production practice
Build test fixtures, contract tests, reviewed diffs, CI checks, documented data contracts, schema migrations, performance notes, and observability.

**Modules:** Module 15: Testing, Quality, Version Control, and Production Practice (lessons 143–153)

### Phase 10 — Advanced patterns and capstone
Apply reusable workflows, streaming patterns, canonicalization cautions, portability tests, and a final end-to-end management pipeline.

**Modules:** Module 16: Advanced Patterns, Specializations, and Capstone Preparation (lessons 154–168)

## Dependency map

- Start with Module 1; no programming experience is required.
- Module 2 follows Module 1 and supports Module 3; Module 4 applies the data model to design decisions, and Module 5 applies it to file/tool processing.
- Module 6 builds on JSON syntax and modelling; Module 7 applies JSON to HTTP/API contracts and application boundaries.
- Modules 8–11 introduce YAML syntax, scalar semantics, advanced structures, and parser ecosystems in sequence.
- Module 12 connects the JSON and YAML tracks. It benefits from Modules 2–11 and supports later integration and portability work.
- Modules 13–15 apply the formats to configuration and production work; Module 14 should be considered alongside all input-processing lessons, not only after them.
- Module 16 is the advanced/specialization track and capstone preparation. Some advanced standards, canonicalization, and parser features are optional until a real application requires them.

## Core, advanced, and specialization labels

- **Core:** Modules 1–15 are the complete foundational and professional-practice pathway. Module-level difficulty moves from beginner to advanced.
- **Advanced / specialist:** Module 16 (lessons 154–168) focuses on advanced patterns, streaming/canonicalization cautions, reusable workflows, assessment, and capstone planning.
- All lessons remain draft; “core” or “advanced” describes learning scope, not publication status.

## Suggested workload

Estimated workload: 50 hours across 168 short lessons, 32 practical exercises, 10 projects plus capstone, revision, and final assessment. This is a planning estimate; actual completion time depends on the parser/tool practice and project depth.
