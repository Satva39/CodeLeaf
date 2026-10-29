import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, CheckCircle2, Clock3, Crown, ListChecks, ShieldCheck, XCircle } from "lucide-react";
import { PageShell, EmptyState } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";

async function requestJson(path, options = {}) {
  const response = await apiFetch(`${API_BASE}${path}`, {
    credentials: "include", ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    const error = new Error(typeof detail === "string" ? detail : detail?.message || "The mock assessment request failed.");
    error.status = response.status;
    error.code = typeof detail === "object" ? detail?.code : undefined;
    throw error;
  }
  return payload;
}

function formatTime(seconds) {
  const safe = Math.max(0, Number(seconds) || 0);
  return `${Math.floor(safe / 60).toString().padStart(2, "0")}:${Math.floor(safe % 60).toString().padStart(2, "0")}`;
}

export default function MockExamPage() {
  const { examSlug = "html" } = useParams();
  const navigate = useNavigate();
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(null);
  const [answers, setAnswers] = useState({});
  const [index, setIndex] = useState(0);
  const [report, setReport] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [remaining, setRemaining] = useState(20 * 60);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setInfo(null); setAttempt(null); setReport(null); setError(""); setAnswers({});
    requestJson(`/api/courses/${encodeURIComponent(examSlug)}/mock-exam`, { signal: controller.signal })
      .then(setInfo)
      .catch((err) => { if (err.name !== "AbortError") setError(err.message || "Mock assessment information is unavailable."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [examSlug]);

  const questions = Array.isArray(attempt?.questions) ? attempt.questions : [];
  const current = questions[index];
  const answeredCount = useMemo(() => questions.filter((question) => answers[question.id]).length, [answers, questions]);

  useEffect(() => {
    if (!attempt?.expires_at || report) return undefined;
    const update = () => setRemaining(Math.max(0, Math.ceil((new Date(attempt.expires_at).getTime() - Date.now()) / 1000)));
    update();
    const timer = window.setInterval(update, 500);
    return () => window.clearInterval(timer);
  }, [attempt?.expires_at, report]);

  async function startAttempt() {
    setBusy(true); setError("");
    try {
      const created = await requestJson(`/api/courses/${encodeURIComponent(examSlug)}/mock-exam/start`, { method: "POST", body: "{}" });
      setAttempt(created); setAnswers({}); setIndex(0); setReport(null);
      setRemaining(Math.max(0, Math.ceil((new Date(created.expires_at).getTime() - Date.now()) / 1000)));
    } catch (err) {
      if (err.status === 401) navigate(`/login?next=${encodeURIComponent(`/mock-exam/${examSlug}`)}`);
      else setError(err.message || "Could not start the mock assessment.");
    } finally { setBusy(false); }
  }

  async function submitAttempt() {
    if (!attempt || report || busy) return;
    setBusy(true); setError("");
    try {
      const payload = await requestJson(`/api/me/mock-exams/${encodeURIComponent(attempt.attempt_id)}/submit`, {
        method: "POST", body: JSON.stringify({ answers }),
      });
      setReport(payload.report || {});
      setAttempt(payload);
      if (payload.report?.timed_out) setError("Time expired before the server received your submission. This attempt was recorded as timed out.");
    } catch (err) { setError(err.message || "Could not submit the mock assessment."); }
    finally { setBusy(false); }
  }

  if (loading) return <PageShell className="narrow-page"><div className="panel collection-state">Checking the published question bank…</div></PageShell>;
  if (error && !info && !attempt) return <PageShell className="narrow-page"><EmptyState title="Mock assessment unavailable" detail={error} action={<Link className="button button-secondary" to="/certificates">Back to certificates</Link>} /></PageShell>;

  if (report) {
    return <PageShell className="narrow-page mock-exam-page">
      <section className="exam-result-card panel">
        <span className={`result-big-icon ${report.passed ? "passed" : "not-passed"}`}>{report.passed ? <CheckCircle2 size={29} /> : <XCircle size={29} />}</span>
        <div className="eyebrow">TIMED PRACTICE · NOT A CERTIFICATION EXAM</div>
        <h1>{report.passed ? "Mock assessment complete" : "Review and practise again"}</h1>
        <p>You scored {report.score_percent}% ({report.correct_count} of {report.question_count} correct). Passing guide: {report.pass_percent}%. This report does not award XP or issue/change a certificate.</p>
        <div className="score-ring" style={{ "--score": `${report.score_percent}%` }}><div><strong>{report.score_percent}%</strong><small>Score</small></div></div>
        {report.timed_out && <p className="form-error" role="status">This attempt timed out and received no credit for answers submitted after the deadline.</p>}
        <section className="mock-topic-report"><h2>Topic performance</h2>{(report.topic_performance || []).map((topic) => <div className="mock-topic-row" key={topic.topic}><div><strong>{topic.topic}</strong><span>{topic.correct}/{topic.total} · {topic.percent}%</span></div><div className="mock-topic-track"><span style={{ width: `${topic.percent}%` }} /></div></div>)}</section>
        <section className="exam-answer-review"><h2>Answer review</h2>{(report.results || []).map((item, i) => <article className="exam-answer-review-item" key={item.question_id}><h3>{i + 1}. {item.prompt}</h3><p>{item.is_correct ? "Correct" : "Incorrect"} · Your answer: {item.selected_answer || "Not answered"}</p>{!item.is_correct && <p><strong>Correct answer:</strong> {item.correct_answer}</p>}<p>{item.explanation}</p>{item.lesson_slug && <Link to={`/learn/${examSlug}/${item.lesson_slug}`}>Review related lesson</Link>}</article>)}</section>
        <div className="hero-actions"><Link className="button button-primary" to={`/mock-exam/${encodeURIComponent(examSlug)}`} onClick={() => { setReport(null); setAttempt(null); setAnswers({}); setIndex(0); setError(""); }}>Try another mock</Link><Link className="button button-secondary" to={`/exam/${encodeURIComponent(examSlug)}`}>Certification exam</Link><Link className="button button-secondary" to="/plans">Plan details</Link></div>
      </section>
    </PageShell>;
  }

  if (!attempt) {
    const canStart = Boolean(info?.can_start);
    return <PageShell className="narrow-page mock-exam-page">
      <div className="exam-start-card panel">
        <div className="eyebrow">PRO · MAX · FULL ACCESS</div>
        <h1>{info?.title || "Timed mock assessment"}</h1>
        <p>{info?.message || "Practise with a timed set drawn from the course's published question bank."}</p>
        <div className="exam-start-stats"><span><ListChecks size={16} /> {info?.question_count || 20} questions</span><span><Clock3 size={16} /> {info?.duration_minutes || 20} minutes</span><span><ShieldCheck size={16} /> Practice only</span></div>
        {!info?.available && <div className="notice-box"><XCircle size={17} /><p>{info?.message || "The course does not have enough published questions for this mock assessment yet."}</p></div>}
        {!canStart && info?.available && <div className="notice-box"><Crown size={17} /><p>This timed mock collection is included with Pro, Max, and Full Access. Standard course exams and earned certificates remain available on every plan.</p></div>}
        {error && <p className="form-error" role="alert">{error}</p>}
        {canStart ? <button className="button button-primary button-wide" onClick={startAttempt} disabled={busy || !info?.available}>{busy ? "Starting…" : "Begin timed mock"} <ArrowRight size={16} /></button> : <Link className="button button-primary button-wide" to={info?.available ? "/plans" : "/certificates"}>{info?.available ? "View Pro plans" : "Back to certificates"} <ArrowRight size={16} /></Link>}
        <Link className="text-link center-link" to={`/exam/${encodeURIComponent(examSlug)}`}>Open the certification exam</Link>
      </div>
    </PageShell>;
  }

  return <PageShell className="narrow-page mock-exam-page">
    <section className="exam-question-card panel">
      <div className="exam-question-topline"><span>Question {index + 1} of {questions.length}</span><span>{answeredCount} answered</span><strong className={remaining <= 60 ? "mock-time-low" : "mock-time"}><Clock3 size={15} /> {formatTime(remaining)}</strong></div>
      <div className="exam-progress-track"><span style={{ width: `${((index + 1) / Math.max(1, questions.length)) * 100}%` }} /></div>
      <div className="eyebrow">{current?.topic || info?.title}</div><h1>{current?.prompt}</h1>
      <fieldset className="exam-option-list"><legend className="sr-only">Choose your answer</legend>{(current?.options || []).map((option, i) => <label className={`exam-option ${answers[current.id] === option ? "selected" : ""}`} key={`${current.id}-${i}`}><input type="radio" name={`mock-answer-${current.id}`} checked={answers[current.id] === option} onChange={() => setAnswers((previous) => ({ ...previous, [current.id]: option }))} /><span>{option}</span></label>)}</fieldset>
      {error && <p className="form-error" role="alert">{error}</p>}
      {remaining <= 0 && <p className="form-error" role="status">Time is up. Submit now; the server enforces the deadline.</p>}
      <div className="exam-question-actions"><button className="button button-secondary" disabled={index === 0 || busy} onClick={() => setIndex((old) => Math.max(0, old - 1))}><ArrowLeft size={16} /> Previous</button>{remaining <= 0 ? <button className="button button-primary" disabled={busy} onClick={submitAttempt}>{busy ? "Submitting…" : "Submit timed-out attempt"} <CheckCircle2 size={16} /></button> : index < questions.length - 1 ? <button className="button button-primary" disabled={!current || !answers[current.id] || busy} onClick={() => setIndex((old) => Math.min(questions.length - 1, old + 1))}>Next <ArrowRight size={16} /></button> : <button className="button button-primary" disabled={busy} onClick={submitAttempt}>{busy ? "Submitting…" : "Submit mock assessment"} <CheckCircle2 size={16} /></button>}</div>
      <p className="exam-unanswered-note">Only the saved attempt is timed by the server. Timed-out submissions do not receive credit for late answers; results do not affect XP or certification.</p>
    </section>
  </PageShell>;
}
