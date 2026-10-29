# CodeLeaf Learning Hub & More Navigation Hotfix

## What changed

1. The Learning Hub now extracts readable messages from structured FastAPI error details instead of converting objects to `[object Object]`.
2. Requests for recommendations, reviews, roadmaps, and learning preferences now resolve independently. A plan-gated recommendations request no longer prevents the other Learning Hub sections from loading.
3. A `403 FEATURE_REQUIRES_UPGRADE` on personalized recommendations is handled as an expected plan restriction. The page shows a clear Pro-and-above upgrade prompt and a link to `/plans`; it does not weaken backend authorization.
4. The primary navbar keeps **Tutorials**, **References**, **Projects**, and **Practice** visible.
5. **Review**, **Learning hub**, **AI coach**, **Portfolio**, and **Certificates** are grouped under a responsive **More** dropdown. The dropdown closes on outside click, Escape, or navigation and exposes `aria-expanded`.
6. Responsive styles and a source-contract regression test were added/updated.

## Files in this patch

- `frontend/src/pages/LearningHubPage.jsx`
- `frontend/src/components/layout/Header.jsx`
- `frontend/src/styles/layout.css`
- `frontend/src/styles/responsive.css`
- `frontend/src/styles/phase5.css`
- `frontend/scripts/test_learninghub_upgrade_more_nav.mjs`
- `LEARNING_HUB_MORE_NAV_HOTFIX_README.md`

## Apply

Extract the ZIP into the root of your existing `E:\Code_Leaf` project, preserving folders and replacing matching files. This patch does not include `.env` files, secrets, or deletions.

## Verify locally

From the project root:

```powershell
node frontend/scripts/test_learninghub_upgrade_more_nav.mjs
node frontend/scripts/test_phase5_routes.mjs
node frontend/scripts/test_ui_polish.mjs
node frontend/scripts/test_auth_ui_contract.mjs
```

The targeted checks above passed in the build environment. JSX syntax validation also passed for `LearningHubPage.jsx` and `Header.jsx`. A full Vite production build was not run because frontend dependencies (`node_modules`, including Vite) were not installed in this environment.

## About the 403

The backend route for `/api/me/recommendations` uses the `personalized_recommendations` entitlement. The Free plan currently does not include this feature, so the backend returns HTTP 403 with a structured `FEATURE_REQUIRES_UPGRADE` detail. This patch preserves that backend rule and makes the frontend display a usable upgrade state. It does not silently grant paid functionality to Free accounts.
