import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { apiGetJson, invalidateApiCache } from "../src/lib/apiCache.js";

const originalFetch = globalThis.fetch;
const source = await readFile(new URL("../src/pages/LessonPage.jsx", import.meta.url), "utf8");
let aborted = false;
globalThis.fetch = (_url, options = {}) => new Promise((_resolve, reject) => {
  const signal = options.signal;
  if (!signal) return reject(new Error("Expected timed requests to receive an AbortSignal."));
  signal.addEventListener("abort", () => {
    aborted = true;
    reject(signal.reason || new DOMException("Aborted", "AbortError"));
  }, { once: true });
});

try {
  const url = "/api/courses/html/lessons/timeout-contract-test";
  await assert.rejects(
    apiGetJson(url, { timeoutMs: 30 }),
    /Request timed out after 30 ms\./,
    "a stalled API request should reject with a clear timeout message",
  );
  assert.equal(aborted, true, "the underlying fetch must be aborted");
  assert.match(source, /timeoutMs:\s*12_000/, "lesson content has a bounded 12-second timeout");
  assert.match(source, /setLessonContentError\(/, "lesson errors are retained for display");
  assert.match(source, /typeof error\?\.message === "string"/, "only readable error messages are displayed");
  assert.match(source, /timeoutMs:\s*12_000/, "lesson requests have a bounded timeout");
  assert.match(source, /Retry lesson/, "the learner can retry without reloading the browser");
  invalidateApiCache(url);
  console.log("PASS stalled lesson/API requests are aborted and produce a visible retryable error");
} finally {
  globalThis.fetch = originalFetch;
}
