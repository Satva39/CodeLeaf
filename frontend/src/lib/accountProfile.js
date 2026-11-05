import { apiFetch } from "./apiClient.js";

const API_BASE = (typeof import.meta.env === "object" && import.meta.env
  ? (import.meta.env.DEV ? "" : (import.meta.env.VITE_API_BASE_URL ?? ""))
  : "").replace(/\/$/, "");

const RETRYABLE_STATUS_CODES = new Set([408, 425, 429, 500, 502, 503, 504]);

function abortError() {
  const error = new Error("The account request was cancelled.");
  error.name = "AbortError";
  return error;
}

function waitForRetry(milliseconds, signal) {
  if (signal?.aborted) return Promise.reject(abortError());
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, milliseconds);
    const onAbort = () => {
      clearTimeout(timeout);
      signal?.removeEventListener("abort", onAbort);
      reject(abortError());
    };
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

function isAccountUser(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  return ["id", "email", "username", "display_name"].some((key) => {
    const field = value[key];
    return field !== null && field !== undefined && String(field).trim().length > 0;
  });
}

/** Accept the current { user: ... } API envelope and historical direct-user payloads. */
export function extractAccountUser(payload) {
  const candidates = [
    payload?.user,
    payload?.data?.user,
    payload?.profile,
    payload?.data?.profile,
    payload,
  ];
  return candidates.find(isAccountUser) || null;
}

function responseError(payload, status) {
  const detail = payload?.detail;
  const message = typeof detail === "string" && detail.trim()
    ? detail
    : detail && typeof detail === "object"
      ? [detail.message, detail.detail, detail.error].find((value) => typeof value === "string" && value.trim())
        || `Account request failed with HTTP ${status}.`
      : `Account request failed with HTTP ${status}.`;
  const error = new Error(message);
  error.status = status;
  error.retryable = RETRYABLE_STATUS_CODES.has(status);
  return error;
}

/**
 * Load the signed-in account without reusing a potentially stale short-lived /api/me
 * cache entry. Render cold starts and transient proxy failures are retried safely.
 */
export async function fetchCurrentAccountUser({
  signal,
  onRetry,
  attempts = 3,
  timeoutMs = 35_000,
  retryDelayMs = 1_000,
  fetcher = apiFetch,
  url = `${API_BASE}/api/me`,
} = {}) {
  const maximumAttempts = Math.max(1, Math.min(4, Number(attempts) || 3));
  let lastError = null;

  for (let attempt = 0; attempt < maximumAttempts; attempt += 1) {
    if (signal?.aborted) throw abortError();

    const requestController = new AbortController();
    const forwardAbort = () => requestController.abort();
    signal?.addEventListener("abort", forwardAbort, { once: true });
    const timeout = setTimeout(() => requestController.abort(), timeoutMs);

    try {
      const response = await fetcher(url, {
        method: "GET",
        credentials: "include",
        cache: "no-store",
        headers: { Accept: "application/json" },
        signal: requestController.signal,
      });
      const contentType = response.headers?.get?.("content-type") || "";
      // Parse defensively even when an older proxy omitted the JSON content type.
      // An HTML/empty fallback still becomes null and is rejected below.
      const payload = await response.json().catch(() => null);

      if (response.status === 401) throw responseError(payload, 401);
      if (!response.ok) throw responseError(payload, response.status);

      const user = extractAccountUser(payload);
      if (!user) {
        const error = new Error(
          `The account service returned an unexpected response${contentType ? ` (${contentType})` : ""}. The request was retried automatically.`,
        );
        error.retryable = true;
        throw error;
      }
      return user;
    } catch (error) {
      if (signal?.aborted) throw abortError();
      lastError = requestController.signal.aborted
        ? new Error(`The account service did not respond within ${Math.ceil(timeoutMs / 1000)} seconds.`)
        : error;

      if (lastError.status === 401 || (!lastError.retryable && !(lastError instanceof TypeError) && !requestController.signal.aborted)) {
        throw lastError;
      }
      if (attempt + 1 >= maximumAttempts) throw lastError;
      onRetry?.({ attempt: attempt + 1, attempts: maximumAttempts, error: lastError });
      await waitForRetry(retryDelayMs * (attempt + 1), signal);
    } finally {
      clearTimeout(timeout);
      signal?.removeEventListener("abort", forwardAbort);
    }
  }

  throw lastError || new Error("Account details could not be loaded. Please retry.");
}
