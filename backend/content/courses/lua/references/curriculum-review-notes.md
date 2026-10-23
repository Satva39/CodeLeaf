# Lua curriculum review notes

## Source coverage

The 33-page attached PDF was reviewed across Sections A–G, including its numbered syllabus, 25 practice exercises, project progression, specialist topics, and suggested path. The 22 modules and 226 lesson headings are carried into `course.json`, module files, and individual lesson files. PDF lesson titles/subtopic terminology is retained where practical.

## Version and accuracy notes

- The PDF’s 5.5 baseline is retained. At the check date (2026-10-20), Lua.org lists Lua 5.5.1 as the latest stable release: https://www.lua.org/download.html.
- Lua 5.5 introduces explicit global-declaration facilities and other changes; not every global assignment should be described as universally requiring a declaration. See https://www.lua.org/manual/5.5/manual.html and https://www.lua.org/versions.html.
- `table.create`, named variadic argument syntax, loop-variable rules, garbage-collection changes, and UTF-8 behavior are version-specific. Check the Lua 5.5 manual and do not assume they exist on Lua 5.1 or LuaJIT.
- Lua patterns are not interchangeable with PCRE-style regular expressions. Lua’s `#` length operator on tables depends on sequence boundaries; `pairs` ordering is not guaranteed.
- `load` with a reduced environment is not a complete sandbox. Untrusted scripts need a carefully designed host boundary, process isolation, and enforced resource/time/network/filesystem limits.
- LÖVE and OpenResty APIs are host-specific. The C API, binary modules, and precompiled bytecode must match the target Lua runtime/ABI.
- The final-exam questions and exercise/project solution guides are draft materials; human item-level review and test calibration are required before publication.

## Validation / deployment

This is an additive course-content patch. The project ZIP’s existing importer and validator support the file layout, so no schema, migration, frontend, dependency manifest, Render, Vercel or Docker changes are included. Course content is `draft`. No database import, publication, Lua interpreter execution, C build, LÖVE launch, or production deployment was performed.

## PDF scope qualifications

No syllabus item was intentionally omitted from the 226 ordered lesson headings. Host-specific and legacy topics remain specialist tracks rather than being presented as universal Lua features. Practical exercises and project briefs are normalized from the PDF into per-file records. Any generated generic knowledge-check distractors and architecture-level reference solution guides require review rather than publication as approved assessment content.
