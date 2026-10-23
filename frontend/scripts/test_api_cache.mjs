import assert from "node:assert/strict";
import { apiGetJson, invalidateApiCache } from "../src/lib/apiCache.js";

const originalFetch = globalThis.fetch;
const pending = [];
globalThis.fetch = (url) => new Promise((resolve, reject) => pending.push({ url, resolve, reject }));
const response = (body) => ({ ok: true, json: async () => body });

try {
  const url = "/api/me/progress";
  const oldRequest = apiGetJson(url, { credentials: "include", ttlMs: 1000 });
  await Promise.resolve();
  assert.equal(pending.length, 1, "first request starts once");

  invalidateApiCache(url);
  const currentRequest = apiGetJson(url, { credentials: "include", ttlMs: 1000 });
  await Promise.resolve();
  assert.equal(pending.length, 2, "invalidating a user-scoped URL permits a fresh request");

  pending[0].resolve(response({ account: "previous-session" }));
  assert.deepEqual(await oldRequest, { account: "previous-session" });
  const followerRequest = apiGetJson(url, { credentials: "include", ttlMs: 1000 });
  assert.equal(pending.length, 2, "late old request does not remove the newer in-flight entry");

  pending[1].resolve(response({ account: "current-session" }));
  assert.deepEqual(await currentRequest, { account: "current-session" });
  assert.deepEqual(await followerRequest, { account: "current-session" });
  assert.deepEqual(await apiGetJson(url, { credentials: "include", ttlMs: 1000 }), { account: "current-session" }, "only the current response is cached");
  console.log("PASS invalidated user-scoped requests cannot clobber newer in-flight requests or cache stale payloads");
} finally {
  globalThis.fetch = originalFetch;
}
