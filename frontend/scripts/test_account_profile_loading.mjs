import assert from "node:assert/strict";
import { extractAccountUser, fetchCurrentAccountUser } from "../src/lib/accountProfile.js";

const nestedUser = { id: "user-1", email: "learner@example.test", username: "learner", display_name: "Learner" };
assert.deepEqual(extractAccountUser({ user: nestedUser, stats: { total_xp: 10 } }), nestedUser);
assert.deepEqual(extractAccountUser(nestedUser), nestedUser);
assert.deepEqual(extractAccountUser({ data: { user: nestedUser } }), nestedUser);
assert.equal(extractAccountUser({ status: "ok", items: [] }), null);
console.log("PASS current and legacy account profile response envelopes are normalized safely");

const requestOptions = [];
let attempts = 0;
const recovered = await fetchCurrentAccountUser({
  url: "/api/me",
  attempts: 3,
  timeoutMs: 1_000,
  retryDelayMs: 0,
  fetcher: async (_url, options) => {
    attempts += 1;
    requestOptions.push(options);
    if (attempts === 1) return new Response(JSON.stringify({ detail: "Waking up" }), { status: 503, headers: { "content-type": "application/json" } });
    return new Response(JSON.stringify({ user: nestedUser }), { status: 200, headers: { "content-type": "application/json" } });
  },
});
assert.deepEqual(recovered, nestedUser);
assert.equal(attempts, 2);
assert.equal(requestOptions[0].cache, "no-store");
assert.equal(requestOptions[0].credentials, "include");
console.log("PASS transient service failures retry and profile reads bypass browser caching");

let malformedAttempts = 0;
const fromLegacyResponse = await fetchCurrentAccountUser({
  url: "/api/me",
  attempts: 2,
  timeoutMs: 1_000,
  retryDelayMs: 0,
  fetcher: async () => {
    malformedAttempts += 1;
    return new Response(JSON.stringify(nestedUser), { status: 200 });
  },
});
assert.deepEqual(fromLegacyResponse, nestedUser);
assert.equal(malformedAttempts, 1);
console.log("PASS JSON responses without an explicit content type remain compatible");

let unauthorizedAttempts = 0;
await assert.rejects(
  fetchCurrentAccountUser({
    url: "/api/me",
    attempts: 3,
    retryDelayMs: 0,
    fetcher: async () => {
      unauthorizedAttempts += 1;
      return new Response(JSON.stringify({ detail: "Sign in to continue." }), { status: 401, headers: { "content-type": "application/json" } });
    },
  }),
  (error) => error.status === 401,
);
assert.equal(unauthorizedAttempts, 1);
console.log("PASS unauthenticated sessions are not retried as server failures");
