import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

// Preserve raw request bytes for webhook signature verification and other APIs.
export const config = { api: { bodyParser: false } };

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

function configuredApiOrigin() {
  const configured = process.env.CODELEAF_API_ORIGIN;
  if (!configured) throw new Error("CODELEAF_API_ORIGIN is not configured.");
  const parsed = new URL(configured);
  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    parsed.username ||
    parsed.password ||
    parsed.pathname !== "/" ||
    parsed.search ||
    parsed.hash
  ) {
    throw new Error("CODELEAF_API_ORIGIN must be an origin URL without credentials or a path.");
  }
  if (process.env.NODE_ENV === "production" && parsed.protocol !== "https:") {
    throw new Error("CODELEAF_API_ORIGIN must use HTTPS in production.");
  }
  return parsed.origin;
}

function forwardedPath(req) {
  const raw = req.query?.path;
  const segments = Array.isArray(raw) ? raw : raw ? [raw] : [];
  if (
    segments.some(
      (segment) =>
        typeof segment !== "string" ||
        !segment ||
        segment === "." ||
        segment === ".." ||
        segment.includes("\\") ||
        segment.includes("\0"),
    )
  ) {
    throw new Error("Invalid API path.");
  }
  return segments.map((segment) => encodeURIComponent(segment)).join("/");
}

async function readRawBody(req) {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}

export default async function handler(req, res) {
  try {
    const origin = configuredApiOrigin();
    const path = forwardedPath(req);
    const incoming = new URL(req.url || "/", `https://${req.headers.host || "localhost"}`);
    const target = new URL(path ? `/api/${path}` : "/api", origin);
    target.search = incoming.search;

    const headers = new Headers();
    for (const [name, value] of Object.entries(req.headers || {})) {
      const lowerName = name.toLowerCase();
      if (HOP_BY_HOP_HEADERS.has(lowerName) || value == null) continue;
      headers.set(lowerName, Array.isArray(value) ? value.join(", ") : String(value));
    }
    // Let fetch negotiate its own response encoding; response bytes may be decoded by it.
    headers.delete("accept-encoding");

    const method = String(req.method || "GET").toUpperCase();
    const body = method === "GET" || method === "HEAD" ? undefined : await readRawBody(req);
    if (body?.length) headers.set("content-length", String(body.length));
    else headers.delete("content-length");

    const upstream = await fetch(target, {
      method,
      headers,
      body,
      redirect: "manual",
    });

    res.statusCode = upstream.status;
    for (const [name, value] of upstream.headers) {
      const lowerName = name.toLowerCase();
      if (HOP_BY_HOP_HEADERS.has(lowerName) || lowerName === "set-cookie") continue;
      res.setHeader(name, value);
    }
    const cookies = upstream.headers.getSetCookie?.() || [];
    if (cookies.length) res.setHeader("set-cookie", cookies);

    if (method === "HEAD" || !upstream.body) {
      res.end();
      return;
    }
    await pipeline(Readable.fromWeb(upstream.body), res);
  } catch (error) {
    // Do not expose target URLs, credentials, request bodies, or upstream error details.
    if (res.headersSent) {
      res.destroy();
      return;
    }
    const missingConfiguration =
      error instanceof Error && error.message === "CODELEAF_API_ORIGIN is not configured.";
    const invalidPath = error instanceof Error && error.message === "Invalid API path.";
    res.statusCode = missingConfiguration ? 503 : invalidPath ? 400 : 502;
    res.setHeader("content-type", "application/json; charset=utf-8");
    res.end(JSON.stringify({
      detail: missingConfiguration
        ? error.message
        : invalidPath
          ? "Invalid API path."
          : "API proxy unavailable.",
    }));
  }
}
