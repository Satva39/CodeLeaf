# Phase 3B — Retrieval Practice and Review Queue

## What this increment adds

- A `/review` page driven by the authenticated `/api/me/reviews` response.
- Due and upcoming review lists for the current signed-in account.
- A review entry point from the learner's Progress page and main navigation.
- “Remind tomorrow” snoozing using the existing server endpoint.
- Daily review limit and first-interval preferences, saved through the existing learning-preferences endpoint.
- A self-rating step at the end of a review lesson (`Again`, `Hard`, `Good`, `Easy`) that updates the existing persistent review schedule.
- Published-content checks for review targets so hidden or removed lesson/exercise entries are not exposed by the queue.
- Account-scoped ratings: the review ID, course, lesson, item type, and item slug must agree on the server.

## Learning and reward integrity

Self-ratings are learner-reported scheduling signals. They do not prove mastery, complete a lesson, reveal protected answers, or award XP. XP remains controlled by the existing server-verified lesson completion and exercise grading flow. Existing `review_schedules` and `learning_preferences` tables from `0004_phase5_capabilities` are reused; this increment adds no database migration.

## API behavior

- `GET /api/me/reviews`: due and upcoming items plus preferences.
- `POST /api/me/reviews/{review_id}/snooze`: snooze a user's own review item.
- `POST /api/me/reviews/{review_id}/rate`: record the learner's recall rating and update the next review interval.
- `PATCH /api/me/learning-preferences`: save the review frequency and daily limit.

Review scheduling still depends on server-recorded lesson completion and exercise submission events. It does not create review history from page visits or localStorage-only progress.
