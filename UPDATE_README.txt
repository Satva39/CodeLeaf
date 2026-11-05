CODELEAF — DOG AVATAR + PUBLIC PROFILE UPDATE
Changed/added files overlay for the Code_Leaf.zip you supplied

CONTENTS
- Shared dog-avatar renderer and centralized item artwork registry
- Avatar wardrobe/editor with temporary preview, discard, and one atomic save
- Accessory/outfit artwork assets (including the repaired Moon Hoodie asset)
- Profile integration and public profile page at /u/<username>
- Public profile settings and section-level privacy controls
- Backward-compatible Alembic migration for opt-in publication settings and
  case-insensitive username uniqueness
- Backend and frontend integration contract tests

APPLYING THE UPDATE
1. Make a fresh copy/backup of your current Code_Leaf project.
2. Extract this ZIP into the Code_Leaf project root, preserving the folder
   structure, and allow the listed changed files to be replaced.
3. Do not replace .env, .git, node_modules, backend/.venv, or backend/content.
4. No new environment variables are required for the default deployment.
   The existing Vercel same-origin API proxy is retained. CODELEAF_API_ORIGIN
   remains an optional server-side Vercel override if your backend origin differs.

BACKEND VALIDATION / MIGRATION
From the backend directory:
  python -m py_compile app/main.py app/models.py app/schemas.py app/games_routes.py app/auth_routes.py alembic/versions/0014_public_profile_visibility.py
  python scripts/test_public_profile_api.py
  alembic upgrade head

Run the migration against the intended database only after taking your normal
Neon backup and confirming DATABASE_URL points to that database. The migration
adds opt-in public-profile columns and a case-insensitive username index; it
preserves user rows and existing usernames. It deliberately stops if historical
case-only duplicate usernames exist, rather than renaming or deleting users.

FRONTEND VALIDATION
From the frontend directory, on the target OS:
  npm ci
  npm run build
  node scripts/test_dog_avatar_consistency.mjs
  node scripts/test_dog_profile_integration.mjs
  node scripts/test_battles_avatar_contract.mjs
  node scripts/test_deployment_config.mjs

If node_modules was copied from Windows to Linux (or the reverse), reinstall it
with npm ci on the target OS. The source ZIP's installed dependencies are
platform-specific; this update ZIP intentionally does not include node_modules.

PUBLIC PROFILE BEHAVIOR
- New profiles are private by default.
- A valid username always has a share URL preview: /u/<username>.
- Publishing requires an active, email-verified account.
- XP, streak, certificates, achievements, and learning progress are returned
  only when the owner enables their individual visibility setting.
- Private, inactive, and unverified public-profile lookups are indistinguishable
  and return 404. Email, password hashes, tokens, account IDs, roles, and private
  portfolio data are not serialized by the public endpoint.

VALIDATION RESULT FROM THIS WORKSPACE
- Public-profile/avatar backend integration test: PASS (9 checks).
- Backend phase-5 contract suite: PASS (8 checks).
- Frontend source-contract suite: 40/41 PASS. The sole failing test is the
  existing portfolio ZIP contract assertion in test_portfolio_zip_certificates.mjs;
  it concerns backend/app/phase5_routes.py and is unrelated to this update.
- Changed JSX files: PASS Babel parser validation (6 files).
- Avatar artwork registry: PASS; all 32 referenced image files exist and are
  non-empty.
- Vite production build could not be completed in this Linux workspace because
  the provided node_modules contains Windows Rollup binaries and lacks the
  Linux optional package @rollup/rollup-linux-x64-gnu. Re-run npm ci on the
  deployment OS and then npm run build.

NOTES
- No production deployment or GitHub push was performed.
- No production database records were changed.
- This package contains only files that differ from, or are newly added to,
  the exact Code_Leaf.zip supplied in this conversation, plus this README and
  its manifest.
