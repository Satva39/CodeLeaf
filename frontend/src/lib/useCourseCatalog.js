import { useEffect, useState } from "react";
import { COURSE_CATALOG } from "../data.js";
import { mapAuthoritativeCourseCatalog } from "./courseCatalogFilters.js";
import { API_BASE } from "./demoState.js";
import { apiGetJson } from "./apiCache.js";

const CATALOG_URL = `${API_BASE}/api/courses`;
let catalogSnapshot = {
  courses: COURSE_CATALOG,
  loading: true,
  error: false,
  updatedAt: 0,
};
let catalogPromise = null;
const listeners = new Set();

function notifyCatalog() {
  listeners.forEach((listener) => listener(catalogSnapshot));
}

function mergeCatalog(payload) {
  if (!Array.isArray(payload?.items))
    throw new Error("Course catalog response is invalid.");
  // The API is authoritative for catalog membership and status. Static metadata
  // is used only for presentation fallback fields such as course logo/color.
  const courses = mapAuthoritativeCourseCatalog(payload.items, COURSE_CATALOG);
  catalogSnapshot = {
    courses,
    loading: false,
    error: false,
    updatedAt: Date.now(),
  };
  notifyCatalog();
}

function loadCatalog() {
  if (catalogPromise) return catalogPromise;
  catalogSnapshot = { ...catalogSnapshot, loading: true, error: false };
  notifyCatalog();
  catalogPromise = apiGetJson(CATALOG_URL, { ttlMs: 30_000, persist: true })
    .then(mergeCatalog)
    .catch(() => {
      catalogSnapshot = {
        courses: COURSE_CATALOG,
        loading: false,
        error: true,
        updatedAt: Date.now(),
      };
      notifyCatalog();
    })
    .finally(() => {
      catalogPromise = null;
    });
  return catalogPromise;
}

/** Shared catalog state: concurrent consumers and StrictMode mounts use one request. */
export function useCourseCatalogState() {
  const [state, setState] = useState(catalogSnapshot);
  useEffect(() => {
    const subscribe = (next) => setState(next);
    listeners.add(subscribe);
    setState(catalogSnapshot);
    if (
      catalogSnapshot.loading ||
      catalogSnapshot.error ||
      Date.now() - catalogSnapshot.updatedAt > 30_000
    )
      loadCatalog();
    return () => listeners.delete(subscribe);
  }, []);
  return state;
}

/** Backwards-compatible convenience hook for components that only need the list. */
export function useCourseCatalog() {
  return useCourseCatalogState().courses;
}
