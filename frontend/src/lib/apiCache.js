import { apiFetch } from "./apiClient.js";
/** In-memory GET cache with in-flight deduplication and optional safe session cache. */
const cache = new Map();
const inFlight = new Map();
let cacheGeneration = 0;
const SESSION_PREFIX = "codeleaf-api-cache-v1:";

function keyFor(url, credentials) {
  return `${credentials || "same-origin"}|${url}`;
}
function safeSessionStorage() {
  try {
    return typeof window !== "undefined" ? window.sessionStorage : null;
  } catch {
    return null;
  }
}
function persistentKey(url) {
  return `${SESSION_PREFIX}${url}`;
}

export class ApiRequestError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.payload = payload;
  }
}

export function peekApiJson(url, credentials = "same-origin", persist = false) {
  const key = keyFor(url, credentials);
  let item = cache.get(key);
  if (item && item.expiresAt <= Date.now()) {
    cache.delete(key);
    item = undefined;
  }
  if (!item && persist) {
    const storage = safeSessionStorage();
    try {
      const saved = storage?.getItem(persistentKey(url));
      item = saved ? JSON.parse(saved) : undefined;
      if (item && item.expiresAt > Date.now()) cache.set(key, item);
      else if (item) {
        storage?.removeItem(persistentKey(url));
        item = undefined;
      }
    } catch {
      item = undefined;
    }
  }
  return item?.value;
}

export function apiGetJson(
  url,
  {
    credentials = "same-origin",
    ttlMs = 0,
    persist = false,
    headers = {},
    timeoutMs = 0,
  } = {},
) {
  const key = keyFor(url, credentials);
  const cached = ttlMs > 0 ? peekApiJson(url, credentials, persist) : undefined;
  if (cached !== undefined) return Promise.resolve(cached);
  const existing = inFlight.get(key);
  if (existing) return existing;
  const generationAtStart = cacheGeneration;
  const controller = timeoutMs > 0 ? new AbortController() : null;
  const timeoutHandle = controller
    ? setTimeout(() => controller.abort(), timeoutMs)
    : null;

  const request = apiFetch(url, {
    method: "GET",
    credentials,
    headers: { Accept: "application/json", ...headers },
    ...(controller ? { signal: controller.signal } : {}),
  })
    .then(async (response) => {
      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        const detail = payload?.detail;
        const message = typeof detail === "string" && detail.trim()
          ? detail
          : detail && typeof detail === "object"
            ? [detail.message, detail.detail, detail.error].find((value) => typeof value === "string" && value.trim())
              || `Request failed with HTTP ${response.status}`
            : `Request failed with HTTP ${response.status}`;
        throw new ApiRequestError(message, response.status, payload);
      }
      if (ttlMs > 0 && generationAtStart === cacheGeneration) {
        const item = { value: payload, expiresAt: Date.now() + ttlMs };
        cache.set(key, item);
        if (persist) {
          const storage = safeSessionStorage();
          try {
            storage?.setItem(persistentKey(url), JSON.stringify(item));
          } catch {
            /* quota/private mode */
          }
        }
      }
      return payload;
    })
    .catch((error) => {
      if (controller?.signal.aborted) {
        throw new Error(`Request timed out after ${timeoutMs} ms.`);
      }
      throw error;
    })
    .finally(() => {
      if (timeoutHandle !== null) clearTimeout(timeoutHandle);
      // An invalidated older request must not clear a newer request registered
      // under the same URL after an account/session transition.
      if (inFlight.get(key) === request) inFlight.delete(key);
    });

  inFlight.set(key, request);
  return request;
}

/** Invalidate cached GETs after a write, or clear all memory/session entries. */
export function invalidateApiCache(urlContains) {
  const storage = safeSessionStorage();
  cacheGeneration += 1;
  if (!urlContains) {
    cache.clear();
    inFlight.clear();
    if (storage) {
      try {
        for (let i = storage.length - 1; i >= 0; i -= 1) {
          const key = storage.key(i);
          if (key?.startsWith(SESSION_PREFIX)) storage.removeItem(key);
        }
      } catch {
        /* storage may be blocked */
      }
    }
    return;
  }
  for (const key of cache.keys()) {
    if (key.includes(urlContains)) cache.delete(key);
  }
  // Do not let new account/session reads share an older in-flight response.
  // The original caller may still receive it, so consumers also guard updates.
  for (const key of inFlight.keys()) {
    if (key.includes(urlContains)) inFlight.delete(key);
  }
  if (storage) {
    try {
      for (let i = storage.length - 1; i >= 0; i -= 1) {
        const key = storage.key(i);
        if (key?.startsWith(SESSION_PREFIX) && key.includes(urlContains))
          storage.removeItem(key);
      }
    } catch {
      /* storage may be blocked */
    }
  }
}
