# Updating an existing local CodeLeaf checkout

The update adds the complete 61-track catalog roadmap, CodeLeaf branding, deployment settings for Vercel/Render/Neon, a Vercel `/api/*` proxy, a Render blueprint, and an Alembic starter migration.

## Safely apply the update on Windows

1. Stop the frontend and backend dev servers with `Ctrl+C` in their terminals.
2. Extract the update ZIP. Copy the files **inside the `CodeLeaf` folder** over the files in your existing `E:\Code_Leaf` folder and accept replacing matching source/configuration files.
3. Keep your existing `backend\.env`, `frontend\.env`, `backend\.venv` (or `.venv`), `frontend\node_modules`, and any local database data. The ZIP intentionally does not contain secrets, virtual environments, node_modules, or the database volume.
4. In the backend terminal, activate your existing virtual environment and run `python scripts/init_db.py`. This adds the missing catalog rows; it does not publish courses or delete learner data.
5. In `frontend`, run `npm install`, then `npm run build`. This also refreshes the package lockfile for the renamed `codeleaf-frontend` package.

## Deploying later

- Push the project to GitHub.
- Create managed PostgreSQL on Neon.
- Deploy the API on Render from the root `render.yaml`; configure `DATABASE_URL`, `FRONTEND_ORIGINS`, and `JWT_SECRET` in Render settings.
- After Render gives the API a URL, replace `https://your-codeleaf-api.onrender.com` in `frontend/vercel.json` with that exact service URL and commit the change.
- Deploy the `frontend` directory on Vercel. Keep `VITE_API_BASE_URL` unset in the Vercel environment so browser requests use the same-origin `/api/*` rewrite.
- Set Render's `FRONTEND_ORIGINS` to the exact Vercel site origin, without a trailing slash, and redeploy the API.

The course tracks are roadmap placeholders until individual curricula are reviewed and imported. Real exams/certificates, live Razorpay payments, and a secure multi-language code runner need their own implementation and testing before public launch.
