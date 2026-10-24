import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  CalendarClock,
  CheckCircle2,
  Clock3,
  RefreshCw,
  Settings2,
  Sparkles,
} from "lucide-react";
import { API_BASE } from "../lib/demoState.js";
import { apiFetch } from "../lib/apiClient.js";
import { buildReviewLessonHref, formatReviewDueDate } from "../lib/reviewSchedule.js";
import { EmptyState, PageShell } from "../components/common.jsx";
import "../styles/phase3-review.css";

async function readJson(response, fallback) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.detail || fallback);
    error.status = response.status;
    throw error;
  }
  return payload;
}

function ReviewCard({ item, upcoming = false, busyId, onSnooze }) {
  const icon = item.item_type === "exercise" ? <Sparkles size={18} /> : <BookOpen size={18} />;
  return (
    <article className={`phase3-review-card${upcoming ? " is-upcoming" : ""}`}>
      <div className="phase3-review-card-icon" aria-hidden="true">{icon}</div>
      <div className="phase3-review-card-copy">
        <div className="phase3-review-meta">
          <span>{item.item_type === "exercise" ? "EXERCISE REVIEW" : "LESSON REVIEW"}</span>
          <span>{upcoming ? formatReviewDueDate(item.due_at) : "READY TO REVIEW"}</span>
        </div>
        <h3>{item.title || String(item.item_slug || "Review item").replaceAll("-", " ")}</h3>
        <p>{item.item_type === "exercise"
          ? "Revisit the lesson and recall the reasoning behind this exercise before trying it again."
          : "Revisit the key idea, then rate how well you could recall it without relying on the explanation."}</p>
        <small>{item.course_slug} · {item.repetitions || 0} successful review interval{item.repetitions === 1 ? "" : "s"}</small>
      </div>
      <div className="phase3-review-card-actions">
        {!upcoming ? (
          <>
            <Link className="button button-primary button-small" to={buildReviewLessonHref(item)}>
              Review now <ArrowRight size={14} />
            </Link>
            <button type="button" className="button button-quiet button-small" onClick={() => onSnooze(item.id)} disabled={busyId === item.id}>
              <Clock3 size={13} /> {busyId === item.id ? "Snoozing…" : "Remind tomorrow"}
            </button>
          </>
        ) : (
          <Link className="button button-secondary button-small" to={item.item_type === "exercise" && item.lesson_slug ? `/learn/${encodeURIComponent(item.course_slug)}/${encodeURIComponent(item.lesson_slug)}` : `/learn/${encodeURIComponent(item.course_slug)}/${encodeURIComponent(item.item_slug)}`}>
            Preview <ArrowRight size={14} />
          </Link>
        )}
      </div>
    </article>
  );
}

