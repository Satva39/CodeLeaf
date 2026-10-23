# AI Course Status

- **Target slug:** `ai`
- **Source:** `AI.pdf`, 45 pages; Sections A–G reviewed.
- **Status:** draft; do not publish without subject-matter review.
- **Verified source-syllabus counts:** 18 modules, 158 numbered lessons, 1,039 source subtopics, 24 practical exercises, 10 projects including the capstone.
- **Generated patch counts:** 18 modules, 158 lesson JSON files, 24 exercise JSON files, 24 protected exercise solution files, 10 project JSON files, 10 protected project solution-outline files, 158 protected knowledge-check sets / 474 questions, 1 final exam blueprint, 18 SVG module diagrams.
- **Integration:** uses existing `backend/scripts/import_course_files.py` and `app.course_content_validation.validate_course_tree`; no application/schema/deployment configuration changes are included.
- **Examples:** standard-library Python examples use the `static-validation` execution mode. They are not executed by the browser and do not call model APIs.
- **Security:** keep question sets/solution outlines in backend content; never send private answer keys to a public client or execute arbitrary learner code in the production FastAPI process.
- **Assessment:** each lesson knowledge check has three questions, but the content and lightweight keyword graders still need subject-matter review. The final assessment is a blueprint only.
- **Deployment:** not deployed or tested against a live database.
