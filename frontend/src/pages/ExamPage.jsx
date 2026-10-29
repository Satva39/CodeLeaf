import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowRight,
  Award,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Clock3,
  ListChecks,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { COURSE_CATALOG } from "../data.js";
import { API_BASE } from "../lib/demoState.js";
import { PageShell, CourseIcon, EmptyState } from "../components/common.jsx";

async function requestJson(path, options = {}) {
  const response = await apiFetch(`${API_BASE}${path}`, {
    credentials: "include",
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    const message = typeof detail === "string"
      ? detail
      : (detail?.message || "The exam request could not be completed.");
    const error = new Error(message);
    error.status = response.status;
    error.code = typeof detail === "object" ? detail?.code : undefined;
    throw error;
  }
  return payload;
}

export default function ExamPage() {
  const { examSlug = "html" } = useParams();
  const course = COURSE_CATALOG.find((item) => item.slug === examSlug) || COURSE_CATALOG[0];
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setInfo(null);
    setAttempt(null);
    setAnswers({});
    setResult(null);
    requestJson(`/api/courses/${encodeURIComponent(examSlug)}/exam`, { signal: controller.signal })
      .then(setInfo)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message || "The exam is not available.");
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [examSlug]);

  const questions = Array.isArray(attempt?.questions) ? attempt.questions : [];
  const current = questions[questionIndex];
  const answeredCount = useMemo(() => questions.filter((question) => answers[question.id]).length, [answers, questions]);

  async function startExam() {
    setBusy(true);
    setError("");
    try {
      const created = await requestJson(`/api/courses/${encodeURIComponent(examSlug)}/exam/start`, { method: "POST", body: "{}" });
      setAttempt(created);
      setQuestionIndex(0);
      setAnswers({});
      setResult(null);
    } catch (err) {
      setError(err.status === 401 ? "Please sign in to start this exam." : (err.message || "Could not start the exam."));
    } finally {
      setBusy(false);
    }
  }

  async function submitExam() {
    if (!attempt || answeredCount !== questions.length) return;
    setBusy(true);
    setError("");
    try {
      const submitted = await requestJson(`/api/me/exams/${encodeURIComponent(attempt.attempt_id)}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      setResult(submitted);
    } catch (err) {
      setError(err.message || "Could not submit the exam.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <PageShell className="narrow-page"><div className="panel collection-state">Loading {course.title} exam information…</div></PageShell>;

  if (error && !info && !attempt) {
    return <PageShell className="narrow-page"><EmptyState title="Exam not available" detail={`${error} Draft exams remain unavailable unless local draft preview is explicitly enabled.`} action={<Link to="/certificates" className="button button-secondary">Back to certificates</Link>} /></PageShell>;
  }

  if (!attempt && !result) {
    return (
      <PageShell className="narrow-page">
        <div className="exam-start-card panel">
          <span className="exam-large-icon"><CourseIcon course={course} /></span>
          <div className="eyebrow">CODELEAF SKILLS ASSESSMENT</div>
          <h1>{info?.title || `${course.title} Skills Assessment`}</h1>
          <p>This course-specific certification stage contains 80 distinct MCQs drawn from the published question bank. Answers are checked by the backend. Passing the MCQ stage is followed by a mandatory practical assessment; the MCQ result alone never awards a certificate.</p>
          <div className="exam-start-stats">
            <span><ListChecks size={16} /> {info?.question_count || 0} questions</span>
            <span><Clock3 size={16} /> About {info?.duration_minutes || 60} minutes</span>
            <span><ShieldCheck size={16} /> Pass: {info?.pass_percent || 70}%</span>
          </div>
          <div className="notice-box"><CircleHelp size={17} /><p>Every question must be answered. Your score and any certificate eligibility are determined by the server. Draft curriculum stays hidden outside local preview.</p></div>
          {error && <p className="form-error" role="alert">{error} {error.toLowerCase().includes("sign in") && <Link to="/login" className="text-link">Sign in</Link>}</p>}
          <button className="button button-primary button-wide" disabled={busy || !info?.question_count} onClick={startExam}>{busy ? "Starting…" : "Begin exam"} <ArrowRight size={16} /></button>
          <Link className="button button-secondary button-wide mock-exam-entry" to={`/mock-exam/${encodeURIComponent(examSlug)}`}>Try a timed practice mock (Pro+) <ArrowRight size={15} /></Link>
          <Link className="text-link center-link" to="/certificates">Back to certificates</Link>
        </div>
      </PageShell>
    );
  }

  if (result) {
    const passed = Boolean(result.passed);
    return (
      <PageShell className="narrow-page">
        <div className="exam-result-card panel">
          <span className={`result-big-icon ${passed ? "passed" : "not-passed"}`}>{passed ? <CheckCircle2 size={29} /> : <XCircle size={29} />}</span>
          <div className="eyebrow">SERVER-GRADED EXAM RESULT</div>
          <h1>{passed ? "You passed the exam" : "Keep practising and try again"}</h1>
          <p>You answered {result.correct_count} of {result.question_count} questions correctly and scored {result.score_percent}%. Passing threshold: {result.pass_percent}%.</p>
          <div className="score-ring" style={{ "--score": `${result.score_percent}%` }}><div><strong>{result.score_percent}%</strong><small>Score</small></div></div>
          <div className="certificate-proof panel">
            {result.certificate ? <Award size={23} /> : <ShieldCheck size={23} />}
            <div><strong>{result.certificate ? "Verified certificate issued" : passed ? "Exam passed — certificate status" : "Certificate not issued"}</strong><small>{result.certificate ? `Credential ID · ${result.certificate.public_id}` : result.certificate_message || "A passing exam alone does not guarantee certificate eligibility."}</small></div>
            <span className={`pill ${result.certificate ? "pill-mint" : "pill-neutral"}`}>{result.certificate_status || "not_issued"}</span>
          </div>
          {passed && result.certificate_status === "practical_exam_required" && (
            <div className="hero-actions">
              <Link className="button button-primary" to={`/practical/${encodeURIComponent(examSlug)}`}>Take practical exam <ArrowRight size={15} /></Link>
            </div>
          )}
          {passed && result.certificate_status === "practical_exam_not_passed" && (
            <div className="hero-actions">
              <Link className="button button-primary" to={`/practical/${encodeURIComponent(examSlug)}`}>Retry practical exam <ArrowRight size={15} /></Link>
            </div>
          )}
          {passed && result.certificate_status === "practical_exam_unavailable" && (
            <p className="collection-checked-note" role="status">{result.certificate_message || "The practical assessment is not published yet. The MCQ pass alone cannot issue a certificate."}</p>
          )}
          <section className="exam-answer-review">
            <h2>Review your answers</h2>
            {(result.results || []).map((item, index) => <article className="exam-answer-review-item" key={item.question_id}><h3>{index + 1}. {item.prompt}</h3><p>{item.is_correct ? "Correct" : "Your answer"}: {item.selected_answer}</p>{!item.is_correct && <p><strong>Correct answer:</strong> {item.correct_answer}</p>}<p>{item.explanation}</p>{item.lesson_slug && <Link to={`/learn/${examSlug}/${item.lesson_slug}`}>Review related lesson</Link>}</article>)}
          </section>
          <div className="hero-actions">
            {result.certificate?.public_id && (
              <Link
                className="button button-primary"
                to={`/certificates/view/${encodeURIComponent(result.certificate.public_id)}`}
              >
                View certificate <ArrowRight size={15} />
              </Link>
            )}
            <Link className={`button ${result.certificate?.public_id ? "button-secondary" : "button-primary"}`} to="/certificates">View certificates</Link>
            <Link className="button button-secondary" to={`/exam/${examSlug}`}>Back to exam</Link>
          </div>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell className="narrow-page">
      <div className="exam-question-card panel">
        <div className="exam-question-topline"><span>Question {questionIndex + 1} of {questions.length}</span><span>{answeredCount} answered</span></div>
        <div className="exam-progress-track"><span style={{ width: `${((questionIndex + 1) / Math.max(1, questions.length)) * 100}%` }} /></div>
        <div className="eyebrow">{current?.topic || info?.title}</div>
        <h1>{current?.prompt}</h1>
        <fieldset className="exam-option-list">
          <legend className="sr-only">Choose your answer</legend>
          {(current?.options || []).map((option, index) => <label className={`exam-option ${answers[current.id] === option ? "selected" : ""}`} key={`${current.id}-${index}`}><input type="radio" name={`answer-${current.id}`} checked={answers[current.id] === option} onChange={() => setAnswers((previous) => ({ ...previous, [current.id]: option }))} /><span>{option}</span></label>)}
        </fieldset>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="exam-question-actions">
          <button className="button button-secondary" disabled={questionIndex === 0 || busy} onClick={() => setQuestionIndex((index) => Math.max(0, index - 1))}><ChevronLeft size={16} /> Previous</button>
          {questionIndex < questions.length - 1 ? <button className="button button-primary" disabled={!current || !answers[current.id] || busy} onClick={() => setQuestionIndex((index) => Math.min(questions.length - 1, index + 1))}>Next <ChevronRight size={16} /></button> : <button className="button button-primary" disabled={busy || answeredCount !== questions.length} onClick={submitExam}>{busy ? "Submitting…" : "Submit exam"} <CheckCircle2 size={16} /></button>}
        </div>
        {answeredCount !== questions.length && <p className="exam-unanswered-note">Answer all questions before submitting ({questions.length - answeredCount} remaining).</p>}
      </div>
      <Link className="text-link center-link" to="/certificates">Exit to certificates</Link>
    </PageShell>
  );
}
