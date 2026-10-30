import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const vercel = JSON.parse(fs.readFileSync(path.join(root, "vercel.json"), "utf8"));
const proxy = fs.readFileSync(path.join(root, "api/proxy/[...path].js"), "utf8");
const packageJson = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const render = fs.readFileSync(path.join(root, "../render.yaml"), "utf8");
assert.equal(vercel.rewrites?.[0]?.source, "/api/:path*");
assert.equal(vercel.rewrites?.[0]?.destination, "/api/proxy/:path*");
assert.match(proxy, /CODELEAF_API_ORIGIN/);
assert.equal(vercel.rewrites?.[1]?.source, "/(.*)");
assert.match(proxy, /process\.env\.CODELEAF_API_ORIGIN/);
assert.match(proxy, /DEFAULT_API_ORIGIN = "https:\/\/codeleaf-api\.onrender\.com"/);
assert.match(proxy, /\/api\/\$\{path\}/);
assert.equal(packageJson.scripts["test:deployment-config"], "node scripts/test_deployment_config.mjs");
for (const key of ["DATABASE_URL", "FRONTEND_ORIGINS", "FRONTEND_BASE_URL", "JWT_SECRET", "EMAIL_TEST_MODE", "EMAIL_FROM", "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_USE_TLS", "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET", "RAZORPAY_PRO_PLAN_ID", "RAZORPAY_MAX_PLAN_ID"]) {
  assert.match(render, new RegExp(`key: ${key}(?:\\s|$)`), `Render blueprint must declare ${key}`);
}
assert.match(render, /key: PREVIEW_DRAFT_COURSES\s+value: "false"/);
assert.match(render, /healthCheckPath: \/api\/ready/);
console.log("PASS production API paths rewrite to the same-origin Vercel proxy");
console.log("PASS proxy forwards to configured server-only API origin or the default production backend and preserves /api prefix");
console.log("PASS Render blueprint declares Razorpay server-only credential and plan-ID settings");
console.log("PASS the SPA fallback remains configured");
console.log("PASS Render blueprint declares required production database, origin, and SMTP settings");
