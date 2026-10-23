# CodeLeaf frontend organization update

## Changes

- Split the route table into a small `App.jsx`.
- Moved each primary page to its own module under `frontend/src/pages/`.
- Moved shared layout pieces to `components/layout/` and reusable widgets to `components/common.jsx`.
- Extracted browser demo state to `lib/demoState.js`.
- Extracted sample lesson-content builders to `data/lessonContent.js`.
- Split the stylesheet into `frontend/src/styles/` files while preserving cascade order.
- Increased small typography values and key text styles for more comfortable default reading, based on the supplied 110% zoom screenshot.
- Added `frontend/src/README.md` explaining where common future changes belong.

## Scope note
This is a source organization and readability pass; it does not replace the course-manifest importer or mark roadmap courses as published.
