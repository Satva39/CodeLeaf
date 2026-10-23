import assert from "node:assert/strict";
import { Readable, Writable } from "node:stream";
import handler from "../api/proxy/[...path].js";

class MockResponse extends Writable {
  constructor() {
    super();
    this.statusCode = 200;
    this.headers = new Map();
    this.chunks = [];
    this.ended = false;
  }
  _write(chunk, _encoding, callback) {
    this.chunks.push(Buffer.from(chunk));
    callback();
  }
  setHeader(name, value) {
    this.headers.set(name.toLowerCase(), value);
  }
  end(chunk) {
    if (chunk !== undefined) this.chunks.push(Buffer.from(chunk));
    this.ended = true;
    return super.end();
  }
  get body() {
    return Buffer.concat(this.chunks).toString("utf8");
  }
  getHeader(name) {
    return this.headers.get(name.toLowerCase());
  }
}

function request({ method = "GET", url = "/api/proxy/courses?limit=1", path = ["courses"], headers = {}, body = "" } = {}) {
  const stream = Readable.from(body ? [Buffer.from(body)] : []);
  stream.method = method;
  stream.url = url;
  stream.query = { path };
  stream.headers = { host: "codeleaf.test", ...headers };
  return stream;
}

async function invoke(req) {
  const res = new MockResponse();
  await handler(req, res);
  return res;
}

async function main() {
  const originalFetch = globalThis.fetch;
  const originalOrigin = process.env.CODELEAF_API_ORIGIN;
  const originalNodeEnv = process.env.NODE_ENV;
  const fetchCalls = [];
  try {
    globalThis.fetch = async (target, options) => {
      fetchCalls.push({ target: String(target), options });
      return new Response("{\"ok\":true}", {
        status: 201,
        headers: { "content-type": "application/json", "set-cookie": "session=abc; Path=/; HttpOnly" },
      });
    };
    process.env.NODE_ENV = "production";
    delete process.env.CODELEAF_API_ORIGIN;
    const missing = await invoke(request());
    assert.equal(missing.statusCode, 503);
    assert.match(missing.body, /CODELEAF_API_ORIGIN is not configured/);
    assert.equal(fetchCalls.length, 0);
    console.log("PASS missing API origin fails closed with 503 and no upstream request");

    process.env.CODELEAF_API_ORIGIN = "https://api.codeleaf.test/base-path";
    const invalid = await invoke(request());
    assert.equal(invalid.statusCode, 502);
    assert.equal(invalid.body, '{"detail":"API proxy unavailable."}');
    assert.equal(fetchCalls.length, 0);
    console.log("PASS invalid origin is rejected without leaking origin details");

    process.env.CODELEAF_API_ORIGIN = "https://api.codeleaf.test";
    const postBody = '{"lesson":"intro"}';
    const forwarded = await invoke(request({
      method: "POST",
      url: "/api/proxy/courses?mode=preview",
      path: ["courses"],
      headers: { "content-type": "application/json", "content-length": String(Buffer.byteLength(postBody)), cookie: "session=incoming" },
      body: postBody,
    }));
    assert.equal(forwarded.statusCode, 201);
    assert.equal(fetchCalls.length, 1);
    assert.equal(fetchCalls[0].target, "https://api.codeleaf.test/api/courses?mode=preview");
    assert.equal(Buffer.from(fetchCalls[0].options.body).toString("utf8"), postBody);
    assert.equal(fetchCalls[0].options.headers.get("cookie"), "session=incoming");
    assert.equal(fetchCalls[0].options.headers.has("host"), false);
    assert.deepEqual(forwarded.getHeader("set-cookie"), ["session=abc; Path=/; HttpOnly"]);
    assert.equal(forwarded.body, '{"ok":true}');
    console.log("PASS same-origin proxy forwards query/body/cookies and preserves upstream Set-Cookie");

    const unsafe = await invoke(request({ path: ["..", "private"] }));
    assert.equal(unsafe.statusCode, 400);
    assert.equal(unsafe.body, '{"detail":"Invalid API path."}');
    assert.equal(fetchCalls.length, 1);
    console.log("PASS path traversal rejected without making an upstream request");
  } finally {
    globalThis.fetch = originalFetch;
    if (originalOrigin === undefined) delete process.env.CODELEAF_API_ORIGIN;
    else process.env.CODELEAF_API_ORIGIN = originalOrigin;
    if (originalNodeEnv === undefined) delete process.env.NODE_ENV;
    else process.env.NODE_ENV = originalNodeEnv;
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
