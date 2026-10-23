# Curriculum review notes — MongoDB

**Source:** supplied `MongoDB(1).pdf`, 55 pages. **Reference check date:** 2026-10-15.

## Structure retained

The PDF contains 25 modules and 261 numbered primary topics. Each numbered topic is stored as one ordered lesson; nested `n.n` subtopics are included in that lesson's `subtopics` array and displayed as a checklist. Section C's 20 practical exercises are represented by 20 additional linked practice-lab exercises. Section D's ten named projects are represented as separate project files. Section E's specializations remain optional branches. Sections F and G inform the prerequisite roadmap and quality gates.

## Interpretation/corrections

- The roadmap mentions `mongosh` as the modern shell and relegates the historical `mongo` shell to legacy maintenance. This course adopts `mongosh` as the default and treats legacy material only as migration context.
- MongoDB Atlas Search and Vector Search are specialist offerings. Lesson examples mark them as deployment-dependent and direct learners to product docs rather than implying universal Community/Enterprise availability.
- Atlas monitoring/automation, selected encryption/auditing, backup tooling and some operations can differ by hosting model and subscription/deployment. Lessons require checking feature-specific support.
- MongoDB single-document writes are atomic; multi-document transaction use is explicit rather than treating every multi-document operation as transactional. Transaction support, limitations and performance depend on topology and version.
- The reference set points to the rolling manual/current driver guides, but exact syntax and compatibility should be checked against the versions selected by the learner. No fixed server version is imposed where the PDF did not name one.
- The PDF syllabus includes topic coverage, not complete technical lessons or tested code for all 261 topics. This patch creates original lesson explanations and reference snippets; the course remains draft until examples, answer keys and deployment assumptions receive subject-matter review.

## Exclusions

No numbered syllabus topic was excluded. No frontend or backend code changes were deemed necessary: the inspected CodeLeaf importer reads each course directory using the existing `course.json`/module/lesson/exercise structure and the existing API resolves course content dynamically by slug. The patch adds only `backend/content/courses/mongodb/` plus root-level import instructions.
