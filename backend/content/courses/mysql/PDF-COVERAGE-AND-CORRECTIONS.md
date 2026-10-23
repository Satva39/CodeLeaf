# MySQL PDF coverage and technical clarifications

## Coverage result

The attached 32-page PDF was text-extracted and visually reviewed as a complete document. Section B contains 37 modules and exactly 435 numbered main topics (numbered continuously 1–435). All topic titles and their recognizable indented subtopics are preserved in the per-lesson `source_syllabus_number`, `source_module_number`, and `subtopics` fields. Sections C–G are represented as the practical exercise bank, 11 projects (including the capstone), assessment blueprint, learning roadmap, and specialist track labels.

## Clarifications made in the authored material

- **Release tracks:** The PDF identifies MySQL 9.7 and MySQL 26.7 as current release lines as of October 2026. The official manual’s release pages were checked on 2026-10-12. Examples distinguish the 9.7 documentation from the calendar-versioned 26.7 documentation and do not imply feature parity without verification.
- **InnoDB defaults:** The PDF explicitly says InnoDB is the default in MySQL 8.4. That fact is retained with a labeled 8.4 source; actual configured defaults and available engines must be inspected for the chosen release/distribution/managed service.
- **`INTERSECT` / `EXCEPT`, JSON validation, `EXPLAIN ANALYZE`, spatial functions, replication/cluster administration, connector APIs, and legacy syntax:** the PDF already says some of these are version-dependent or specialist. Course instructions treat them as version-specific and require checking the selected manual or connector guide. No unverified compatibility claim is presented as universal.
- **Operational topics:** commands for backup, restore, grants, schema change, replication, and failover are designed for a disposable lab or static planning. They are not a claim that production operations were performed.
- **Browser code execution:** the existing CodeLeaf lesson UI can show reference output; it does not execute arbitrary MySQL queries. Every MySQL lesson uses `static-validation`, with a dedicated local MySQL/isolated runner required for real execution. No new unsafe execution service was added.

## Still requiring human review

All course records remain `draft`. The generated JSON and visuals pass structural/path validation, but an independent MySQL engineer should execute and review every database-specific example, review answer quality and exercise grading, test API answer-key protection, and confirm release compatibility before publication.
