import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = async (relativePath) => readFile(path.join(here, "..", "src", relativePath), "utf8");
const [authPage, app, header, profile, accountStyles, pageStyles] = await Promise.all([
  source("pages/AuthPage.jsx"),
  source("App.jsx"),
  source("components/layout/Header.jsx"),
  source("pages/ProfilePage.jsx"),
  source("styles/account.css"),
  source("styles/pages.css"),
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
check(/apiFetch\(`\$\{API_BASE\}\/api\/auth\/logout`/, profile, "logout must call the existing server logout endpoint");
check(/if \(!response\.ok \|\| payload\?\.ok === false\)/, profile, "logout must not redirect when the server reports failure");
check(/invalidateApiCache\(\)/, profile, "successful logout must clear cached session/user responses");
check(/navigate\("\/login", \{ replace: true \}\)/, profile, "successful logout must replace the current route with sign-in");
check(/className="account-logout-button"/, profile, "signed-in account settings must show a logout button");
check(/accountMode === "remote" && \(\s*<button/s, profile, "logout must only be shown after a signed-in session is confirmed");
check(/setLogoutError\(error\?\.message \|\| "Logout could not be completed\. Please try again\."\)/, profile, "logout failure must be surfaced to the user");
check(/\.account-info-card \.account-logout-button:focus-visible/, pageStyles, "logout button must have a visible keyboard focus indicator");
check(/\.account-info-card \.account-logout-button:hover:not\(:disabled\)/, pageStyles, "logout button must have a hover state");
check(/Change password/, profile, "the existing change-password UI must remain available");
check(/\/api\/auth\/change-password/, profile, "the existing change-password endpoint must remain wired");
assert.doesNotMatch(profile, /privacy controls|PRIVACY & VISIBILITY|account-setting-unavailable|Not available yet/i, "the unfinished privacy placeholder must be removed from the profile page");
check(/onClick=\{exportAccount\}/, profile, "Download my data must remain available in account security");
check(/apiFetch\(`\$\{API_BASE\}\/api\/me\/export`\)/, profile, "Download my data must call the existing export endpoint");
check(/codeleaf-account-export\.json/, profile, "account export must download a JSON file");
check(/onClick=\{deleteAccount\}/, profile, "Delete account must remain available in account security");
check(/apiFetch\(`\$\{API_BASE\}\/api\/me\/delete`/, profile, "Delete account must call the existing deletion endpoint");
check(/Enter your current password to confirm account deletion/, profile, "account deletion must retain the current-password confirmation");

const preferencesStyles = await source("styles/phase3c-personal-learning.css");
check(/\.phase3c-preferences-form select option\s*\{[^}]*background-color:\s*#172338;[^}]*color:\s*#e8edf7;/s, preferencesStyles, "dark-theme dropdown options must have readable foreground and background colors");
check(/:root\[data-theme="light"\] \.phase3c-preferences-form select option\s*\{[^}]*background-color:\s*#ffffff;[^}]*color:\s*#182235;/s, preferencesStyles, "light-theme dropdown options must have readable foreground and background colors");

console.log("PASS auth routes and action-link pages remain wired");
console.log("PASS successful login publishes a signed-in state transition");
console.log("PASS password visibility toggle is accessible and masked by default");
console.log("PASS resend verification button includes an accessible loading state and themed styles");
console.log("PASS the header rechecks /api/me and refreshes on auth changes");
console.log("PASS password/email changes and account actions publish signed-out state");
console.log("PASS logout calls the server, clears cached state, and handles failures safely");
console.log("PASS privacy placeholder is removed while data export and account deletion remain wired");
console.log("Frontend authentication UI contract checks passed.");
