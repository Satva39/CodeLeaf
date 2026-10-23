# Solidity curriculum review notes

**Source:** `Solidity.pdf` (24 pages), all pages text-extracted and the embedded page renders visually sampled while reviewing headings, exercise/project tables, roadmap and checklist.
**Status:** Draft — subject-matter and code-example review required before publication.
**Coverage:** 22 modules; 300 numbered lesson topics preserved in source order; 24 practical exercises; 12 regular projects plus one capstone; four specialist tracks; one final-exam blueprint and protected question bank.

## Version correction and current assumptions

- The PDF includes the string `Solidity 0.8.38-…` and references development documentation. The official Solidity release page accessed on 2026-10-20 lists v0.8.37 as the latest stable release at that time, while the latest docs page is labeled `0.8.38-develop`. Course examples therefore target the explicit compiler `0.8.37`; the version distinction is recorded rather than silently treating a development build as stable.
- Compiler versions, compiler bug advisories, EVM targets, transient-storage support, library major versions, and chain support are version-sensitive. Pin the exact compiler/tooling in practice, then re-check official docs and release notes before publishing.
- Foundry and Hardhat commands/features change by major version. The lessons are static content: the current CodeLeaf browser playground previews only HTML/CSS/JavaScript, not Solidity. Run examples in a local Remix VM or a separate local EVM project. No arbitrary Solidity execution is added to the FastAPI service.
- ERC standards and reusable libraries define interoperability surfaces, not a blanket security guarantee. The course recommends reviewed OpenZeppelin components but requires review of configuration, extensions, and authorization.
- Security labs are explicitly local/test-only. No external contracts or networks should be tested without authorization; the escrow/crowdfunding/treasury examples use simulated funds.

## Structure and syllabus mapping

All 300 numbered topics from Section B are kept as one JSON file each, in the same sequence and module grouping. Section C's 24 exercises are represented as separately stored exercise files and protected solution files. Section D's 12 projects plus the community-grants capstone are represented individually with staged milestones and 100-point rubrics. The four specialist tracks, recommended learning stages, tool roles, and version-aware maintenance topics from Section E/F are represented in `references/specialist-tracks.json`, `references/learning-roadmap.json`, and `references/reference-index.json`.

The PDF's Section A outcome list, prerequisites and overview are reflected in `course.json`. Its Section G publication checklist is retained as QA expectations in this file and `COURSE_STATUS.md`.

## Corrections or scoped cautions

1. **Compiler version:** the development documentation marker in the PDF is not assumed to identify the latest stable compiler. `0.8.37` is a dated course target pending a new release check at publication.
2. **Transient storage / new opcodes:** these are taught as conditional specialist topics. Verify compiler support, EVM target and target-chain support before enabling them.
3. **Upgradeability:** proxy examples are conceptual; production designs require storage-layout checks, initializer protections, access-control/governance review, and rollback/emergency planning.
4. **Token implementation:** lessons direct learners to interfaces and reviewed libraries; an abbreviated learning interface is not presented as a complete standard implementation.
5. **Security classification:** OWASP categories may change; the reference index points to the official 2025 edition and asks maintainers to refresh the current source before release.
6. **No exclusions:** no numbered syllabus topic or listed exercise/project was intentionally omitted. Supporting text under topic 7 (blocks/transactions, distributed state/consensus, public vs private blockchains) and the advanced specialist paths is retained.

## Integration decisions

The supplied project already has a directory-based importer, course-tree validator, database upserts, draft/publish gating, server-side protected knowledge-check routes, SVG-asset route, and a dynamic course catalog. No backend route/model/migration or frontend page edit was needed for the new course. Keep status as draft and import using the existing dry-run-first workflow. Course visibility requires a database import; published visibility additionally requires an explicit reviewed publish workflow.
