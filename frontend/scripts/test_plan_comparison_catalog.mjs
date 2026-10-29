import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  FALLBACK_PLAN_CATALOG,
  hasCompletePlanCatalog,
  mergePlanCatalog,
  normalizePlanCatalogPayload,
} from "../src/lib/planCatalog.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const page = fs.readFileSync(path.join(root, "src/pages/PlansPage.jsx"), "utf8");

// Empty / failed API responses must still render a complete comparison matrix.
const fallbackOnly = mergePlanCatalog([]);
assert.equal(fallbackOnly.length, 4);
assert.deepEqual(fallbackOnly.map((plan) => plan.id), ["free", "pro", "max", "full_access"]);
assert.equal(fallbackOnly.every((plan) => plan.features.published_learning === true), true);
assert.equal(fallbackOnly.every((plan) => plan.features.learning_progress === true), true);
assert.equal(fallbackOnly.every((plan) => plan.features.course_exams === true), true);
assert.equal(fallbackOnly.every((plan) => plan.features.portfolio === true), true);
assert.equal(fallbackOnly[0].features.advanced_analytics, false);
assert.equal(fallbackOnly[1].features.advanced_analytics, true);
assert.equal(fallbackOnly[1].features.premium_practice_sets, false);
assert.equal(fallbackOnly[2].features.premium_practice_sets, true);
assert.equal(fallbackOnly[3].features.ad_free, true);
assert.equal(fallbackOnly[0].limits.project_storage_bytes, 1024 ** 3);
assert.equal(fallbackOnly[1].limits.project_storage_bytes, 10 * 1024 ** 3);
assert.equal(fallbackOnly[2].limits.project_storage_bytes, 50 * 1024 ** 3);
assert.equal(fallbackOnly[3].limits.project_storage_bytes, 100 * 1024 ** 3);
assert.equal(fallbackOnly[3].limits.max_single_zip_bytes, 500 * 1024 ** 2);
assert.equal(fallbackOnly[3].limits.code_executions_per_day, 1500);

// Support current and legacy catalog shapes, and use live values where available.
assert.equal(normalizePlanCatalogPayload({ items: FALLBACK_PLAN_CATALOG }).length, 4);
assert.equal(normalizePlanCatalogPayload({ plans: FALLBACK_PLAN_CATALOG }).length, 4);
assert.equal(normalizePlanCatalogPayload({ available_plans: { free: FALLBACK_PLAN_CATALOG[0] } })[0].id, "free");
assert.equal(hasCompletePlanCatalog(FALLBACK_PLAN_CATALOG), true);
assert.equal(hasCompletePlanCatalog([{ id: "free", features: {}, limits: {} }]), false);
const incompleteLive = [{ id: "free", amount_paise: 123, features: { published_learning: true }, limits: { workspaces: 99 } }];
const mergedLive = mergePlanCatalog(incompleteLive);
assert.equal(mergedLive[0].amount_paise, 123);
assert.equal(mergedLive[0].features.learning_progress, true);
assert.equal(mergedLive[0].limits.workspaces, 99);
assert.equal(mergedLive[0].limits.project_storage_bytes, 1024 ** 3);

// Frontend must render meaningful included states and clearly disclose fallback mode.
assert.match(page, /mergePlanCatalog\(planCatalog\)/);
assert.match(page, /value === true \? "Included" : "Not included"/);
assert.match(page, /plan-catalog-fallback/);
assert.match(page, /hasCompletePlanCatalog\(items\)/);

console.log("PASS pricing comparison shows included features and correct allowances when the API catalog is unavailable or incomplete");
