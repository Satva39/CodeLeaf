import assert from "node:assert/strict";
import { apiFetch } from "../src/lib/apiClient.js";

const originalFetch = globalThis.fetch;
const originalDocument = Object.getOwnPropertyDescriptor(globalThis, "document");
const captured = [];
Object.defineProperty(globalThis, "document", {
  configurable: true,
  value: { cookie: "other=x; codeleaf_csrf=csrf-value-123" },
});
globalThis.fetch = async (input, init) => {
  captured.push({ input, init });
  return { ok: true, status: 200 };
};

try {
  await apiFetch("/api/profile", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: "{}" });
  assert.equal(captured[0].init.credentials, "include", "API requests default to credentialed cookies");
  assert.equal(captured[0].init.headers.get("X-CSRF-Token"), "csrf-value-123", "unsafe request includes the CSRF cookie in its header");
  assert.equal(captured[0].init.headers.get("Content-Type"), "application/json", "existing headers are preserved");

  await apiFetch("/api/public/courses");
  assert.equal(captured[1].init.headers.has("X-CSRF-Token"), false, "safe GET requests do not need a CSRF header");

  await apiFetch("/api/logout", { method: "POST", headers: { "X-CSRF-Token": "caller-token" } });
  assert.equal(captured[2].init.headers.get("X-CSRF-Token"), "caller-token", "explicit CSRF headers are preserved");
  console.log("PASS credential defaults and CSRF header handling");
} finally {
  globalThis.fetch = originalFetch;
  if (originalDocument) Object.defineProperty(globalThis, "document", originalDocument);
  else delete globalThis.document;
}
