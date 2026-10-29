/**
 * Fallback feature catalog for the public pricing comparison.
 *
 * The API remains authoritative for access enforcement. These defaults exist only
 * so the public comparison never renders an empty matrix when /api/plans is
 * temporarily unavailable or an older backend returns an incomplete schema.
 */
const MIB = 1024 * 1024;
const GIB = 1024 * MIB;
const MAX_SINGLE_ZIP_BYTES = 500 * MIB;

const FEATURES_FREE = {
  published_learning: true,
  standard_exercises: true,
  learning_progress: true,
  course_exams: true,
  earned_certificates: true,
  public_projects: true,
  portfolio: true,
  saved_workspaces: true,
  browser_playground: true,
  standard_analytics: true,
  advanced_analytics: false,
  personalized_recommendations: false,
  premium_practice: false,
  premium_practice_sets: false,
  project_planning: false,
  premium_projects: false,
  ai_tutor: false,
  ai_code_review: false,
  ad_free: false,
  priority_support: false,
  leaderboards: false,
};

const FEATURES_PRO = {
  ...FEATURES_FREE,
  advanced_analytics: true,
  personalized_recommendations: true,
  premium_practice: true,
  project_planning: true,
  leaderboards: true,
};

const FEATURES_MAX = {
  ...FEATURES_PRO,
  premium_practice_sets: true,
  premium_projects: true,
  ai_tutor: true,
  ai_code_review: true,
  ad_free: true,
  priority_support: true,
};

function limits({ storageGiB, workspaces, snippets, runs, ai, xp, ads }) {
  return {
    max_single_zip_bytes: MAX_SINGLE_ZIP_BYTES,
    project_storage_bytes: storageGiB * GIB,
    workspaces,
    saved_snippets: snippets,
    code_executions_per_day: runs,
    ai_requests_per_day: ai,
    xp_multiplier: xp,
    ads_enabled: ads,
  };
}

export const FALLBACK_PLAN_CATALOG = [
  {
    id: "free",
    title: "Free",
    amount_paise: 0,
    currency: "INR",
    billing: "free",
    description: "A complete foundation for learning and practicing.",
    features: FEATURES_FREE,
    limits: limits({ storageGiB: 1, workspaces: 3, snippets: 10, runs: 50, ai: 0, xp: 1, ads: true }),
  },
  {
    id: "pro",
    title: "Pro",
    amount_paise: 29_900,
    currency: "INR",
    billing: "monthly",
    description: "More structure, analytics and room for projects.",
    features: FEATURES_PRO,
    limits: limits({ storageGiB: 10, workspaces: 25, snippets: 100, runs: 300, ai: 0, xp: 1, ads: true }),
  },
  {
    id: "max",
    title: "Max",
    amount_paise: 69_900,
    currency: "INR",
    billing: "monthly",
    description: "Ad-free learning with advanced projects and AI tools when configured.",
    features: FEATURES_MAX,
    limits: limits({ storageGiB: 50, workspaces: 100, snippets: 500, runs: 1_000, ai: 100, xp: 1.5, ads: false }),
  },
  {
    id: "full_access",
    title: "Full Access",
    amount_paise: 4_999_900,
    currency: "INR",
    billing: "lifetime",
    description: "One-time lifetime access to all standard individual Pro and Max features.",
    features: FEATURES_MAX,
    limits: limits({ storageGiB: 100, workspaces: 200, snippets: 1_000, runs: 1_500, ai: 150, xp: 1.5, ads: false }),
  },
];

const FEATURE_KEYS = Object.keys(FALLBACK_PLAN_CATALOG[0].features);
const LIMIT_KEYS = Object.keys(FALLBACK_PLAN_CATALOG[0].limits);
const isRecord = (value) => value !== null && typeof value === "object" && !Array.isArray(value);

/** Accept the current API response and common previous catalog response shapes. */
export function normalizePlanCatalogPayload(payload) {
  if (Array.isArray(payload)) return payload;
  if (!isRecord(payload)) return [];
  if (Array.isArray(payload.items)) return payload.items;
  if (Array.isArray(payload.plans)) return payload.plans;
  if (isRecord(payload.available_plans)) {
    return Object.entries(payload.available_plans).map(([id, plan]) => ({ id, ...plan }));
  }
  return [];
}

/** True only when every plan supplies all feature and allowance keys. */
export function hasCompletePlanCatalog(items) {
  if (!Array.isArray(items)) return false;
  const byId = new Map(items.filter(isRecord).map((item) => [item.id, item]));
  return FALLBACK_PLAN_CATALOG.every((fallback) => {
    const item = byId.get(fallback.id);
    if (!isRecord(item) || !isRecord(item.features) || !isRecord(item.limits)) return false;
    return FEATURE_KEYS.every((key) => Object.hasOwn(item.features, key))
      && LIMIT_KEYS.every((key) => Object.hasOwn(item.limits, key));
  });
}

/** Merge live values over defaults, filling any missing keys from the fallback catalog. */
export function mergePlanCatalog(items) {
  const liveById = new Map(
    (Array.isArray(items) ? items : [])
      .filter(isRecord)
      .filter((item) => typeof item.id === "string")
      .map((item) => [item.id, item]),
  );

  return FALLBACK_PLAN_CATALOG.map((fallback) => {
    const live = liveById.get(fallback.id) || {};
    return {
      ...fallback,
      ...live,
      features: {
        ...fallback.features,
        ...(isRecord(live.features) ? live.features : {}),
      },
      limits: {
        ...fallback.limits,
        ...(isRecord(live.limits) ? live.limits : {}),
      },
    };
  });
}
