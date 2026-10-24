# Phase 3C — Personal learning, bookmarks, and calm motivation

## Included
- A more useful bookmarks library with search, per-course filtering, sorting, counts, responsive rows, and clear empty/error states. It retains the existing account bookmark API and browser-only guest behavior.
- Account-backed learning preferences for review cadence, daily review cap, timezone, and explicit opt-in product analytics. It uses the existing `/api/me/learning-preferences` endpoints from Phase 5; no migration or new backend endpoint is introduced.
- Styles are added in a page-scoped stylesheet imported by the two affected pages. Global `frontend/src/styles.css` and existing imports are not modified.

## Safety / behavior
- Guest preferences are not represented as account-synced or silently written to the server.
- Preferences load only after `/api/me` confirms an authenticated account.
- Server validation remains authoritative for time zone, interval, daily limit, and analytics consent.
- The UI does not generate fake XP, streaks, or completion totals.
- Search and filters only change the current bookmark view; they do not mutate bookmark records.

## Validation
Run `node scripts/test_phase3c_personal_learning.mjs` from `frontend/`. Then run the existing frontend test scripts and `npm run build`. Manual account-backed testing is still required on the deployed app.
