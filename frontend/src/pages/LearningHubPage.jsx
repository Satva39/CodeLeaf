import { useCallback, useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ArrowRight, BrainCircuit, CalendarClock, CheckCircle2, Compass, LockKeyhole, Route, Settings2 } from "lucide-react";
import { EmptyState, PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";

async function getPayload(path, options = {}) {
  const response = await apiFetch(`${API_BASE}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(body.detail || "The learning hub could not be loaded.");
    error.status = response.status;
    throw error;
  }
  return body;
}

export default function LearningHubPage() {
  const location = useLocation();
  const [recommendations, setRecommendations] = useState([]);
  const [due, setDue] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [roadmaps, setRoadmaps] = useState([]);
  const [preferences, setPreferences] = useState({ timezone_name: "Asia/Kolkata", review_frequency_days: 1, daily_review_limit: 10, analytics_enabled: false });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [rec, queue, map, prefs] = await Promise.all([
        getPayload("/api/me/recommendations"),
        getPayload("/api/me/reviews"),
        getPayload("/api/me/roadmaps"),
        getPayload("/api/me/learning-preferences"),
      ]);
      setRecommendations(rec.items || []);
      setDue(queue.due || []);
      setUpcoming(queue.upcoming || []);
      setRoadmaps(map.tracks || []);
      setPreferences(prefs.preferences || preferences);
    } catch (err) {
      setError(err.message || "Learning data is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  // Account settings links directly to this section; wait until the API-backed page
  // has finished loading so the anchor exists before scrolling.
  useEffect(() => {
    if (loading || location.hash !== "#privacy-preferences") return;
    const target = document.getElementById("privacy-preferences");
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      target.focus({ preventScroll: true });
    }
  }, [loading, location.hash]);

  const savePreferences = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice("");
    setError("");
    try {
      const result = await getPayload("/api/me/learning-preferences", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(preferences) });
      setPreferences(result.preferences);
      setNotice("Your review and privacy preferences were saved.");
    } catch (err) {
      setError(err.message || "Preferences could not be saved.");
    } finally {
      setSaving(false);
    }
  };

  const snooze = async (item) => {
    try {
      await getPayload(`/api/me/reviews/${encodeURIComponent(item.id)}/snooze`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ days: 1 }) });
      setDue((items) => items.filter((entry) => entry.id !== item.id));
      setNotice(`“${item.title}” was snoozed for one day.`);
    } catch (err) {
      setError(err.message || "This review could not be snoozed.");
    }
  };

  if (!loading && error && /sign in|session|database is not configured/i.test(error)) {
    return <PageShell><EmptyState icon={LockKeyhole} title="Sign in to use your learning hub" detail={error} action={<Link to="/login" className="button button-primary">Sign in <ArrowRight size={14} /></Link>} /></PageShell>;
  }

  return (
    <PageShell className="phase5-page">
      <div className="phase5-hero panel">
        <div><div className="eyebrow">YOUR NEXT USEFUL STEP</div><h1>Learning hub</h1><p>Recommendations are based on recorded lesson progress, exercise attempts, and review dates. XP is not treated as a mastery score.</p></div>
        <BrainCircuit size={34} aria-hidden="true" />
      </div>
      {error && <p className="phase5-alert" role="alert">{error}</p>}
      {notice && <p className="phase5-notice" role="status">{notice}</p>}
      {loading ? <div className="panel phase5-state">Loading your learning history…</div> : <>
        <section className="panel phase5-section">
          <div className="phase5-section-title"><div><div className="eyebrow">RULE-BASED GUIDANCE</div><h2>Recommended next</h2></div><Compass size={22} /></div>
          {recommendations.length ? <div className="phase5-list">{recommendations.map((item, index) => <article className="phase5-row" key={`${item.kind}-${item.course_slug}-${item.item_slug}-${index}`}>
            <span className="phase5-number">{index + 1}</span><div className="phase5-row-main"><strong>{item.title}</strong><p>{item.reason}</p><small>{item.kind.replaceAll("_", " ")}</small></div><Link className="button button-secondary button-small" to={item.href || "/tutorials"}>Open <ArrowRight size={13} /></Link>
          </article>)}</div> : <p className="phase5-muted">No rule-based recommendation is available yet. Start a published lesson or complete an exercise to create real learning history.</p>}
        </section>
        <section className="panel phase5-section">
          <div className="phase5-section-title"><div><div className="eyebrow">RETRIEVAL PRACTICE</div><h2>Due for review <span className="phase5-count">{due.length}</span></h2></div><CalendarClock size={22} /></div>
          {due.length ? <div className="phase5-list">{due.map((item) => <article className="phase5-row" key={item.id}><div className="phase5-row-main"><strong>{item.title}</strong><p>{item.course_slug} · {item.item_type} · interval {item.interval_days} day(s)</p><small>{item.last_result === "incorrect" ? "Last recorded result: incorrect" : "Scheduled from recorded learning activity"}</small></div><div className="phase5-actions"><Link className="button button-primary button-small" to={item.item_type === "lesson" ? `/learn/${item.course_slug}/${item.item_slug}` : `/practice/${item.course_slug}`}>Review</Link><button className="button button-secondary button-small" type="button" onClick={() => void snooze(item)}>Snooze 1 day</button></div></article>)}</div> : <p className="phase5-muted">Your review queue is clear for now. Correctness and due dates are recorded by the server, not entered manually here.</p>}
          {upcoming.length > 0 && <details className="phase5-upcoming"><summary>Upcoming reviews ({upcoming.length})</summary>{upcoming.map((item) => <p key={item.id}>{item.title} — due {new Date(item.due_at).toLocaleDateString()}</p>)}</details>}
        </section>
        <section className="panel phase5-section">
          <div className="phase5-section-title"><div><div className="eyebrow">SKILL PATHS</div><h2>Career roadmaps</h2></div><Route size={22} /></div>
          <p className="phase5-muted">Roadmap stages use explicit track metadata. A stage is counted complete only when its available published courses have recorded completed lessons; unavailable courses are not counted as progress.</p>
          <div className="phase5-roadmap-grid">{roadmaps.map((track) => <article className="phase5-roadmap-card" key={track.slug}><div className="phase5-roadmap-top"><h3>{track.title}</h3><span>{track.progress_percent}%</span></div><p>{track.summary}</p>{track.outcomes?.length > 0 && <p className="phase5-muted"><strong>Outcomes:</strong> {track.outcomes.join(" · ")}</p>}<div className="phase5-progress-track" role="progressbar" aria-label={`${track.title} required stage completion`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={track.progress_percent}><span style={{ width: `${track.progress_percent}%` }} /></div><small>{track.required_stages_completed} of {track.required_stages_total} required stages recorded complete</small><ol>{track.stages.map((stage) => <li key={stage.slug} className={`phase5-stage phase5-stage-${stage.status}`}><span>{stage.status === "completed" ? <CheckCircle2 size={14} /> : <span className="phase5-stage-dot" />}</span><div><strong>{stage.title}</strong><small>{stage.kind} · {stage.status.replaceAll("_", " ")}</small>{stage.prerequisites?.length > 0 && <small>Prerequisites: {stage.prerequisites.join(", ")}</small>}{stage.missing_course_slugs?.length > 0 && <small>Courses not published yet: {stage.missing_course_slugs.slice(0, 3).join(", ")}</small>}{stage.missing_project_slugs?.length > 0 && <small>Projects not published yet: {stage.missing_project_slugs.slice(0, 3).join(", ")}</small>}{stage.projects_awaiting_submission?.length > 0 && <small>Portfolio submission needed: {stage.projects_awaiting_submission.slice(0, 3).join(", ")}</small>}{stage.module_progress?.length > 0 && <small>Modules: {stage.module_progress.slice(0, 2).map((module) => `${module.title || module.module_slug} (${module.status.replaceAll("_", " ")})`).join(" · ")}</small>}</div></li>)}</ol></article>)}</div>
        </section>
        <section id="privacy-preferences" tabIndex={-1} className="panel phase5-section phase5-privacy-preferences">
          <div className="phase5-section-title"><div><div className="eyebrow">YOUR CONTROL</div><h2>Privacy & learning preferences</h2></div><Settings2 size={22} /></div>
          <form className="phase5-preferences" onSubmit={savePreferences}>
            <label>Timezone <select value={preferences.timezone_name} onChange={(event) => setPreferences((value) => ({ ...value, timezone_name: event.target.value }))}><option value="Asia/Kolkata">Asia/Kolkata (India)</option><option value="UTC">UTC</option><option value="America/New_York">America/New_York</option><option value="Europe/London">Europe/London</option><option value="Asia/Singapore">Asia/Singapore</option></select><small>Review dates are stored as UTC instants; your timezone is saved as a preference.</small></label>
            <label>Review frequency <select value={preferences.review_frequency_days} onChange={(event) => setPreferences((value) => ({ ...value, review_frequency_days: Number(event.target.value) }))}>{[1,2,3,5,7,14,30].map((days) => <option key={days} value={days}>{days} day{days > 1 ? "s" : ""}</option>)}</select></label>
            <label>Daily review limit <select value={preferences.daily_review_limit} onChange={(event) => setPreferences((value) => ({ ...value, daily_review_limit: Number(event.target.value) }))}>{[5,10,15,20,30,50].map((count) => <option key={count} value={count}>{count} items</option>)}</select></label>
            <label className="phase5-checkbox"><input type="checkbox" checked={Boolean(preferences.analytics_enabled)} onChange={(event) => setPreferences((value) => ({ ...value, analytics_enabled: event.target.checked }))} /><span><strong>Allow privacy-minimized product analytics</strong><small>Optional aggregated events only. No account ID, email, IP, submitted code, or answers are stored in the event table.</small></span></label>
            <button className="button button-primary" type="submit" disabled={saving}>{saving ? "Saving…" : "Save preferences"}</button>
          </form>
        </section>
      </>}
    </PageShell>
  );
}
