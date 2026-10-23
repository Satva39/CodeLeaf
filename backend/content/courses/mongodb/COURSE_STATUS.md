# MongoDB course status and source coverage

**Status: DRAFT — not approved for publication.**

Built from the supplied `MongoDB(1).pdf` (55 pages). The extracted syllabus headings and the rendered page overview were reviewed; all numbered primary topics 1–261 are retained in order as separate lesson files across all 25 modules. The PDF's deeper numbered subtopics are retained in each lesson's `subtopics` list. No numbered topic is intentionally omitted.

## Source module coverage

| Module | Source title | Topic range | Topic count | Track |
|---:|---|---:|---:|---|
| 1 | Introduction to MongoDB | 1–9 | 9 | core |
| 2 | MongoDB Fundamentals and Architecture | 10–18 | 9 | core |
| 3 | Installation, Connection and Developer Tools | 19–28 | 10 | core |
| 4 | BSON Types and Document Data | 29–38 | 10 | core |
| 5 | CRUD Operations | 39–50 | 12 | core |
| 6 | MongoDB Query Language (MQL) | 51–64 | 14 | core |
| 7 | Updates, Deletes and Bulk Operations | 65–74 | 10 | core |
| 8 | MongoDB Aggregation Pipeline | 75–89 | 15 | core |
| 9 | Advanced Aggregation and Analytics | 90–98 | 9 | advanced |
| 10 | MongoDB Schema Design and Data Modeling | 99–110 | 12 | core |
| 11 | MongoDB Indexes | 111–122 | 12 | core |
| 12 | Schema Validation and Data Integrity | 123–128 | 6 | core |
| 13 | Relationships, Atomicity and Transactions | 129–137 | 9 | advanced |
| 14 | MongoDB Application Development | 138–154 | 17 | core |
| 15 | Specialized Collections and Database Features | 155–164 | 10 | optional-specialist |
| 16 | MongoDB Search and Vector Search — Specialized | 165–176 | 12 | optional-specialist |
| 17 | Change Streams and Event-Driven Processing | 177–184 | 8 | advanced |
| 18 | Replication and High Availability | 185–193 | 9 | advanced |
| 19 | Sharding and Horizontal Scaling | 194–202 | 9 | advanced |
| 20 | MongoDB Security | 203–213 | 11 | core-professional |
| 21 | Administration, Backup and Recovery | 214–223 | 10 | core-professional |
| 22 | Performance Optimization | 224–232 | 9 | advanced |
| 23 | Data Import, Migration and Integration | 233–241 | 9 | core-professional |
| 24 | Testing, Reliability and Quality Assurance | 242–251 | 10 | core-professional |
| 25 | Atlas, Production Deployment and Professional Practices | 252–261 | 10 | core-professional |

## Counts generated

- 25 module JSON files and 261 individual lesson JSON files.
- 281 linked exercise JSON files: one practice exercise for every lesson plus 20 practical labs mapped from Section C of the PDF. Each exercise has a separate repository-only solution JSON file.
- 261 protected lesson knowledge-check files with 3 questions each (783 questions), plus 1 protected final assessment with 20 questions and 1 exam blueprint. Total questions: 803.
- 10 project files mapped to the Project Roadmap in Section D, each with a starter file and protected reference outline.
- 286 original SVG teaching visuals: 25 module overview diagrams and 261 lesson diagrams.
- 1 synthetic CSV dataset for import/migration and analytics practice.

## Corrections, interpretation and scope notes

- **No syllabus topic was excluded.** All 261 numbered topic headings and their parsed subtopics remain linked in order.
- The PDF explicitly identifies `mongosh` as the modern shell and the older `mongo` shell as legacy. The course uses `mongosh` by default and does not teach the retired/legacy shell as the normal setup path.
- The PDF correctly separates core document database concepts from Atlas or deployment-specific features. Atlas Search, Vector Search, Atlas monitoring/automation, some encryption/auditing capabilities and specialist operations remain optional or deployment-dependent rather than requirements for every self-managed deployment.
- Transaction, replication and sharding lessons distinguish single-document atomicity from multi-document transactions, and require version/topology-specific verification instead of implying that all deployments support all features.
- The PDF is a syllabus roadmap, not a complete set of lessons. The examples and explanations here are original instructional material; they are not copied from a learning platform. Examples are draft/reference code and need execution against the selected MongoDB server and official driver before publication.
- Official documentation links were checked on 2026-10-15. Because MongoDB server, `mongosh`, drivers and managed-service features can change independently, confirm the exact behavior in the documentation matching the target versions at review time.

## Review gates before publication

1. Run `python scripts/validate_course_content.py --course-slug mongodb` and `python scripts/import_course_files.py --course-slug mongodb` from `backend/`.
2. Review all query/driver/admin examples and execute a representative set in a disposable database/replica-set where appropriate. Static validation does not execute MongoDB.
3. Confirm the learner API strips `answer_key`, `solution_file`, protected solutions and grader internals from public responses; run the existing knowledge-check and course API contract tests against a configured local test database.
4. Confirm the course catalog and lesson pages show draft content only to the supported local preview/admin workflow. Use `--publish` only after the content review and API/security checks pass.
5. Check Atlas and self-managed capability boundaries, server/driver version compatibility, permissions, backup restore and error/retry paths.
6. Do not issue certificates or alter XP from course files; retain the existing backend's verified/idempotent gamification policy.
