# Bash Curriculum Review Notes

**Source:** `Bash.pdf`, 49 pages. **Review date:** 2026-10-18. **Course slug:** `bash`. **Status:** draft.

## Source coverage inspected

- Section A (course overview, learning outcomes, Bash 5.3 version scope).
- Section B (all 20 modules and every numbered lesson from 1 through 197, including each listed subtopic).
- Section C (36 practical exercises: B01–B10, I01–I12, A01–A14).
- Section D (nine smaller projects and one capstone).
- Section E (eight elective/specialist tracks E1–E8).
- Section F (the seven suggested learning phases, dependencies, and readiness milestones).
- Section G (the source document’s coverage and technical-accuracy checks).
- Page layouts/embedded visuals were reviewed using contact sheets for all 49 pages. The PDF is primarily a designed text curriculum with tables and a small capstone directory diagram; no additional embedded technical diagram text was required to reconstruct the syllabus.

## Counts and organization

- 20 ordered modules; 197 consecutive main lessons.
- Each lesson preserves its numbered title and extracted subtopic list from Section B.
- 36 practical exercises are linked to their central lesson and have protected reference-solution files.
- 10 projects are included (nine smaller projects and the Production-Ready Bash Automation Toolkit capstone), each with a 100-point review rubric and a protected reference outline.
- Each lesson has three protected draft knowledge-check questions; final assessment blueprint and question files are separate.
- Eight Section E specialist tracks are preserved separately because the source explicitly presents them as optional/specialized content rather than additions to the numbered core syllabus.

## Corrections, scope and editorial choices

1. **No main lesson titles or numbered topics were intentionally excluded.** The extracted Section B headings were checked to cover each lesson number from 1 to 197 with no numeric gaps.
2. **Specialized material remains elective.** Section E topics are kept in `references/specialist-tracks.json` and are not silently mixed into the 197 main lessons.
3. **Version discipline:** the PDF names the GNU Bash Reference Manual for Bash 5.3 as its principal source. The course also links the current official POSIX shell language, GNU utility, ShellCheck, Bats, Git, and curl documentation. Bash-specific features are labelled where relevant; associative arrays are noted as Bash 4+.
4. **Execution boundary:** the ZIP’s actual `LessonPage.jsx` uses a static/reference-output mode for non-browser languages, and the README says a separate isolated runner is required before supporting Bash/Python/etc. Therefore Bash lessons show a reference output but require local Bash or a separately isolated runner. No arbitrary learner code is added to the FastAPI production path.
5. **Security wording:** examples involving file changes, backups, deployment, or maintenance default to preview/dry-run or narrative-only examples. Production use needs explicit review, a disposable test fixture, and recovery procedures.
6. **Workload:** `estimated_workload_hours` is an editorial planning estimate, not a number stated in the supplied PDF. Review it before publication.
7. **Assessment status:** all course items remain draft. The generated question bank is a first-pass draft requiring subject-matter review before publication; correct-answer material remains in protected source files and must only be served through the backend knowledge-check route.

## Roadmap mapped from Section F

1. Lessons 1–26: first contact, terminal, syntax and quoting.
2. Lessons 27–67: variables, expansions, arrays, control flow and functions.
3. Lessons 68–95: pipelines, CLIs, files and data processing.
4. Lessons 96–117: processes and shell environment.
5. Lessons 118–148: reliability, debugging, security and advanced features.
6. Lessons 149–169: portability, tools, testing and professional maintenance.
7. Lessons 170–197: real-world automation, recovery and capstone.

## Technical references

- GNU Bash Reference Manual, Edition 5.3: https://www.gnu.org/s/bash/manual/bash.html
- POSIX.1-2024 Shell Command Language: https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html
- GNU Coreutils Manual: https://www.gnu.org/software/coreutils/manual/coreutils.html
- GNU Findutils Manual: https://www.gnu.org/software/findutils/manual/html_mono/find.html
- ShellCheck Wiki: https://www.shellcheck.net/wiki/
- Bats-core documentation: https://bats-core.readthedocs.io/en/stable/
- Git documentation: https://git-scm.com/docs
- curl documentation: https://curl.se/docs/
