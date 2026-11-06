import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const vercel = JSON.parse(fs.readFileSync(path.join(root, "vercel.json"), "utf8"));
const packageJson = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const render = fs.readFileSync(path.join(root, "../render.yaml"), "utf8");
assert.equal(vercel.rewrites?.[0]?.source, "/api/:path*");
assert.equal(vercel.rewrites?.[0]?.destination, "https://codeleaf-api.onrender.com/api/:path*");
assert.equal(vercel.rewrites?.[1]?.source, "/(.*)");
assert.equal(packageJson.scripts["test:deployment-config"], "node scripts/test_deployment_config.mjs");
for (const key of ["DATABASE_URL", "FRONTEND_ORIGINS", "FRONTEND_BASE_URL", "JWT_SECRET", "EMAIL_TEST_MODE", "EMAIL_FROM", "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_USE_TLS", "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET", "RAZORPAY_PRO_PLAN_ID", "RAZORPAY_MAX_PLAN_ID"]) {
  assert.match(render, new RegExp(`key: ${key}(?:\\s|$)`), `Render blueprint must declare ${key}`);
}
assert.match(render, /key: PREVIEW_DRAFT_COURSES\s+value: "false"/);
assert.match(render, /healthCheckPath: \/api\/ready/);
console.log("PASS production API paths use the same-origin Vercel rewrite to the Render API");
console.log("PASS Render blueprint declares Razorpay server-only credential and plan-ID settings");
console.log("PASS the SPA fallback remains configured");
console.log("PASS Render blueprint declares required production database, origin, and SMTP settings");
