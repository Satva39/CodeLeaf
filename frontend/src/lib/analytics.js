import { apiFetch } from "./apiClient.js";
import { API_BASE } from "./demoState.js";

const ALLOWED = new Set([
  "course_start", "course_completion", "exercise_attempt", "exercise_incorrect",
  "lesson_dropoff", "broken_asset", "project_completion", "lesson_completion",
]);

// The backend checks the learner's explicit opt-in and never persists this event
// with an account ID, raw IP, answer, email, source code or arbitrary payload.
export function recordAnalyticsEvent(event) {
  if (!event || !ALLOWED.has(event.event_type)) return Promise.resolve(false);
  return apiFetch(`${API_BASE}/api/me/analytics/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_type: event.event_type,
      course_slug: event.course_slug || null,
      lesson_slug: event.lesson_slug || null,
      item_key: event.item_key || null,
      outcome: event.outcome || null,
    }),
  }).then((response) => response.ok).catch(() => false);
}
