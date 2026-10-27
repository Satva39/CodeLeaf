import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, BookOpen, CheckCircle2, ChevronDown, Code2, Eye, Lightbulb, Play, ShieldCheck, Sparkles, Zap } from "lucide-react";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import { useGamificationStats } from "../lib/useGamificationStats.js";
import { compatibleFilename, openSeededWorkspace, resolveLanguage } from "../lib/languageWorkspace.js";
import { isSupportedPracticeExercise, practiceExerciseLabel } from "../lib/practiceExerciseTypes.js";
import { EmptyState, PageShell } from "../components/common.jsx";

async function responsePayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
  return payload;
}

async function fetchAllCourseExercises(courseSlug, signal) {
  const collected = [];
  let offset = 0;
  let total = Infinity;
  while (offset < total && offset < 5000) {
    const payload = await responsePayload(await apiFetch(
      `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/exercises?limit=100&offset=${offset}`,
      { credentials: "include", signal },
    ));
    const items = Array.isArray(payload.items) ? payload.items : [];
    collected.push(...items);
    total = Number(payload.total ?? collected.length);
    if (!items.length) break;
    offset += items.length;
  }
  return collected;
}

async function fetchCourseExerciseProgress(courseSlug, signal) {
  const response = await apiFetch(
    `${API_BASE}/api/me/courses/${encodeURIComponent(courseSlug)}/exercise-progress`,
    { credentials: "include", signal },
  );
  if (response.status === 401) return [];
  const payload = await responsePayload(response);
  return Array.isArray(payload.items) ? payload.items : [];
}

function exerciseRoute(courseSlug, item) {
  return `/practice/${encodeURIComponent(courseSlug)}/${encodeURIComponent(item.lesson_slug)}/${encodeURIComponent(item.slug)}`;
}
function prettyCode(value) {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "";
  return JSON.stringify(value, null, 2);
}

function starterAnswer(exercise) {
  const starter = exercise?.starter && typeof exercise.starter === "object" ? exercise.starter : {};
  for (const key of ["code", "source_code"]) {
    if (typeof starter[key] === "string" && starter[key].trim()) return starter[key];
  }
  const type = String(exercise?.type || "").toLowerCase().replaceAll("-", "_");
  if (["coding", "code", "implementation"].includes(type) && typeof starter.starter === "string") return starter.starter;
  if (["practical", "workbook_practice"].includes(type) && typeof starter.content === "string") return starter.content;
  if (typeof starter.starter === "string" && /solidity/i.test(String(starter.language || ""))) return starter.starter;
  if (typeof starter.template === "string") return starter.template;
  if (typeof starter.response_template === "string") return starter.response_template;
  const sections = Array.isArray(starter.template_sections) ? starter.template_sections : Array.isArray(starter.submission_sections) ? starter.submission_sections : [];
  if (sections.length) return sections.map((section) => `${String(section)}:\n\n`).join("");
  if (Array.isArray(starter.headers)) {
    const rows = Array.isArray(starter.rows) ? starter.rows : [];
    return [starter.headers, ...rows].map((row) => Array.isArray(row) ? row.map((cell) => String(cell ?? "")).join(",") : String(row ?? "")).join("\n");
  }
  return "";
}

function usesCodeEditor(exercise) {
  const starter = exercise?.starter && typeof exercise.starter === "object" ? exercise.starter : {};
  const type = String(exercise?.type || "").toLowerCase().replaceAll("-", "_");
  if (["choice", "multiple_choice", "mcq"].includes(type) || Array.isArray(starter.options)) return false;
  if (["coding", "code", "implementation"].includes(type)) return true;
  if (typeof starter.code === "string" || typeof starter.source_code === "string") return true;
  if (["practical", "workbook_practice"].includes(type) && (typeof starter.content === "string" || (Array.isArray(starter.headers) && starter.headers.length > 0))) return true;
  if (type === "workbook_practice" && Array.isArray(starter.headers)) return true;
  return typeof starter.starter === "string" && /solidity/i.test(String(starter.language || ""));
}

