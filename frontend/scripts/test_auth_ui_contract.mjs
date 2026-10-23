import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = async (relativePath) => readFile(path.join(here, "..", "src", relativePath), "utf8");
const [authPage, app, header, profile] = await Promise.all([
  source("pages/AuthPage.jsx"),
  source("App.jsx"),
  source("components/layout/Header.jsx"),
  source("pages/ProfilePage.jsx"),
]);
const check = (pattern, content, message) => assert.ok(pattern.test(content), message);

check(/`\/api\/auth\/\$\{isRegister \? "register" : "login"\}`/, authPage, "registration/login endpoints must remain wired");
check(/\/api\/auth\/forgot-password/, authPage, "password recovery endpoint must remain wired");
check(/\/api\/auth\/reset-password/, authPage, "password reset endpoint must remain wired");
check(/codeleaf:auth-changed.*authenticated:\s*true/s, authPage, "successful login must publish an authenticated transition");
check(/\/api\/auth\/verify-email/, authPage, "email verification endpoint must remain wired");
check(/\/api\/auth\/verify-email-change/, authPage, "email-change confirmation endpoint must remain wired");

for (const route of ["/forgot-password", "/reset-password", "/verify-email", "/verify-email-change"]) {
  assert.ok(app.includes(`path="${route}"`), `the app router must expose ${route}`);
}

check(/window\.addEventListener\("codeleaf:auth-changed",\s*recheck\)/, header, "the shared header must react to authentication changes");
check(/apiGetJson\(`\$\{API_BASE\}\/api\/me`/, header, "the header must confirm session state with /api/me");
check(/setIsAuthenticated\(true\)/, header, "a valid session must update signed-in UI state");
check(/setIsAuthenticated\(error\?\.status === 401 \? false : null\)/, header, "an unauthorized session must clear signed-in state without masking other API failures");
check(/invalidateApiCache\("\/api\/me"\)/, header, "authentication changes must invalidate cached user data");
check(/codeleaf:auth-changed.*authenticated:\s*false/s, profile, "account security transitions must publish signed-out state");

console.log("PASS auth routes and action-link pages remain wired");
console.log("PASS successful login publishes a signed-in state transition");
console.log("PASS the header rechecks /api/me and refreshes on auth changes");
console.log("PASS password/email changes and account actions publish signed-out state");
console.log("Frontend authentication UI contract checks passed.");
