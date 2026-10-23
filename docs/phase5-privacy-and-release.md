# CodeLeaf Phase 5 privacy, roles, and release boundaries

## Learning and analytics

Recommendations are deterministic rules based on recorded lesson progress, exercise attempts, and scheduled reviews. XP is an engagement reward and must not be presented as mastery. Review timing stores UTC instants; the learner's IANA timezone is a display/control preference. Analytics is opt-in per account. `course_start` records a published course overview load; `lesson_dropoff` records client-observed navigation away from a lesson route and is only a navigation proxy, not proof of learner disengagement. `course_completion` is emitted only when the server confirms the final published lesson was newly completed. Exercise incorrect counts grouped by course and item provide an error-rate proxy for difficulty. Stored analytics events intentionally omit user ID, email, IP, raw answers, submitted source code, and free-form payloads; event timestamps are cleaned opportunistically on analytics ingestion or summary requests against a 90-day retention window; this is not a scheduled deletion guarantee, so configure a daily retention job for formal compliance. The summary omits groups with fewer than five events, but this is an event-count threshold rather than a distinct-learner cohort threshold because the schema deliberately does not retain account IDs.

## Portfolio

Project submissions are private by default. Sharing requires an explicit visibility change and each displayed metadata field is set by the owner. Public payloads must never contain submitted source bundles, user email, private profile fields, answer keys, or secrets. Screenshot URLs are HTTPS-only metadata; use controlled storage with content-type/size checks and moderation before accepting uploaded files in a later phase.

## Content studio and permissions

The editor role is stored on the server-side `users.role` column and cannot be granted via profile or revision request payloads. Assign editor/admin roles only through a trusted administrator or database operations procedure, protected by audit controls. Revision validation and review must precede a studio publish action. **Current studio publishing updates revision history only; it does not write live course files or bypass the existing importer/release preflight.** Before making a revision learner-visible, export it into the normal structured content workflow, run validations and review, then publish the specific approved content using existing procedures.

## Migrations and rollback

Apply `alembic upgrade head` only after a database backup and after reviewing the migration against the target database. The Phase 5 migration is defensive against already-present columns/tables but must still be tested on a disposable copy of the production schema before deployment. Rolling back the migration drops Phase 5 tables and the added `users.role` and `project_submissions.portfolio_metadata` columns; this discards Phase 5 data, so prefer restoring the database backup or forward-fixing unless the data loss is accepted.
