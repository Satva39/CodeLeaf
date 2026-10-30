import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const page = fs.readFileSync(path.join(root, "src/pages/PlansPage.jsx"), "utf8");
const api = fs.readFileSync(path.join(root, "../backend/app/main.py"), "utf8");
assert.match(page, /setPaymentReadiness\(catalog\.payments \|\| null\)/);
assert.match(page, /ready !== true/);
assert.match(page, /checkoutUnavailable/);
assert.match(page, /disabled=\{pending === p\.id \|\| isCurrent \|\| includedInCurrent \|\| lifetimeActive \|\| checkoutUnavailable\}/);
assert.match(page, /SECURE CHECKOUT SETUP/);
assert.match(page, /missing_environment/);
assert.match(api, /def payment_checkout_readiness\(/);
assert.match(api, /"payments": payment_checkout_readiness\(\)/);
assert.match(api, /PAYMENT_CONFIGURATION_INCOMPLETE/);
assert.match(api, /RAZORPAY_WEBHOOK_SECRET/);
console.log("PASS Plans page reflects server-side payment readiness and never treats missing configuration as a successful checkout");
