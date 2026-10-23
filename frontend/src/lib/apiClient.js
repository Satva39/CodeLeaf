/** Fetch helper that sends the signed double-submit CSRF token on browser writes. */
function readCookie(name) {
  if (typeof document === "undefined") return "";
  const prefix = `${name}=`;
  const entry = document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith(prefix));
  if (!entry) return "";
  try {
    return decodeURIComponent(entry.slice(prefix.length));
  } catch {
    return entry.slice(prefix.length);
  }
}

export function apiFetch(input, init = {}) {
  const method = String(init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers || {});
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrf = readCookie("codeleaf_csrf");
    if (csrf && !headers.has("X-CSRF-Token")) headers.set("X-CSRF-Token", csrf);
  }
  return fetch(input, {
    ...init,
    headers,
    credentials: init.credentials || "include",
  });
}
