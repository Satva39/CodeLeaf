import { useEffect, useState } from "react";
import { API_BASE, getCompleted } from "./demoState.js";
import { apiGetJson, invalidateApiCache } from "./apiCache.js";

const initialSnapshot = {
  mode: "loading",
  completedIds: [],
  recentItems: [],
};
let snapshot = initialSnapshot;
let pendingLoad = null;
let progressRevision = 0;
let loadGeneration = 0;
const subscribers = new Set();

function notifySubscribers() {
  subscribers.forEach((notify) => notify(snapshot));
}

export function confirmRemoteLessonCompletion(id) {
  if (!id) return;
  progressRevision += 1;
  invalidateApiCache("/api/me/progress");
  snapshot = {
    mode: "remote",
    completedIds: [...new Set([...(snapshot.completedIds || []), id])],
    recentItems: snapshot.recentItems || [],
  };
  notifySubscribers();
}

export function refreshLearnerProgress() {
  if (pendingLoad) return pendingLoad;
  const revisionAtStart = progressRevision;
  const generationAtStart = loadGeneration;
  const pending = apiGetJson(`${API_BASE}/api/me/progress`, {
    credentials: "include",
    ttlMs: 3_000,
  })
    .then((payload) => {
      if (generationAtStart !== loadGeneration) return snapshot;
      const recentItems = (payload.items || [])
        .filter((item) => item.course_slug && item.lesson_slug && item.last_opened_at)
        .sort((a, b) => String(b.last_opened_at).localeCompare(String(a.last_opened_at)));
      const fetchedSnapshot = {
        mode: "remote",
        recentItems,
        completedIds: (payload.items || [])
          .filter((item) => item.completed)
          .map((item) => `${item.course_slug}:${item.lesson_slug}`),
      };
      if (revisionAtStart !== progressRevision && snapshot.mode === "remote") {
        snapshot = {
          mode: "remote",
          completedIds: [
            ...new Set([
              ...(fetchedSnapshot.completedIds || []),
              ...(snapshot.completedIds || []),
            ]),
          ],
          recentItems: fetchedSnapshot.recentItems || snapshot.recentItems || [],
        };
      } else {
        snapshot = fetchedSnapshot;
      }
    })
    .catch((error) => {
      // Only an explicit unauthenticated response allows guest-local progress.
      // A response started for a previous account/session must never be adopted.
      if (generationAtStart !== loadGeneration || revisionAtStart !== progressRevision) return;
      snapshot =
        error?.status === 401
          ? { mode: "guest", completedIds: getCompleted(), recentItems: [] }
          : { mode: "unavailable", completedIds: [], recentItems: [] };
    })
    .then(() => {
      if (generationAtStart === loadGeneration) notifySubscribers();
      return snapshot;
    })
    .finally(() => {
      if (pendingLoad === pending) pendingLoad = null;
    });
  pendingLoad = pending;
  return pending;
}

/** Use PostgreSQL-backed progress for authenticated learners, local actions for guests. */
export function useLearnerProgress() {
  const [progress, setProgress] = useState(snapshot);

  useEffect(() => {
    const update = (next) => setProgress(next);
    subscribers.add(update);
    if (snapshot.mode === "loading") refreshLearnerProgress();
    else setProgress(snapshot);

    const onLocalChange = (event) => {
      const changedKeys = event?.detail?.changedKeys || [];
      const progressKeys = [
        "completed",
        "completedExercises",
        "xpEvents",
        "activityDates",
      ];
      const isStorageEvent = event?.type === "storage";
      if (
        !isStorageEvent &&
        !changedKeys.some((key) => progressKeys.includes(key))
      )
        return;
      if (snapshot.mode === "guest") {
        snapshot = { mode: "guest", completedIds: getCompleted() };
        notifySubscribers();
        return;
      }
      // The remote completion handler updates this shared snapshot from the
      // server response. Only cross-tab changes need a remote refresh in that mode.
      if (snapshot.mode !== "remote" || isStorageEvent)
        refreshLearnerProgress();
    };
    const onAuthChanged = () => {
      loadGeneration += 1;
      progressRevision += 1;
      snapshot = { mode: "loading", completedIds: [], recentItems: [] };
      notifySubscribers();
      pendingLoad = null;
      invalidateApiCache("/api/me/progress");
      refreshLearnerProgress();
    };
    window.addEventListener("codeleaf:stats-updated", onLocalChange);
    window.addEventListener("storage", onLocalChange);
    window.addEventListener("codeleaf:auth-changed", onAuthChanged);
    return () => {
      subscribers.delete(update);
      window.removeEventListener("codeleaf:stats-updated", onLocalChange);
      window.removeEventListener("storage", onLocalChange);
      window.removeEventListener("codeleaf:auth-changed", onAuthChanged);
    };
  }, []);

  return progress;
}
