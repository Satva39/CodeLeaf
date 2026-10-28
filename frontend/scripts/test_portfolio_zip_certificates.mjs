import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const page = readFileSync(new URL("../src/pages/PortfolioPage.jsx", import.meta.url), "utf8");
const routes = readFileSync(new URL("../../backend/app/phase5_routes.py", import.meta.url), "utf8");
const migration = readFileSync(new URL("../../backend/alembic/versions/0006_portfolio_project_zip_archives.py", import.meta.url), "utf8");
const chunkMigration = readFileSync(new URL("../../backend/alembic/versions/0007_portfolio_zip_chunks.py", import.meta.url), "utf8");

assert.match(page, /type="file" accept="\.zip,application\/zip"/);
assert.match(page, /api\/me\/portfolio\/submissions\/upload/);
assert.match(page, /Download ZIP/);
assert.match(page, /Certificates earned/);
assert.match(page, /verification_url/);
assert.match(routes, /MAX_PROJECT_ZIP_BYTES = 500 \* 1024 \* 1024/);
assert.match(routes, /Project ZIP files must be 500 MB or smaller/);
assert.match(routes, /Accept any learner-created ZIP/);
assert.doesNotMatch(routes, /A matching course project was not found in the reviewed course manifest/);
assert.match(routes, /ProjectSubmissionZipChunk/);
assert.match(page, /any project you built yourself/);
assert.match(page, /Maximum 500 MB compressed/);
assert.match(chunkMigration, /project_submission_zip_chunks/);
assert.match(routes, /unsafe file path or symbolic link/);
assert.match(routes, /_portfolio_certificate_items\(db, owner\)/);
assert.match(routes, /visibility == "public"/);
assert.match(migration, /zip_bundle/);
assert.match(migration, /zip_filename/);

console.log("Portfolio ZIP upload/download and certificate display contract checks passed.");
