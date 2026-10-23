# MySQL course status and source coverage

**Status: DRAFT — not approved for publication.**

Built from the supplied `MySQL.pdf` (32 pages). The full text and page contact sheet were inspected. Every numbered syllabus topic is retained in order as its own lesson: topics 1–435; modules 1–37. No numbered topic is intentionally omitted.

## Module coverage

| Module | Source title | Topic range | Topic count | Track |
|---:|---|---:|---:|---|
| 1 | Introduction to MySQL | 1–8 | 8 | core |
| 2 | Installing and Setting Up MySQL | 9–17 | 9 | core |
| 3 | Your First Database and SQL Fundamentals | 18–27 | 10 | core |
| 4 | MySQL Data Types | 28–37 | 10 | core |
| 5 | Database, Table, and Schema Management | 38–46 | 9 | core |
| 6 | Inserting, Updating, and Deleting Data | 47–54 | 8 | core |
| 7 | Retrieving and Filtering Data | 55–64 | 10 | core |
| 8 | Operators and Built-In Functions | 65–74 | 10 | core |
| 9 | Aggregate Functions and Grouping | 75–80 | 6 | core |
| 10 | Working with Table Relationships and Joins | 81–88 | 8 | core |
| 11 | Subqueries, CTEs, and Set Operations | 89–98 | 10 | core |
| 12 | Relational Database Design | 99–111 | 13 | core |
| 13 | Advanced Data Modification and Validation | 112–120 | 9 | core |
| 14 | Indexing Fundamentals | 121–131 | 11 | core |
| 15 | Views and Reusable Database Logic | 132–138 | 7 | core |
| 16 | Stored Procedures and Stored Functions | 139–150 | 12 | core |
| 17 | Triggers and Scheduled Events | 151–160 | 10 | core |
| 18 | Window Functions and Analytical Queries | 161–172 | 12 | advanced |
| 19 | Transactions and Concurrency Control | 173–186 | 14 | advanced |
| 20 | MySQL JSON | 187–198 | 12 | optional |
| 21 | Full-Text Search and Spatial Data | 199–211 | 13 | optional |
| 22 | Table Partitioning and Storage Engines | 212–224 | 13 | optional |
| 23 | MySQL Security Fundamentals | 225–240 | 16 | core-professional |
| 24 | Server Administration and Configuration | 241–253 | 13 | core-professional |
| 25 | Monitoring, Logs, and Diagnostics | 254–267 | 14 | core-professional |
| 26 | Database Import, Export, and Migration | 268–280 | 13 | core-professional |
| 27 | Backup, Recovery, and Disaster Preparedness | 281–294 | 14 | core-professional |
| 28 | Query Performance and Optimization | 295–310 | 16 | advanced |
| 29 | Server and Workload Performance Tuning | 311–324 | 14 | advanced |
| 30 | Replication and Read Scalability | 325–339 | 15 | advanced-dba |
| 31 | High Availability and Cluster Architecture | 340–352 | 13 | advanced-dba |
| 32 | Connecting MySQL to Applications | 353–372 | 20 | core-professional |
| 33 | Testing and Database Quality | 373–384 | 12 | core-professional |
| 34 | Version Control, Deployment, and Operations | 385–397 | 13 | core-professional |
| 35 | MySQL Troubleshooting and Best Practices | 398–412 | 15 | core-professional |
| 36 | Version Compatibility and Legacy MySQL | 413–422 | 10 | core-professional |
| 37 | Optional Ecosystem and Specialist Topics | 423–435 | 13 | optional |

## Course counts

- 37 modules and 435 individual lesson JSON files.
- 435 separate exercise JSON files, each linked from its lesson, each with a repository-only solution file.
- 435 separate lesson knowledge-check files; 3 questions per set (1,305 questions total).
- 1 final assessment question set with 10 questions; 1 exam blueprint.
- 11 staged project files, each with a separate starter file and protected reference plan.
- 472 original SVG visuals: 37 module overview diagrams and 435 lesson-level diagrams.
- 1 synthetic CSV dataset: `datasets/sample_sales.csv` (data file; not a visual asset).

## Version and scope notes

- The PDF’s October 2026 claim about MySQL 9.7 and 26.7 release lines was checked against official MySQL release documentation. The course labels 9.7 as its default stable-track reference and directs learners to 26.7 documentation for release-specific behavior.
- The source PDF notes InnoDB as the default in MySQL 8.4; the course preserves that statement with an explicit 8.4 scope rather than inferring that every release or managed service must have the same configuration.
- SQL set-operation support, JSON schema validation, optimizer commands, authentication defaults, storage engines, and connector APIs can be version- or distribution-specific. Individual lessons call out this requirement and link to official references.
- Most statements in the PDF are syllabus topics, not completed tutorials; the course provides new draft teaching material and original visuals instead of presenting the PDF itself as lesson prose.

## Review gates before publication

1. Execute representative SQL examples against the chosen MySQL versions; syntax/output checks here are static unless expressly stated.
2. Review all lesson outcomes, generated distractors and protected answer files for technical accuracy.
3. Confirm FastAPI responses never expose question answer keys, exercise grading configuration, or project reference solutions.
4. Import as drafts first; set authored status to `published` only after content review and tests.
5. Re-run the course validator, importer dry-run, backend API contract tests and frontend build after import.
