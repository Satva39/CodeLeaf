import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, Award, CheckCircle2, Clock3, ListChecks, ShieldCheck, XCircle } from "lucide-react";
import { COURSE_CATALOG } from "../data.js";
import { API_BASE } from "../lib/demoState.js";
import { apiFetch } from "../lib/apiClient.js";
import { CourseIcon, EmptyState, PageShell } from "../components/common.jsx";

async function requestJson(path, options = {}) {
  const response = await apiFetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    const error = new Error(typeof detail === "string" ? detail : (detail?.message || "The practical exam request could not be completed."));
    error.status = response.status;
    error.code = typeof detail === "object" ? detail?.code : undefined;
    throw error;
  }
  return payload;
}

export default function PracticalExamPage() {
  const { examSlug = "html" } = useParams();
  const course = COURSE_CATALOG.find((item) => item.slug === examSlug) || COURSE_CATALOG[0];
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setInfo(null); setAttempt(null); setAnswers({}); setResult(null);
    setLoading(true); setError("");
    requestJson(`/api/courses/${encodeURIComponent(examSlug)}/practical-exam`, { signal: controller.signal })
      .then(setInfo)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message || "The practical exam is unavailable.");
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [examSlug]);

  const tasks = Array.isArray(attempt?.tasks) ? attempt.tasks : [];
  const answeredCount = useMemo(() => tasks.filter((task) => String(answers[task.id] || "").trim()).length, [answers, tasks]);

  async function startPractical() {
    setBusy(true); setError("");
    try {
      const created = await requestJson(`/api/courses/${encodeURIComponent(examSlug)}/practical-exam/start`, { method: "POST", body: "{}" });
      setAttempt(created);
      setAnswers({});
      setResult(null);
    } catch (err) {
      setError(err.message || "Could not start the practical assessment.");
    } finally {
      setBusy(false);
    }
  }

  async function submitPractical() {
    if (!attempt || answeredCount !== tasks.length) return;
    setBusy(true); setError("");
    try {
      const submitted = await requestJson(`/api/me/practical-exams/${encodeURIComponent(attempt.attempt_id)}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      setResult(submitted);
    } catch (err) {
      setError(err.message || "Could not submit the practical assessment.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <PageShell className="narrow-page"><div className="panel collection-state">Loading {course.title} practical assessment…</div></PageShell>;

  if (error && !info && !attempt) {
    return (
      <PageShell className="narrow-page">
        <EmptyState
          icon={ShieldCheck}
          title="Practical exam unavailable"
          detail={`${error} The practical stage must be published and the MCQ exam must be passed before it can be taken.`}
          action={<Link to={`/exam/${encodeURIComponent(examSlug)}`} className="button button-primary">Back to MCQ exam</Link>}
        />
      </PageShell>
    );
  }

  if (result) {
    const passed = Boolean(result.passed);
    return (
      <PageShell className="narrow-page">
        <div className="exam-result-card panel">
          <span className={`result-big-icon ${passed ? "passed" : "not-passed"}`}>{passed ? <CheckCircle2 size={29} /> : <XCircle size={29} />}</span>
          <div className="eyebrow">SERVER-GRADED PRACTICAL RESULT</div>
          <h1>{passed ? "Practical assessment passed" : "Practical assessment not passed"}</h1>
          <p>You scored {result.score_percent}% against a passing threshold of {result.pass_percent}%.</p>
          <div className="certificate-proof panel">
            {result.certificate ? <Award size={23} /> : <ShieldCheck size={23} />}
            <div><strong>{result.certificate ? "Verified certificate issued" : "Certificate status"}</strong><small>{result.certificate ? `Credential ID · ${result.certificate.public_id}` : result.certificate_message || "Both exam stages and all prerequisites must pass before certification."}</small></div>
            <span className={`pill ${result.certificate ? "pill-mint" : "pill-neutral"}`}>{result.certificate_status || "not_issued"}</span>
          </div>
          <section className="exam-answer-review">
            <h2>Task results</h2>
            {(result.results || []).map((item, index) => (
              <article className="exam-answer-review-item" key={item.task_id}>
                <h3>{index + 1}. {item.title}</h3>
                <p>{item.is_correct ? "Accepted" : "Not accepted"} · {item.points_earned} / {item.points_possible} points</p>
                {item.feedback && <p>{item.feedback}</p>}
              </article>
            ))}
          </section>
          <div className="hero-actions">
            <Link className="button button-primary" to="/certificates">View certificates</Link>
            {!passed && <Link className="button button-secondary" to={`/practical/${encodeURIComponent(examSlug)}`}>Retry practical exam</Link>}
          </div>
        </div>
      </PageShell>
    );
  }

  if (!attempt) {
    return (
      <PageShell className="narrow-page">
        <div className="exam-start-card panel">
          <span className="exam-large-icon"><CourseIcon course={course} /></span>
          <div className="eyebrow">MANDATORY CERTIFICATION STAGE 2</div>
          <h1>{info?.title || `${course.title} Practical Assessment`}</h1>
          <p>This intermediate-level practical assessment becomes available only after the MCQ stage has been passed. The server grades every task and checks eligibility again before issuing a certificate.</p>
          <div className="exam-start-stats">
            <span><ListChecks size={16} /> {info?.task_count || 0} tasks</span>
            <span><Clock3 size={16} /> Intermediate level</span>
            <span><ShieldCheck size={16} /> Pass: {info?.pass_percent || 70}%</span>
          </div>
          <div className="notice-box"><ShieldCheck size={17} /><p>Each task is scored by its published server-side grader. Client-side scores and completion flags are not accepted.</p></div>
          <section className="exam-answer-review">
            <h2>Assessment tasks</h2>
            {(info?.tasks || []).map((task, index) => (
              <article className="exam-answer-review-item" key={task.id}>
                <h3>{index + 1}. {task.title}</h3>
                <p>{task.prompt}</p>
                {task.rubric?.length > 0 && <ul>{task.rubric.map((item, rubricIndex) => <li key={`${task.id}-${rubricIndex}`}>{item}</li>)}</ul>}
              </article>
            ))}
          </section>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary button-wide" disabled={busy || !(info?.task_count > 0)} onClick={startPractical}>{busy ? "Starting…" : "Begin practical exam"} <ArrowRight size={16} /></button>
          <Link className="text-link center-link" to="/certificates">Back to certificates</Link>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell className="narrow-page">
      <div className="exam-question-card panel">
        <div className="exam-question-topline"><span>Practical assessment · {tasks.length} tasks</span><span>{answeredCount} answered</span></div>
        <div className="exam-progress-track"><span style={{ width: `${answeredCount * 100 / Math.max(1, tasks.length)}%` }} /></div>
        <div className="eyebrow">{attempt.title || info?.title}</div>
        <h1>Complete each task</h1>
        {tasks.map((task, index) => (
          <section className="exam-answer-review-item" key={task.id}>
            <h2>{index + 1}. {task.title}</h2>
            <p>{task.prompt}</p>
            {task.starter && <pre><code>{task.starter}</code></pre>}
            {task.rubric?.length > 0 && <ul>{task.rubric.map((item, rubricIndex) => <li key={`${task.id}-${rubricIndex}`}>{item}</li>)}</ul>}
            <label className="exercise-answer-label">
              <span>Your submission</span>
              <textarea
                rows={6}
                spellCheck="false"
                value={answers[task.id] || ""}
                onChange={(event) => setAnswers((previous) => ({ ...previous, [task.id]: event.target.value }))}
                placeholder="Write your task response…"
                aria-label={`Submission for ${task.title}`}
              />
            </label>
          </section>
        ))}
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="exam-question-actions">
          <button className="button button-secondary" onClick={() => setAttempt(null)} disabled={busy}>Back to instructions</button>
          <button className="button button-primary" disabled={busy || answeredCount !== tasks.length} onClick={submitPractical}>{busy ? "Submitting…" : "Submit practical exam"} <CheckCircle2 size={16} /></button>
        </div>
        {answeredCount !== tasks.length && <p className="exam-unanswered-note">Complete every task before submitting ({tasks.length - answeredCount} remaining).</p>}
      </div>
      <Link className="text-link center-link" to="/certificates">Exit to certificates</Link>
    </PageShell>
  );
}
