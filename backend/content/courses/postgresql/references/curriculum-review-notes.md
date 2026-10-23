# PostgreSQL curriculum review notes

## Source inspection

- Source: attached `PostgreSQL.pdf`, 51 pages. All pages were rendered and reviewed as page images; extracted text was parsed to confirm the complete 24-module and 220-lesson sequence. The PDF includes Section C (26 exercises), Section D (10 projects including the multi-vendor commerce capstone), Section E (core/advanced/specialist priority guidance), Section F (seven suggested learning stages and dependency notes) and Section G (coverage/quality rules).
- The generated course preserves the source lesson numbering and topic labels. Each numbered topic has an independent lesson JSON, its own protected three-question knowledge check and shared SVG visual(s). All authored artifacts remain draft.
- Workload (180 hours) and per-lesson learning outcomes/examples are author-created planning estimates rather than claims from the PDF.

## Version and technical clarifications

1. The source overview states PostgreSQL 18.6 docs as the primary reference and PostgreSQL 19 in development. Official docs checked 2026-10-15 show PostgreSQL 18.6 as the current PostgreSQL 18 documentation, with PostgreSQL 19 still in beta/development; the course therefore does not teach 19-only features as stable.
2. PostgreSQL 18 changes generated-column behavior: virtual generated columns are the default. The lesson on generated columns explicitly calls out the VIRTUAL/STORED distinction and requires checking version-specific restrictions.
3. `EXPLAIN ANALYZE` executes the statement being measured. The performance lessons warn against applying it to a mutating statement unless execution is intended and safe.
4. Extension topics are clearly bounded: PostGIS and pg_trgm may require installing/enabling optional extensions and suitable privileges; they are not assumed present in all managed environments.
5. Replication, physical backup/restore, WAL archiving, row-level security, roles and operational exercises are design/lab content; the package does not configure a server or claim that a restore/failover was executed.
6. SQL is PostgreSQL-specific where relevant. Python driver examples use parameterized SQL but require a separate isolated runner; the current CodeLeaf playground preview does not execute server code.

## Coverage boundary and omissions

- No lesson topic from the PDF's 1–220 continuous sequence was excluded. All subtopics beneath each numbered topic were extracted into each lesson's `subtopics` and displayed as coverage blocks.
- All 26 Section C exercise briefs are represented. All 10 Section D project briefs are represented, including the capstone. Section E specialist topics are mapped into modules 13, 18, 21 and 23 where relevant; optional extension/internals content does not replace the core database path.
- `course.json` contains one assessment blueprint; the content does not claim a new randomized exam delivery/persistence engine or certificate issuance implementation. That remains subject to the existing platform's verified capabilities.
- No external diagrams or image URLs are used. All visual assets are original self-contained SVG files and locally referenced in the manifest.

## Primary official references

- PostgreSQL 18.6 manual: https://www.postgresql.org/docs/18/
- PostgreSQL 18 release notes: https://www.postgresql.org/docs/18/release-18.html
- PostgreSQL tutorial: https://www.postgresql.org/docs/18/tutorial.html
- SQL language reference: https://www.postgresql.org/docs/18/sql.html
- Data types: https://www.postgresql.org/docs/18/datatype.html
- Data definition: https://www.postgresql.org/docs/18/ddl.html
- Queries: https://www.postgresql.org/docs/18/queries.html
- Concurrency control: https://www.postgresql.org/docs/18/mvcc.html
- Indexes and EXPLAIN: https://www.postgresql.org/docs/18/indexes.html and https://www.postgresql.org/docs/18/using-explain.html
- Security and row-level security: https://www.postgresql.org/docs/18/user-manag.html and https://www.postgresql.org/docs/18/ddl-rowsecurity.html
- Backup and restore: https://www.postgresql.org/docs/18/backup.html
- High availability and replication: https://www.postgresql.org/docs/18/high-availability.html
- Psycopg 3: https://www.psycopg.org/psycopg3/docs/

Official version claims were checked online on 2026-10-15. Lesson-specific explanations, quizzes and SQL examples remain draft until reviewed and run against the chosen PostgreSQL environment.
