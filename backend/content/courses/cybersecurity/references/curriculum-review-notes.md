# Cybersecurity curriculum review notes

## Source inspected
- `Cybersecurity.pdf`: all 53 rendered pages were inspected as contact sheets and the complete text layer was extracted. Pages 1-2 contain the overview/scope; Section B describes 25 modules and 200 main topics; Section C lists 24 practical exercises; Section D describes 10 projects; Sections E-G give specialist tracks, roadmap/prerequisites, and quality/source guidance. The module-overview diagrams and project cards shown on rendered pages were visually reviewed.
- `Code_Leaf` ZIP: project README, content README, importer, validator, model/API contracts, lesson rendering path, knowledge-check endpoint, exercise grading logic, sample AI/PostgreSQL course layouts, and catalog integration were inspected.

## Preservation and additions
- All 25 module names, all 200 main topic titles, and their parsed decimal-numbered subtopics are retained in the source syllabus index and individual lesson metadata. The 24 Section C practice briefs are mapped to related lesson exercises; the 10 Section D projects are created as separate project files with protected reference-solution files.
- A per-lesson practice exercise and three protected knowledge-check questions are authored for each topic to ensure practice before later concepts depend on it. This extends the 24 PDF exercise briefs into a 200-exercise practice layer; the 24 source briefs remain explicitly represented rather than being discarded.
- 25 original SVG module overview diagrams are included. Lesson code examples use synthetic values and safe local computations. The existing CodeLeaf runtime does not safely execute arbitrary learner code in the API process, so lesson code is labeled `static-validation`; no production runner was introduced.
- All content remains `draft`; no course data was imported into a database and nothing was published.

## Corrections, version notes, and boundaries
- The PDF's broad course outline is preserved. The linear attack lifecycle is taught as an analytical model only; MITRE ATT&CK is a knowledge base of tactics and techniques and should not be treated as a deterministic sequence followed by every incident.
- The PDF recommends OWASP Top 10:2025. The official OWASP project page confirms that 2025 is the current released Top 10 edition as checked on 2026-10-18. The API Security Top 10 reference used here is the 2023 edition, and should be replaced if OWASP publishes a newer one.
- Incident-response content uses NIST SP 800-61 Rev. 3 (final, April 2025), which supersedes Rev. 2. TLS lesson references use RFC 9846 as the current TLS 1.3 specification shown by the RFC Editor in July 2026, rather than treating RFC 8446 as current.
- The course refers to CVSS v4.0 as vulnerability-severity context, not as the sole risk-prioritization mechanism.
- India-specific materials point to official CERT-In and MeitY source pages. This curriculum is educational, not legal advice; scope and commencement dates must be reviewed against the current official text and qualified counsel before real-world compliance decisions.
- No topics were intentionally excluded from the PDF. Explanatory detail, code examples, assessment questions, and suggested thresholds are authored additions and are draft pending professional review.

## QA limits
- JSON/schema/path/ID/asset checks are automated locally. The course importer dry-run is run in the isolated extracted source tree.
- No external labs, malware samples, live targets, production database, real cloud account, secure code runner, or deployment were tested. Project reference solutions are repository-only and must stay out of learner-facing endpoints.
