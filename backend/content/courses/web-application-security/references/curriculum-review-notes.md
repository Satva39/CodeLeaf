# Curriculum review notes — Web Application Security

**Status:** Draft; all course content remains unpublished pending subject-matter and local test review.
**Source PDF:** `Web Security.pdf` (49 pages), visually checked as page renders and text-extracted across all pages on 2026-10-20.

## Coverage preserved

- Preserved all **26 modules** and all **193 main lesson slots** in Section B.
- Preserved the numbered lesson subtopics extracted from Section B in `source_subtopics` and `subtopics` on each lesson.
- Preserved the 21 practical exercises from Section C. Added nine clearly draft/extension practice tasks to improve coverage of API policy, token validation, SSRF boundaries, supply-chain review, webhook idempotency, privacy, incident response, GraphQL, and AI tool boundaries.
- Preserved all nine projects plus the secure multi-vendor e-commerce capstone from Section D.
- Preserved specialization areas from Section E, the six-stage learning progression from Section F, and the quality/publication distinctions in Section G.
- Generated original SVG module overviews and lesson diagrams. The PDF itself is primarily text/structured curriculum pages; embedded visual elements were inspected in the rendered pages and were not copied into CodeLeaf.

## Documented correction and editorial decisions

1. **Lesson 99 title:** the PDF initially lists “Unsafe URL Fetching and Redirect Chains”, but its publication notes explicitly recommend renaming topic 99 to **“DNS Resolution and Destination Validation for Server-Side Fetches”** to focus on SSRF-related DNS and network boundaries, leaving general redirect validation in topic 82. This patch applies that source-authored correction and records the original title in each affected lesson's `source_syllabus_title` plus a lesson note.
2. **OWASP reference editions:** OWASP Top 10:2025 and OWASP API Security Top 10:2023 are separate awareness documents. The lesson/reference metadata labels them explicitly. The Top 10 is not presented as a complete verification standard.
3. **WSTG release status:** use the released v4.2 page as the stable baseline and label the `latest` documentation as development content that may change. Do not treat draft/latest text as a finalized normative release.
4. **ASVS:** references point to OWASP's current ASVS project, whose current stable release is 5.0.0 according to its official page. Lessons should map to applicable requirement identifiers during detailed SME review rather than reproducing the standard.
5. **Security safety:** labs are written for local/owned environments, synthetic data, or explicit written authorization. Examples emphasize defensive controls and verification rather than exploit payloads or instructions against real targets.
6. **Execution mode:** CodeLeaf's existing playground previews browser HTML/CSS/JavaScript only. Other examples are labeled static-validation or human-review; this patch does not claim that learner code executes in a secure server runner.
7. **Exercises:** the existing importer supports only `choice`, `exact_text`, and `contains_all` grading modes. The added practical tasks use a declared static evidence-term check as a draft aid and explicitly require human review; term matching is not proof that a security fix works.
8. **Publication status:** every course, module, lesson, exercise, question set, project, solution, and assessment is `draft`. Do not publish until content, references, grader behavior, and tests are reviewed.

## Technical assumptions and review needs

- Checked references on 2026-10-20; web-platform behavior and standards evolve, so recheck before publication.
- Course-level estimate: about 100–120 hours including lessons, exercises, projects, testing, and capstone documentation; this is an estimate, not a guaranteed learner duration.
- All test accounts and example identifiers are synthetic. Any production-specific thresholds, retention periods, or jurisdiction-dependent privacy decisions require local governance approval.
- Project briefs do not include a production-ready application or secure multi-language runner. Students implement projects locally/within their own authorized environment; do not execute untrusted learner code inside the FastAPI process.
