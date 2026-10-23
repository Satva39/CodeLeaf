# SQLite curriculum review notes

## Source inspection

- Inspected the supplied `SQLite.pdf`: all 41 pages were rendered for visual review, and the complete extracted text was parsed. The PDF contains Sections A–G, 17 ordered modules, 220 numbered lesson topics, 18 practical exercises, 10 projects, seven optional specialist tracks, learning stages and a quality checklist. `complete-syllabus.json` preserves all lesson titles and the extracted subtopic list for auditing.
- The input is curriculum text with a dark page design; it does not provide a reusable teaching illustration set. Course diagrams in `assets/diagrams/` were authored specifically for this course.
- The supplied ZIP is the source of truth. This patch uses the existing per-course JSON filesystem content model, validator and importer; no unrelated frontend/backend code, dependency manifest or deployment setting is modified.

## Technical corrections and publication notes

1. The PDF says SQLite 3.54.0 was released on 2026-10-09. The official release history now lists SQLite **3.54.1**, released 2026-10-16. The reference baseline in this draft is updated to 3.54.1 as checked on 2026-10-20; always verify the version actually linked to an application. Source: https://sqlite.org/changes.html.
2. Keep version gates visible: STRICT tables require 3.37.0+; JSON functions are built in by default since 3.38.0 but can be omitted in custom builds; JSONB requires 3.45.0+; RETURNING requires 3.35.0+; generated columns require 3.31.0+; timediff() requires 3.43.0+. Optional modules such as FTS5 and R*Tree, compile options and loadable extensions must be verified on the target build. Sources: https://sqlite.org/datatype3.html, https://sqlite.org/json1.html, https://sqlite.org/lang_returning.html, https://sqlite.org/gencol.html, https://sqlite.org/lang_datefunc.html, https://sqlite.org/fts5.html, https://sqlite.org/rtree.html.
3. The PDF correctly identifies writer concurrency, client/server topology and network filesystems as workload-fit concerns. In particular, WAL supports concurrent readers with a writer but does not permit multiple simultaneous writers. Review https://sqlite.org/wal.html and https://sqlite.org/whentouse.html before using WAL or choosing a deployment topology.
4. Native APIs, encryption integration, optional extensions, performance benchmarks, production concurrency, restore drills and custom extensions are specialist areas. This course supplies draft learning briefs and safe local tasks; it does not claim those deployment-specific workflows were executed.
5. All generated course content remains `draft`/`unreviewed`. Knowledge-check answer keys and exercise/project reference outlines stay in the course repository with `protected_content_repository_only` visibility; verify the actual API response policy before publishing. Do not run the SQL snippets against production data.

## Integration scope

The existing `backend/scripts/validate_course_content.py` and `backend/scripts/import_course_files.py` are the expected integration path. The importer’s dry-run validates filesystem content without database writes. No production database, Vercel deployment, Render deployment, payment, certificate issuance or arbitrary SQL runner was touched or tested. SQL content is labeled for a local SQLite CLI/API or query simulation; CodeLeaf’s browser preview is not treated as an SQL runtime.
