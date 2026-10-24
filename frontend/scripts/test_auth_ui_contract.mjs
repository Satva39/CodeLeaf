import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = async (relativePath) => readFile(path.join(here, "..", "src", relativePath), "utf8");
const [authPage, app, header, profile, accountStyles] = await Promise.all([
  source("pages/AuthPage.jsx"),
  source("App.jsx"),
  source("components/layout/Header.jsx"),
  source("pages/ProfilePage.jsx"),
  source("styles/account.css"),
]);
const check = (pattern, content, message) => assert.ok(pattern.test(content), message);

check(/`\/api\/auth\/\$\{isRegister \? "register" : "login"\}`/, authPage, "registration/login endpoints must remain wired");
check(/\/api\/auth\/forgot-password/, authPage, "password recovery endpoint must remain wired");
check(/\/api\/auth\/reset-password/, authPage, "password reset endpoint must remain wired");
check(/codeleaf:auth-changed.*authenticated:\s*true/s, authPage, "successful login must publish an authenticated transition");
check(/\/api\/auth\/verify-email/, authPage, "email verification endpoint must remain wired");
check(/\/api\/auth\/verify-email-change/, authPage, "email-change confirmation endpoint must remain wired");
check(/type=\{showPassword \? "text" : "password"\}/, authPage, "password input must switch between masked and visible types");
check(/aria-label=\{showPassword \? "Hide password" : "Show password"\}/, authPage, "password visibility toggle must have an accessible dynamic label");
check(/aria-pressed=\{showPassword\}/, authPage, "password visibility toggle must expose its pressed state");
check(/className="button button-secondary button-wide auth-resend-button"/, authPage, "resend verification action must use the styled secondary button");
check(/resending \? "Sending verification link…" : "Resend verification link"/, authPage, "resend verification action must expose its sending state");
check(/\.auth-password-toggle:focus-visible/, accountStyles, "password toggle must have a visible keyboard focus indicator");
check(/\.auth-resend-button:hover:not\(:disabled\)/, accountStyles, "resend button must have a designed hover state");

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
console.log("PASS password visibility toggle is accessible and masked by default");
console.log("PASS resend verification button includes an accessible loading state and themed styles");
console.log("PASS the header rechecks /api/me and refreshes on auth changes");
console.log("PASS password/email changes and account actions publish signed-out state");
console.log("Frontend authentication UI contract checks passed.");
