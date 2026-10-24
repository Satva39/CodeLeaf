# Phase 3 — Polish the product experience

## Phase 3A delivered in this patch

- Home-page resume action uses the most recent API-backed lesson record when that lesson's course is currently published or explicitly in local preview.
- A completed recent lesson is labelled **Review last lesson**. An incomplete recent lesson is labelled **Resume last lesson**.
- When there is no lesson record, CodeLeaf presents a course start/continue action; it does not claim that a lesson was already being learned.
- Roadmap/draft/empty courses are excluded from public resume targets.
- Progress statistics distinguish loading and unavailable states from real zeros.
- The progress page only lists a course as “in progress” if there is actual completed-lesson activity for it, and includes a practice path from a recent lesson.
- Page-local styles are imported directly from HomePage and ProgressPage, leaving global CSS import order intact.

## Remaining Phase 3 work

### 3B — Revision and retrieval practice

Add a server-backed review schedule after checking the current production migration head. A revision queue should use persistent, account-scoped records and real review events; it must not manufacture due dates or imply cross-device sync for localStorage-only state.

### 3C — Responsive/accessibility audit

Run responsive checks on home, lessons, references, projects, practice, profile, billing, exam, and certificate pages at desktop/tablet/mobile sizes. Manually validate keyboard-only flows, visible focus, zoom, contrast, reduced motion, labels, and diagram descriptions against WCAG 2.2 AA.

### 3D — Learner dashboard, profile and bookmarks

The project snapshot already has progress/stat hooks, a progress page, and account-aware lesson bookmarks. Continue by verifying endpoint contracts and signed-out behavior, then add any new bookmark types only if the backend supports them. Do not replace account security forms or treat guest browser state as account-wide data.

### 3E — Regression and deployment

Run frontend contract tests and production build locally, test signed-in and guest flows, and verify the live Vercel→Render→Neon path after deploy. No database migrations are part of Phase 3A.
