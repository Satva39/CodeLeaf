import { useEffect, useState } from "react";
import { API_BASE, getLocalStats } from "./demoState.js";
import { apiGetJson, invalidateApiCache } from "./apiCache.js";

function browserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

function mapRemoteStats(data = {}, rewards = {}) {
  return {
    totalXp: Number(data.total_xp || 0),
    completedLessons: Number(data.completed_lessons || 0),
    completedExercises: Number(data.completed_exercises || 0),
    exercisesAttempted: Number(data.exercises_attempted || 0),
    bookmarks: Number(data.bookmarks || 0),
    certificates: Number(data.certificates || 0),
    examsAttempted: Number(data.exams_attempted || 0),
    examsPassed: Number(data.exams_passed || 0),
    currentStreak: Number(data.current_streak || 0),
    longestStreak: Number(data.longest_streak || 0),
    activityDays: (data.activity_days || []).map((day) => ({
      ...day,
      label: new Date(`${day.date}T12:00:00`)
        .toLocaleDateString(undefined, { weekday: "short" })
        .slice(0, 1),
    })),
    activityDates: data.activity_dates || [],
    todayActive: Boolean(data.today_active),
    lessonXp: Number(data.lesson_xp ?? rewards.lesson ?? 20),
    exerciseXp: Number(data.exercise_xp ?? rewards.exercise ?? 20),
    xpMultiplier: Number(data.xp_multiplier ?? 1),
    isRemote: true,
    mode: "remote",
  };
}

function emptyStats(mode = "loading") {
  return {
    totalXp: 0,
    completedLessons: 0,
    completedExercises: 0,
    exercisesAttempted: 0,
    bookmarks: 0,
    certificates: 0,
    examsAttempted: 0,
    examsPassed: 0,
    currentStreak: 0,
    longestStreak: 0,
    activityDays: [],
    activityDates: [],
    todayActive: false,
    lessonXp: 20,
    exerciseXp: 20,
    xpMultiplier: 1,
    isRemote: false,
    mode,
  };
}

// Keep the latest authoritative result between route changes. Many screens display
// XP; they should subscribe to one snapshot, not flash zeros and refetch on mount.
let sharedStats = emptyStats("loading");
let sharedStatsUpdatedAt = 0;
const STATS_FRESH_MS = 8_000;

function commitStats(setter, next) {
  sharedStats = next;
  sharedStatsUpdatedAt = Date.now();
  setter(next);
}

export function useGamificationStats() {
  const [stats, setStats] = useState(() => sharedStats);

  useEffect(() => {
    let alive = true;
    let requestVersion = 0;
    const load = async (force = false) => {
      if (
        !force &&
        sharedStats.mode !== "loading" &&
        sharedStats.mode !== "unavailable" &&
        Date.now() - sharedStatsUpdatedAt < STATS_FRESH_MS
      ) {
        setStats(sharedStats);
        return;
      }
      const thisRequest = ++requestVersion;
      try {
        // The stats endpoint already includes authoritative reward values. Do not
        // wait for a second /api/public/config request before showing the profile.
        const data = await apiGetJson(
          `${API_BASE}/api/me/stats?timezone=${encodeURIComponent(browserTimezone())}`,
          { credentials: "include", ttlMs: 4_000 },
        );
        if (!alive || thisRequest !== requestVersion) return;
        commitStats(setStats, mapRemoteStats(data));
      } catch (error) {
        if (!alive || thisRequest !== requestVersion) return;
        if (error?.status === 401) {
          // Only an explicit unauthenticated response enables local guest activity.
          commitStats(setStats, {
            ...getLocalStats(),
            xpMultiplier: 1,
            isRemote: false,
            mode: "guest",
          });
        } else {
          commitStats(setStats, emptyStats("unavailable"));
        }
      }
    };
    load();
    const refresh = (event) => {
      if (event?.detail?.remoteStats) {
        // The completion response already includes authoritative post-transaction
        // stats. Render them immediately and invalidate older in-flight requests.
        requestVersion += 1;
        invalidateApiCache("/api/me/stats");
        commitStats(setStats, mapRemoteStats(event.detail.remoteStats));
        return;
      }
      if (event?.detail?.guestStats) {
        // Guest actions are locally recorded by design; publish their computed
        // totals immediately instead of waiting for an unauthenticated API round-trip.
        requestVersion += 1;
        commitStats(setStats, {
          ...event.detail.guestStats,
          lessonXp: Number(event.detail.guestStats.lessonXp ?? 20),
          exerciseXp: Number(event.detail.guestStats.exerciseXp ?? 20),
          xpMultiplier: 1,
          isRemote: false,
          mode: "guest",
        });
        return;
      }
      const changedKeys = event?.detail?.changedKeys || [];
      const statsKeys = new Set([
        "xpEvents",
        "completed",
        "completedExercises",
        "exerciseAttempts",
        "activityDates",
        "bookmarks",
        "certificates",
        "examAttempts",
      ]);
      if (
        event?.type === "storage" ||
        changedKeys.some((key) => statsKeys.has(key))
      ) {
        invalidateApiCache("/api/me/stats");
        if (sharedStats.mode === "guest" && changedKeys.length) {
          commitStats(setStats, {
            ...getLocalStats(),
            xpMultiplier: 1,
            isRemote: false,
            mode: "guest",
          });
        } else if (
          event?.type === "storage" ||
          changedKeys.some((key) =>
            ["bookmarks", "certificates", "examAttempts"].includes(key),
          )
        ) {
          // Lesson/exercise completion immediately publishes server-returned stats;
          // only fetch again for cross-tab changes or other account-stat mutations.
          load(true);
        }
      }
    };
    const onAuthChanged = () => {
      requestVersion += 1;
      invalidateApiCache("/api/me/stats");
      sharedStats = emptyStats("loading");
      sharedStatsUpdatedAt = 0;
      setStats(sharedStats);
      load(true);
    };
    window.addEventListener("codeleaf:stats-updated", refresh);
    window.addEventListener("storage", refresh);
    window.addEventListener("codeleaf:auth-changed", onAuthChanged);
    return () => {
      alive = false;
      window.removeEventListener("codeleaf:stats-updated", refresh);
      window.removeEventListener("storage", refresh);
      window.removeEventListener("codeleaf:auth-changed", onAuthChanged);
    };
  }, []);

  return stats;
}