export default function ReviewPage() {
  const [mode, setMode] = useState("loading");
  const [queue, setQueue] = useState({ due: [], upcoming: [], daily_limit: 10, timezone_name: "UTC" });
  const [preferences, setPreferences] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState("");
  const [saving, setSaving] = useState(false);

  const loadQueue = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) setMode("loading");
    setError("");
    try {
      const queueResponse = await apiFetch(`${API_BASE}/api/me/reviews`, {
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      const queuePayload = await readJson(queueResponse, "Your review queue could not be loaded.");
      setQueue({
        due: Array.isArray(queuePayload.due) ? queuePayload.due : [],
        upcoming: Array.isArray(queuePayload.upcoming) ? queuePayload.upcoming : [],
        daily_limit: Number(queuePayload.daily_limit || 10),
        timezone_name: queuePayload.timezone_name || "UTC",
      });
      setPreferences(queuePayload.preferences || null);
      setMode("ready");
    } catch (loadError) {
      if (loadError?.status === 401) {
        setMode("guest");
        setError("");
      } else {
        setMode("unavailable");
        setError(loadError.message || "Review data is temporarily unavailable.");
      }
    }
  }, []);

  useEffect(() => { void loadQueue(); }, [loadQueue]);

  async function snooze(id) {
    setBusyId(id);
    setError("");
    setNotice("");
    try {
      const response = await apiFetch(`${API_BASE}/api/me/reviews/${encodeURIComponent(id)}/snooze`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ days: 1 }),
      });
      await readJson(response, "This review could not be snoozed.");
      setNotice("Moved to tomorrow. Take the pace that works for you.");
      await loadQueue({ quiet: true });
    } catch (actionError) {
      setError(actionError.message || "This review could not be snoozed.");
    } finally {
      setBusyId("");
    }
  }

  async function savePreferences(event) {
    event.preventDefault();
    if (!preferences || saving) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const body = {
        timezone_name: preferences.timezone_name || queue.timezone_name || "UTC",
        review_frequency_days: Math.min(30, Math.max(1, Number(preferences.review_frequency_days) || 1)),
        daily_review_limit: Math.min(50, Math.max(1, Number(preferences.daily_review_limit) || 10)),
        analytics_enabled: Boolean(preferences.analytics_enabled),
      };
      const response = await apiFetch(`${API_BASE}/api/me/learning-preferences`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(body),
      });
      const payload = await readJson(response, "Review preferences could not be saved.");
      setPreferences(payload.preferences || body);
      setNotice("Review preferences saved.");
      await loadQueue({ quiet: true });
    } catch (saveError) {
      setError(saveError.message || "Review preferences could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <PageShell className="phase3-review-page">
      <section className="phase3-review-hero panel">
        <div className="phase3-review-hero-icon"><CalendarClock size={28} /></div>
        <div className="phase3-review-hero-copy">
          <span className="eyebrow">RETRIEVAL PRACTICE</span>
          <h1>Review what you've learned</h1>
          <p>Short, spaced reviews help you revisit concepts. Your queue is based on recorded lesson completions and server-graded exercise attempts—not page views or guessed mastery.</p>
        </div>
        <div className="phase3-review-hero-count"><strong>{mode === "ready" ? queue.due.length : "—"}</strong><span>due today</span></div>
      </section>

      {notice && <div className="phase3-review-notice" role="status"><CheckCircle2 size={17} />{notice}</div>}
      {error && <div className="phase3-review-error" role="alert">{error}<button className="button button-secondary button-small" type="button" onClick={() => void loadQueue()}><RefreshCw size={13} /> Retry</button></div>}

      {mode === "loading" && <div className="panel collection-state" role="status" aria-busy="true">Loading your account review schedule…</div>}
      {mode === "guest" && (
        <EmptyState icon={CalendarClock} title="Sign in to use your review queue" detail="Review schedules are saved to your CodeLeaf account so they can follow you across devices. Guest activity is not presented as synced review history." action={<Link to="/login" className="button button-primary">Sign in to continue <ArrowRight size={14} /></Link>} />
      )}
      {mode === "unavailable" && (
        <EmptyState icon={RefreshCw} title="Review queue unavailable" detail={`${error || "We couldn't retrieve your review schedule."} Check that the Phase 5 review endpoints and database migration are deployed, then retry.`} action={<button type="button" className="button button-secondary" onClick={() => void loadQueue()}><RefreshCw size={14} /> Retry</button>} />
      )}
      {mode === "ready" && (
        <>
          <section className="phase3-review-section">
            <div className="phase3-review-section-heading"><div><span className="eyebrow">YOUR NEXT STEPS</span><h2>Due reviews <span className="phase3-review-count">{queue.due.length}</span></h2></div><p>Open the lesson, actively recall the key idea, then choose an honest rating to set the next interval.</p></div>
            {queue.due.length ? <div className="phase3-review-list">{queue.due.map((item) => <ReviewCard key={item.id} item={item} busyId={busyId} onSnooze={snooze} />)}</div> : (
              <div className="phase3-review-empty panel"><CheckCircle2 size={25} /><div><h3>You're all caught up</h3><p>No reviews are due right now. You can continue learning or come back when your next review is scheduled.</p><Link to="/tutorials" className="button button-secondary">Continue learning <ArrowRight size={14} /></Link></div></div>
            )}
          </section>

          {queue.upcoming.length > 0 && <section className="phase3-review-section"><div className="phase3-review-section-heading"><div><span className="eyebrow">PLANNED NEXT</span><h2>Coming up</h2></div><p>These items aren't due yet; their dates will update after a review.</p></div><div className="phase3-review-list">{queue.upcoming.map((item) => <ReviewCard key={item.id} item={item} upcoming />)}</div></section>}

          {preferences && <section className="phase3-review-preferences panel"><div className="phase3-review-preferences-title"><Settings2 size={20} /><div><h2>Review preferences</h2><p>Set a daily pace that feels manageable. You can change this at any time.</p></div></div><form onSubmit={savePreferences} className="phase3-review-preferences-form">
            <label>First review interval (days)<span>How soon a new item returns</span><input type="number" min="1" max="30" value={preferences.review_frequency_days ?? 1} onChange={(event) => setPreferences((current) => ({ ...current, review_frequency_days: event.target.value }))} /></label>
            <label>Daily review limit<span>Maximum items in the due list</span><input type="number" min="1" max="50" value={preferences.daily_review_limit ?? 10} onChange={(event) => setPreferences((current) => ({ ...current, daily_review_limit: event.target.value }))} /></label>
            <button type="submit" className="button button-primary" disabled={saving}>{saving ? "Saving…" : "Save preferences"} <ArrowRight size={14} /></button>
          </form></section>}
        </>
      )}
    </PageShell>
  );
}