export default function ExerciseDetailPage() {
  const { courseSlug = "", lessonSlug = "", exerciseSlug = "" } = useParams();
  const stats = useGamificationStats();
  const [exercise, setExercise] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [answer, setAnswer] = useState("");
  const [selectedOption, setSelectedOption] = useState("");
  const [hintOpen, setHintOpen] = useState(false);
  const [solution, setSolution] = useState(null);
  const [solutionLoading, setSolutionLoading] = useState(false);
  const [solutionError, setSolutionError] = useState("");
  const [checking, setChecking] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [navigation, setNavigation] = useState({ previous: null, next: null, index: -1, total: 0 });

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(""); setExercise(null); setSolution(null); setFeedback(null); setAnswer(""); setSelectedOption("");
    setNavigation({ previous: null, next: null, index: -1, total: 0 });
    const lessonItemsPromise = apiFetch(
      `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(lessonSlug)}/exercises`,
      { credentials: "include", signal: controller.signal },
    ).then(responsePayload);
    const courseItemsPromise = fetchAllCourseExercises(courseSlug, controller.signal).catch(() => []);
    const progressPromise = fetchCourseExerciseProgress(courseSlug, controller.signal).catch(() => []);
    Promise.all([lessonItemsPromise, courseItemsPromise, progressPromise])
      .then(([lessonPayload, courseItems, progressItems]) => {
        const lessonItems = (Array.isArray(lessonPayload.items) ? lessonPayload.items : [])
          .filter((item) => isSupportedPracticeExercise(item.type));
        const match = lessonItems.find((item) => item.slug === exerciseSlug);
        if (!match) throw new Error("This exercise is not available. It may be unpublished or moved.");
        const supportedCourseItems = courseItems.filter((item) => isSupportedPracticeExercise(item.type));
        const ordered = supportedCourseItems.length ? supportedCourseItems : lessonItems.map((item) => ({ ...item, lesson_slug: lessonSlug }));
        const index = ordered.findIndex((item) => item.slug === exerciseSlug && item.lesson_slug === lessonSlug);
        const progress = new Map(progressItems.map((item) => [
          `${item.lesson_slug}:${item.exercise_slug}`,
          Boolean(item.completed),
        ]));
        const restored = {
          ...match,
          completed: progress.get(`${lessonSlug}:${exerciseSlug}`) === true,
        };
        setExercise(restored);
        setAnswer(starterAnswer(restored));
        if (index >= 0) {
          setNavigation({
            previous: index > 0 ? ordered[index - 1] : null,
            next: index < ordered.length - 1 ? ordered[index + 1] : null,
            index,
            total: ordered.length,
          });
        }
      })
      .catch((err) => { if (err.name !== "AbortError") setError(typeof err.message === "string" ? err.message : "Could not load this exercise."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [courseSlug, lessonSlug, exerciseSlug]);

  const isChoice = Boolean(exercise && (Array.isArray(exercise.starter?.options) || ["choice", "multiple_choice", "mcq"].includes(String(exercise.type || "").toLowerCase())));
  const options = Array.isArray(exercise?.starter?.options) ? exercise.starter.options : [];
  const isCode = usesCodeEditor(exercise) && !isChoice;
  // The course route is authoritative: a Java exercise must use Java, a SQL exercise
  // must use its course's SQL dialect, and AI/data-science tasks use the Python workspace.
  const language = resolveLanguage(courseSlug, "");
  const exerciseFilename = compatibleFilename(exercise?.starter?.file_name || exercise?.starter?.filename, language);
  const currentAnswer = isChoice ? selectedOption : answer;
  const criteria = useMemo(() => Array.isArray(exercise?.acceptance_criteria) ? exercise.acceptance_criteria : [], [exercise]);
  const hints = useMemo(() => Array.isArray(exercise?.hints) ? exercise.hints : [], [exercise]);

  async function checkAnswer() {
    if (!exercise || !String(currentAnswer || "").trim()) { setFeedback({ tone: "error", message: "Choose or write an answer before submitting." }); return; }
    setChecking(true); setFeedback(null);
    try {
      const response = await apiFetch(`${API_BASE}/api/me/exercises/${encodeURIComponent(courseSlug)}/${encodeURIComponent(lessonSlug)}/${encodeURIComponent(exerciseSlug)}/submit`, {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: isCode ? null : currentAnswer, source_code: isCode ? currentAnswer : null, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC" }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok || !data.ok) {
        setFeedback({ tone: "error", message: response.status === 401 ? "Sign in to check this answer and save progress and XP." : data.detail || "This answer could not be checked." });
        return;
      }
      setFeedback({ tone: data.correct ? "success" : "error", message: data.correct ? (data.xp_awarded > 0 ? `Correct! You earned ${data.xp_awarded} XP.` : "Correct! This exercise has already been rewarded.") : "Not quite yet. Review the hint, try another approach, and check again." });
      setExercise((current) => current ? { ...current, completed: Boolean(data.completed) } : current);
    } catch (err) { setFeedback({ tone: "error", message: err.message || "The API could not be reached." }); }
    finally { setChecking(false); }
  }

  async function revealSolution() {
    if (!exercise || solutionLoading) return;
    setSolutionLoading(true); setSolutionError("");
    try {
      const payload = await responsePayload(await apiFetch(`${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(lessonSlug)}/exercises/${encodeURIComponent(exerciseSlug)}/solution`));
      setSolution(payload);
    } catch (err) { setSolutionError(err.message || "A worked solution is not available for this exercise yet."); }
    finally { setSolutionLoading(false); }
  }

  if (loading) return <PageShell className="exercise-detail-page"><div className="panel collection-state">Loading exercise…</div></PageShell>;
  if (!exercise) return <PageShell className="exercise-detail-page"><EmptyState title="Exercise unavailable" detail={error || "This exercise may not be published yet."} action={<Link to={`/practice/${encodeURIComponent(courseSlug)}`} className="button button-primary">Back to exercise library</Link>} /></PageShell>;

  return (
    <PageShell className="exercise-detail-page">
      <div className="exercise-detail-breadcrumb"><Link to={`/practice/${encodeURIComponent(courseSlug)}`}><ArrowLeft size={14} /> All exercises</Link><span>/</span><Link to={`/learn/${encodeURIComponent(courseSlug)}/${encodeURIComponent(lessonSlug)}`}>{exercise.lesson_title || lessonSlug}</Link></div>
      <header className="exercise-detail-hero panel">
        <div><span className="eyebrow">{String(exercise.difficulty || "PRACTICE").toUpperCase()} · {practiceExerciseLabel(exercise.type).toUpperCase()}</span><h1>{exercise.title}</h1><p>{exercise.prompt}</p><div className="exercise-detail-meta"><span><BookOpen size={14} /> {exercise.module_title || "Course practice"}</span><span><Zap size={14} /> {exercise.xp_points ?? stats.exerciseXp} XP on first correct completion</span>{exercise.completed && <span className="pill pill-mint practice-completed-badge" role="status" aria-label="Exercise completed"><CheckCircle2 size={13} /> Completed</span>}</div></div>
        <Code2 size={32} />
      </header>
      <div className="exercise-detail-layout">
        <main className="exercise-detail-main">
          <section className="exercise-detail-card panel">
            {(exercise.starter?.instructions || exercise.starter?.instruction || exercise.starter?.context || exercise.starter?.notes || exercise.starter?.dataset_note || exercise.starter?.note || exercise.starter?.use || exercise.starter?.execution_mode) && <div className="exercise-starter-context">{[exercise.starter?.instructions, exercise.starter?.instruction, exercise.starter?.context, exercise.starter?.notes, exercise.starter?.dataset_note, exercise.starter?.note, exercise.starter?.use, exercise.starter?.execution_mode].filter((value) => typeof value === "string" && value.trim()).map((value, index) => <p key={`${index}-${value}`}>{value}</p>)}</div>}
            <div className="exercise-detail-section-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h2>Write your answer</h2></div><span className="exercise-detail-badge">{isChoice ? "Choose one" : isCode ? exerciseFilename : "Answer"}</span></div>
            {isChoice ? <div className="exercise-options">{options.map((option) => <label key={option} className={`exercise-option ${selectedOption === option ? "selected" : ""}`}><input type="radio" name={`answer-${exercise.slug}`} value={option} checked={selectedOption === option} onChange={() => setSelectedOption(option)} />{option}</label>)}</div> : <label className="exercise-answer-label"><span>{isCode ? `Your code (${language.label})` : "Your answer"}</span><textarea className={isCode ? "exercise-code-input" : ""} rows={isCode ? 14 : 5} spellCheck="false" value={answer} placeholder={exercise.starter?.placeholder || (isCode ? "Write your code here…" : "Write your answer…")} onChange={(event) => setAnswer(event.target.value)} /></label>}
            {criteria.length > 0 && <details className="exercise-criteria"><summary>What a good answer should include <ChevronDown size={14} /></summary><ul>{criteria.map((criterion, index) => <li key={`${index}-${criterion}`}>{criterion}</li>)}</ul></details>}
            <div className="exercise-detail-actions"><button type="button" className="button button-primary" disabled={checking} onClick={checkAnswer}><CheckCircle2 size={15} /> {checking ? "Checking…" : "Check answer"}</button>{isCode && <button type="button" className="button button-secondary" onClick={() => openSeededWorkspace("try", { courseSlug, lessonSlug, title: exercise.title, language: language.key, code: answer || exercise.starter?.code || "" })}><Play size={14} /> Open in Try-it editor</button>}</div>
            {feedback && <p className={`exercise-feedback ${feedback.tone}`} role="status">{feedback.message}{feedback.message.startsWith("Sign in") && <> <Link to="/login">Sign in</Link>.</>}</p>}
          </section>
          {hints.length > 0 && <section className="exercise-detail-card panel"><button className="exercise-reveal-toggle" type="button" aria-expanded={hintOpen} onClick={() => setHintOpen((value) => !value)}><span><Lightbulb size={17} /> Need a hint?</span><ChevronDown size={16} className={hintOpen ? "rotate-180" : ""} /></button>{hintOpen && <div className="exercise-hint-list">{hints.map((hint, index) => <p key={`${index}-${hint}`}><span>{index + 1}</span>{hint}</p>)}</div>}</section>}
          <section className="exercise-detail-card panel">
            <div className="exercise-solution-heading"><div><span className="eyebrow">LEARN FROM AN EXAMPLE</span><h2>Worked solution</h2><p>Try the task first, then reveal the solution to compare your approach.</p></div><Sparkles size={19} /></div>
            {!solution ? <button type="button" className="button button-secondary" disabled={solutionLoading} onClick={revealSolution}><Eye size={15} /> {solutionLoading ? "Loading solution…" : "Show solution"}</button> : <div className="exercise-solution-content">{solution.answer && <><h3>Answer</h3><pre className={typeof solution.answer === "string" ? "exercise-solution-code" : ""}><code>{prettyCode(solution.answer)}</code></pre></>}{solution.expected_result && <><h3>Expected result</h3><pre>{solution.expected_result}</pre></>}{solution.explanation && <><h3>Explanation</h3><p>{solution.explanation}</p></>}{Array.isArray(solution.steps) && solution.steps.length > 0 && <><h3>Steps</h3><ol>{solution.steps.map((step, index) => <li key={`${index}-${step}`}>{step}</li>)}</ol></>}{Array.isArray(solution.test_cases) && solution.test_cases.length > 0 && <><h3>Test cases</h3><div className="table-scroll"><table><thead><tr><th>Input</th><th>Expected</th></tr></thead><tbody>{solution.test_cases.map((test, index) => <tr key={index}><td>{test.input || "—"}</td><td>{test.expected || "—"}</td></tr>)}</tbody></table></div></>}{!solution.answer && !solution.explanation && !solution.expected_result && <p>The author has not provided a full worked answer yet.</p>}<button type="button" className="button button-secondary button-small" onClick={() => setSolution(null)}>Hide solution</button></div>}
            {solutionError && <p className="exercise-feedback error" role="status">{solutionError}</p>}
          </section>
          <nav className="hero-actions exercise-detail-navigation" aria-label="Exercise navigation">
            {navigation.previous ? (
              <Link className="button button-secondary" to={exerciseRoute(courseSlug, navigation.previous)}><ArrowLeft size={15} /> Previous exercise</Link>
            ) : (
              <span className="muted-inline" aria-disabled="true">First exercise</span>
            )}
            {navigation.index >= 0 && navigation.total > 0 && (
              <span className="muted-inline">Exercise {navigation.index + 1} of {navigation.total}</span>
            )}
            {navigation.next ? (
              <Link className="button button-primary" to={exerciseRoute(courseSlug, navigation.next)}>Next exercise <ArrowRight size={15} /></Link>
            ) : (
              <Link className="button button-primary" to={`/practice/${encodeURIComponent(courseSlug)}`}>Back to all exercises <ArrowRight size={15} /></Link>
            )}
          </nav>
        </main>
        <aside className="exercise-detail-aside">
          <section className="exercise-aside-card panel"><ShieldCheck size={19} /><h3>Fair, server-checked practice</h3><p>Correctness is checked by CodeLeaf's configured grader. XP is awarded by the server once; viewing a solution does not grant XP.</p></section>
          <section className="exercise-aside-card panel"><h3>Suggested workflow</h3><ol><li>Read the task and acceptance criteria.</li><li>Write your own answer.</li><li>Check it and review the feedback.</li><li>Use the hint or worked solution to learn.</li></ol></section>
          <Link className="exercise-aside-link" to={`/learn/${encodeURIComponent(courseSlug)}/${encodeURIComponent(lessonSlug)}`}>Review the lesson <ArrowRight size={14} /></Link>
          <Link className="exercise-aside-link" to={`/practice/${encodeURIComponent(courseSlug)}`}>Choose another exercise <ArrowRight size={14} /></Link>
        </aside>
      </div>
    </PageShell>
  );
}
