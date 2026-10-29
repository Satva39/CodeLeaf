import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const plans = readFileSync(new URL("../src/data.js", import.meta.url), "utf8");
const plansPage = readFileSync(new URL("../src/pages/PlansPage.jsx", import.meta.url), "utf8");
const adsController = readFileSync(new URL("../src/components/monetization/AdSenseController.jsx", import.meta.url), "utf8");
const app = readFileSync(new URL("../src/App.jsx", import.meta.url), "utf8");
const index = readFileSync(new URL("../index.html", import.meta.url), "utf8");

for (const [id, price, billing] of [
  ["free", "₹0", "Free forever"],
  ["pro", "₹299", "per month"],
  ["max", "₹699", "per month"],
  ["full_access", "₹49,999", "one-time · lifetime access"],
]) {
  assert.ok(plans.includes(`id: "${id}"`), `${id} pricing card exists`);
  assert.ok(plans.includes(`price: "${price}"`), `${id} price is correct`);
  assert.ok(plans.includes(`billing: "${billing}"`), `${id} billing interval is explicit`);
}
assert.match(plansPage, /api\/me\/entitlements/);
assert.match(plansPage, /plan-comparison-table/);
assert.match(plansPage, /usage-grid/);
assert.match(plansPage, /one-time · lifetime access/);
assert.match(adsController, /api\/me\/entitlements/);
assert.match(adsController, /snapshot\?\.features\?\.ad_free !== true/);
assert.match(adsController, /isAdSafeRoute/);
assert.match(adsController, /window\.location\.reload\(\)/);
assert.match(app, /<AdSenseController \/>/);
assert.match(index, /google-adsense-account/);
assert.doesNotMatch(index, /pagead\.googlesyndication\.com\/pagead\/js\/adsbygoogle\.js/, "AdSense is not globally bootstrapped on sensitive routes");

console.log("Subscription pricing, comparison, account usage and conditional AdSense contracts passed.");
