import { apiFetch } from "./apiClient.js";
import { useEffect, useSyncExternalStore } from "react";
import { API_BASE, getBookmarks, writeDemo } from "./demoState.js";
import { apiGetJson, invalidateApiCache } from "./apiCache.js";

const emptyState = { mode: "idle", ids: [], items: [], error: "" };
let state = emptyState;
let request = null;
let requestVersion = 0;
const subscribers = new Set();

function publish(next) {
  state = next;
  subscribers.forEach((listener) => listener());
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("codeleaf:bookmarks-updated", { detail: { state } }));
  }
}

function localIds() {
  return [...new Set(getBookmarks().filter((item) => typeof item === "string"))];
}

function itemKey(item) {
  return `${item.course_slug}:${item.lesson_slug}`;
}

export function getBookmarkSnapshot() {
  return state;
}

export function subscribeBookmarkState(listener) {
  subscribers.add(listener);
  return () => subscribers.delete(listener);
}

export function useBookmarkState() {
  const snapshot = useSyncExternalStore(subscribeBookmarkState, getBookmarkSnapshot, getBookmarkSnapshot);
  useEffect(() => { void loadBookmarkState(); }, []);
  return snapshot;
}

export function loadBookmarkState({ force = false } = {}) {
  if (request) return request;
  if (!force && state.mode !== "idle" && state.mode !== "unavailable") return Promise.resolve(state);
  publish({ ...state, mode: "loading", error: "" });
  const version = ++requestVersion;
  const pending = apiGetJson(`${API_BASE}/api/me/bookmarks`, {
    credentials: "include",
    ttlMs: 30_000,
  })
    .then((payload) => {
      if (version !== requestVersion) return state;
      const items = Array.isArray(payload?.items) ? payload.items : [];
      publish({
        mode: "remote",
        items,
        ids: [...new Set(items.filter((item) => item?.course_slug && item?.lesson_slug).map(itemKey))],
        error: "",
      });
      return state;
    })
    .catch((error) => {
      if (version !== requestVersion) return state;
      if (error?.status === 401) {
        publish({ mode: "guest", ids: localIds(), items: [], error: "" });
      } else {
        publish({ mode: "unavailable", ids: [], items: [], error: error?.message || "Bookmarks could not be loaded." });
      }
      return state;
    })
    .finally(() => {
      if (request === pending) request = null;
    });
  request = pending;
  return pending;
}

function localToggle(id, currentlySaved) {
  const current = localIds();
  const next = currentlySaved ? current.filter((item) => item !== id) : [...new Set([...current, id])];
  writeDemo({ bookmarks: next });
  publish({ mode: "guest", ids: next, items: [], error: "" });
  return { saved: !currentlySaved, mode: "guest" };
}

export async function toggleBookmarkKey(id) {
  const [courseSlug, lessonSlug] = String(id).split(":");
  if (!courseSlug || !lessonSlug) throw new Error("This bookmark link is invalid.");
  let currentState = state;
  if (currentState.mode === "idle" || currentState.mode === "loading" || currentState.mode === "unavailable") {
    currentState = await loadBookmarkState({ force: currentState.mode === "unavailable" });
  }
  const currentlySaved = (currentState.mode === "remote" ? currentState.ids : localIds()).includes(id);

  if (currentState.mode === "remote") {
    const response = await apiFetch(
      `${API_BASE}/api/me/bookmarks/${encodeURIComponent(courseSlug)}/${encodeURIComponent(lessonSlug)}`,
      { method: currentlySaved ? "DELETE" : "PUT", credentials: "include" },
    );
    if (response.status === 401) {
      invalidateApiCache("/api/me/bookmarks");
      return localToggle(id, currentlySaved);
    }
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || "Bookmark could not be synchronized.");
    const saved = !currentlySaved;
    const ids = saved
      ? [...new Set([...currentState.ids, id])]
      : currentState.ids.filter((item) => item !== id);
    const items = saved
      ? [...currentState.items.filter((item) => itemKey(item) !== id), { course_slug: courseSlug, lesson_slug: lessonSlug, title: lessonSlug.replaceAll("-", " ") }]
      : currentState.items.filter((item) => itemKey(item) !== id);
    invalidateApiCache("/api/me/bookmarks");
    publish({ mode: "remote", ids, items, error: "" });
    return { saved, mode: "remote" };
  }

  if (currentState.mode === "guest") return localToggle(id, currentlySaved);
  throw new Error(currentState.error || "Bookmarks are temporarily unavailable. Please try again.");
}

export function resetBookmarkState() {
  // Invalidate pending responses too; a former account's late response must not
  // overwrite the state after a sign-in/sign-out transition.
  requestVersion += 1;
  invalidateApiCache("/api/me/bookmarks");
  request = null;
  publish({ ...emptyState, ids: [], items: [] });
}
