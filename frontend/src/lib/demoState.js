// Development API calls use Vite's same-origin /api proxy, avoiding browser CORS
// and localhost/127.0.0.1 hostname mismatches. Production may use a separate API origin.
export const API_BASE = (
  import.meta.env.DEV ? "" : (import.meta.env.VITE_API_BASE_URL ?? "")
).replace(/\/$/, "");
const DEMO_KEY = "codeleaf-demo-state-v1";
const FALLBACK_BASE_REWARD = 20;

function safeWindow() {
  return typeof window !== "undefined";
}
function localDateKey(value = new Date()) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
function emitStatsUpdated(changedKeys = []) {
  if (safeWindow()) {
    window.dispatchEvent(
      new CustomEvent("codeleaf:stats-updated", {
        detail: { changedKeys },
      }),
    );
  }
}
function publishRemoteStats(stats) {
  if (safeWindow() && stats && typeof stats === "object") {
    window.dispatchEvent(
      new CustomEvent("codeleaf:stats-updated", {
        detail: { remoteStats: stats },
      }),
    );
  }
}
function publishGuestStats(stats) {
  if (safeWindow() && stats && typeof stats === "object") {
    window.dispatchEvent(
      new CustomEvent("codeleaf:stats-updated", {
        detail: { guestStats: stats },
      }),
    );
  }
}
function readDemo() {
  try {
    return JSON.parse(
      safeWindow() ? localStorage.getItem(DEMO_KEY) || "{}" : "{}",
    );
  } catch {
    return {};
  }
}
function writeDemo(patch) {
  const next = { ...readDemo(), ...patch };
  if (safeWindow()) {
    localStorage.setItem(DEMO_KEY, JSON.stringify(next));
    emitStatsUpdated(Object.keys(patch));
  }
  return next;
}
function getCompleted() {
  return readDemo().completed || [];
}
function getExerciseCompletions() {
  return readDemo().completedExercises || [];
}
function getBookmarks() {
  return readDemo().bookmarks || [];
}
function getProfile() {
  return (
    readDemo().profile || {
      nickname: "Learner",
      handle: "@learner",
      theme: "dark",
      showCertificates: true,
      showProjects: false,
      avatar: "spark",
    }
  );
}
function formatNumber(n) {
  return new Intl.NumberFormat("en-IN").format(Number(n) || 0);
}

function computeStreak(activityDates) {
  const dates = [...new Set((activityDates || []).filter(Boolean))].sort();
  const set = new Set(dates);
  const today = localDateKey();
  const yesterdayDate = new Date();
  yesterdayDate.setDate(yesterdayDate.getDate() - 1);
  const yesterday = localDateKey(yesterdayDate);
  let cursor = set.has(today) ? today : set.has(yesterday) ? yesterday : null;
  let currentStreak = 0;
  while (cursor && set.has(cursor)) {
    currentStreak += 1;
    const d = new Date(`${cursor}T12:00:00`);
    d.setDate(d.getDate() - 1);
    cursor = localDateKey(d);
  }
  let longestStreak = 0;
  let running = 0;
  let prior = null;
  dates.forEach((day) => {
    const d = new Date(`${day}T12:00:00`);
    const expected = new Date(`${prior || day}T12:00:00`);
    expected.setDate(expected.getDate() + 1);
    running = prior && localDateKey(expected) === day ? running + 1 : 1;
    longestStreak = Math.max(longestStreak, running);
    prior = day;
  });
  const activityDays = Array.from({ length: 7 }, (_, index) => {
    const day = new Date();
    day.setDate(day.getDate() - (6 - index));
    const key = localDateKey(day);
    return {
      date: key,
      active: set.has(key),
      label: new Intl.DateTimeFormat("en", { weekday: "short" })
        .format(day)
        .slice(0, 1),
    };
  });
  return { currentStreak, longestStreak, activityDays, activityDates: dates };
}

function getLocalStats() {
  const state = readDemo();
  const events = Array.isArray(state.xpEvents) ? state.xpEvents : [];
  const activityDates = Array.isArray(state.activityDates)
    ? state.activityDates
    : [];
  const streak = computeStreak(activityDates);
  return {
    totalXp: events.reduce(
      (sum, event) => sum + (Number(event.points) || 0),
      0,
    ),
    completedLessons: getCompleted().length,
    completedExercises: getExerciseCompletions().length,
    exercisesAttempted: Number(state.exerciseAttempts || 0),
    bookmarks: getBookmarks().length,
    certificates: Array.isArray(state.certificates)
      ? state.certificates.length
      : 0,
    examsAttempted: Array.isArray(state.examAttempts)
      ? state.examAttempts.length
      : 0,
    examsPassed: Array.isArray(state.examAttempts)
      ? state.examAttempts.filter((attempt) => attempt.passed).length
      : 0,
    currentStreak: streak.currentStreak,
    longestStreak: streak.longestStreak,
    activityDays: streak.activityDays,
    activityDates: streak.activityDates,
    todayActive: streak.activityDates.includes(localDateKey()),
    lessonXp: FALLBACK_BASE_REWARD,
    exerciseXp: FALLBACK_BASE_REWARD,
    isRemote: false,
  };
}

function recordCompletionLocally(kind, id) {
  const state = readDemo();
  const now = new Date();
  const today = localDateKey(now);
  const eventKey = `${kind}:${id}`;
  const events = Array.isArray(state.xpEvents) ? state.xpEvents : [];
  const alreadyCompleted =
    kind === "lesson"
      ? (state.completed || []).includes(id)
      : (state.completedExercises || []).includes(id);
  const alreadyRewarded =
    events.some((event) => event.key === eventKey) || alreadyCompleted;
  // Guest mode uses the platform's base reward only. Subscription boosts are server-verified.
  const points = FALLBACK_BASE_REWARD;
  const nextEvents = alreadyRewarded
    ? events
    : [
        ...events,
        { key: eventKey, kind, id, points, createdAt: now.toISOString() },
      ];
  const activityDates = [
    ...new Set([...(state.activityDates || []), today]),
  ].sort();
  const completed =
    kind === "lesson"
      ? [...new Set([...(state.completed || []), id])]
      : state.completed || [];
  const completedExercises =
    kind === "exercise"
      ? [...new Set([...(state.completedExercises || []), id])]
      : state.completedExercises || [];
  writeDemo({
    xpEvents: nextEvents,
    activityDates,
    completed,
    completedExercises,
  });
  return {
    newlyRewarded: !alreadyRewarded,
    xpAwarded: alreadyRewarded ? 0 : points,
    stats: getLocalStats(),
  };
}

function rememberRemoteCompletion(kind, id) {
  const state = readDemo();
  const completed =
    kind === "lesson"
      ? [...new Set([...(state.completed || []), id])]
      : state.completed || [];
  const completedExercises =
    kind === "exercise"
      ? [...new Set([...(state.completedExercises || []), id])]
      : state.completedExercises || [];
  writeDemo({ completed, completedExercises });
}

function addExerciseAttemptLocally() {
  const state = readDemo();
  writeDemo({ exerciseAttempts: Number(state.exerciseAttempts || 0) + 1 });
}

export {
  readDemo,
  writeDemo,
  getCompleted,
  getExerciseCompletions,
  getBookmarks,
  getProfile,
  formatNumber,
  getLocalStats,
  recordCompletionLocally,
  rememberRemoteCompletion,
  publishRemoteStats,
  publishGuestStats,
  addExerciseAttemptLocally,
  computeStreak,
};
