import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, BookOpenCheck, CheckCircle2, Code2, Search, Zap } from "lucide-react";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import { useGamificationStats } from "../lib/useGamificationStats.js";
import { useCourseCatalog } from "../lib/useCourseCatalog.js";
import { isSupportedPracticeExercise, practiceExerciseLabel } from "../lib/practiceExerciseTypes.js";
import { EmptyState, PageShell } from "../components/common.jsx";
import CourseOverview from "../components/course/CourseOverview.jsx";

async function fetchAllCourseExercises(courseSlug, signal) {
  const collected = [];
  let offset = 0;
  let total = Infinity;
  while (offset < total && offset < 5000) {
    const response = await apiFetch(`${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/exercises?limit=100&offset=${offset}`, { credentials: "include", signal });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || "Practice tasks could not be loaded.");
    const items = Array.isArray(payload.items) ? payload.items : [];
    collected.push(...items);
    total = Number(payload.total ?? collected.length);
    if (!items.length) break;
    offset += items.length;
  }
  return collected;
}

export default function ChallengesPage() {
  const { courseSlug } = useParams();
  const courses = useCourseCatalog();
  const course = courses.find((item) => item.slug === courseSlug);
  const stats = useGamificationStats();
  const [exercises, setExercises] = useState([]);
  const [completedExercises, setCompletedExercises] = useState(() => new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [previewMode, setPreviewMode] = useState(false);
  const [query, setQuery] = useState("");
  const [difficulty, setDifficulty] = useState("All levels");

  useEffect(() => {
    const controller = new AbortController();
    setExercises([]); setCompletedExercises(new Set()); setLoading(true); setError("");
    fetchAllCourseExercises(courseSlug, controller.signal)
      .then(async (items) => {
        const supportedItems = items.filter((item) => isSupportedPracticeExercise(item.type));
        setExercises(supportedItems);
        setPreviewMode(supportedItems.some((item) => item.status === "draft"));
        try {
          const response = await apiFetch(
            `${API_BASE}/api/me/courses/${encodeURIComponent(courseSlug)}/exercise-progress`,
            { credentials: "include", signal: controller.signal },
          );
          if (response.ok) {
            const payload = await response.json().catch(() => ({}));
            const keys = (Array.isArray(payload.items) ? payload.items : [])
              .filter((item) => item.completed)
              .map((item) => `${item.lesson_slug}:${item.exercise_slug}`);
            setCompletedExercises(new Set(keys));
          }
        } catch (progressError) {
          if (progressError.name === "AbortError") throw progressError;
        }
      })
      .catch((err) => { if (err.name !== "AbortError") setError(err.message || "Practice tasks could not be loaded."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [courseSlug]);

  const levels = useMemo(() => ["All levels", ...new Set(exercises.map((item) => item.difficulty || "Practice").filter(Boolean))], [exercises]);
  const filtered = useMemo(() => exercises.filter((exercise) => {
    const text = `${exercise.title} ${exercise.prompt || ""} ${exercise.type || ""} ${exercise.difficulty || ""} ${exercise.module_title || ""} ${exercise.lesson_title || ""}`.toLowerCase();
    return isSupportedPracticeExercise(exercise.type)
      && (difficulty === "All levels" || (exercise.difficulty || "Practice") === difficulty)
      && text.includes(query.trim().toLowerCase());
  }), [exercises, difficulty, query]);
  const grouped = useMemo(() => {
    const result = new Map();
    filtered.forEach((exercise) => {
      const groupName = exercise.module_title || exercise.lesson_title || "Course practice";
      if (!result.has(groupName)) result.set(groupName, []);
      result.get(groupName).push(exercise);
    });
    return [...result.entries()];
  }, [filtered]);

  if (!course) return <PageShell><EmptyState title="Course not found" detail="Choose a course from the Practice catalog." action={<Link to="/practice" className="button button-primary">Browse practice courses</Link>} /></PageShell>;

  return (
    <PageShell className="course-collection-detail course-exercise-library">
      <CourseOverview course={course} sectionLabel="HANDS-ON PRACTICE" pageSuffix="Exercises" backTo="/practice" backLabel="All practice courses" actionTo={`/learn/${course.slug}`} actionLabel="Open tutorial" />
      <section className="practice-summary panel">
        <div className="practice-summary-icon"><CheckCircle2 size={23} /></div>
        <div><h2>One practice library for the whole course</h2><p>Exercises are grouped by module, not buried inside lessons. Open a task on its own page, try your answer, reveal hints, and view the worked solution when you need it.</p></div>
        <span className="challenge-xp"><Zap size={14} /> {stats.exerciseXp} base XP per correct exercise</span>
      </section>
      <div className="collection-detail-toolbar">
        <div><h2>{previewMode ? "Practice tasks in local preview" : "Exercises and coding challenges"}</h2><p>{previewMode ? "Local preview data is shown only when the API allows it." : "Only published exercises are provided by the API."}</p></div>
        <label className="catalog-search panel collection-detail-search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search topic, task, or concept…" aria-label="Search practice tasks" /><span>{filtered.length}</span></label>
      </div>
      {!!exercises.length && <div className="category-tabs collection-category-tabs" aria-label="Filter exercises by difficulty">{levels.map((value) => <button key={value} type="button" onClick={() => setDifficulty(value)} className={difficulty === value ? "active" : ""} aria-pressed={difficulty === value}>{value}</button>)}</div>}
      {loading ? <div className="panel collection-state">Loading {course.title} exercises…</div> : error ? <EmptyState title="Practice is not available yet" detail={`${error} Check that the course, lessons, and exercises have been imported and published.`} action={<Link to="/practice" className="button button-secondary">Browse other courses</Link>} /> : grouped.length ? (
        <div className="exercise-topic-groups">
          {grouped.map(([groupName, items]) => <section key={groupName} className="exercise-topic-group panel">
            <div className="exercise-topic-heading"><div><span className="eyebrow">MODULE / TOPIC</span><h2>{groupName}</h2></div><span>{items.length} task{items.length === 1 ? "" : "s"}</span></div>
            <div className="exercise-topic-list">
              {items.map((exercise) => <article key={`${exercise.course_slug || course.slug}:${exercise.lesson_slug}:${exercise.slug}`} className="exercise-library-row">
                <span className="challenge-row-icon"><Code2 size={17} /></span>
                <div className="challenge-row-copy"><div className="practice-task-meta"><span>{exercise.difficulty || "PRACTICE"}</span><span>{practiceExerciseLabel(exercise.type)}</span>{completedExercises.has(`${exercise.lesson_slug}:${exercise.slug}`) && <span className="pill pill-mint practice-completed-badge" role="status" aria-label="Exercise completed"><CheckCircle2 size={13} aria-hidden="true" /> Completed</span>}</div><h3>{exercise.title}</h3><p>{exercise.prompt || "Open this task to read the instructions."}</p><small>Lesson: {exercise.lesson_title || exercise.lesson_slug}</small></div>
                <span className="challenge-xp"><Zap size={13} /> {exercise.xp_points ?? stats.exerciseXp} XP</span>
                <Link className="button button-secondary button-small" to={`/practice/${encodeURIComponent(course.slug)}/${encodeURIComponent(exercise.lesson_slug)}/${encodeURIComponent(exercise.slug)}`}>Open exercise <ArrowRight size={13} /></Link>
              </article>)}
            </div>
          </section>)}
        </div>
      ) : <EmptyState icon={BookOpenCheck} title={query ? "No matching practice tasks" : "No published practice tasks yet"} detail={query ? "Try another search or difficulty." : `Exercises for ${course.title} will appear here once authored content is imported and published.`} action={query ? <button className="button button-secondary" onClick={() => { setQuery(""); setDifficulty("All levels"); }}>Clear filters</button> : <Link to={`/learn/${course.slug}`} className="button button-primary">Read the tutorial <ArrowRight size={14} /></Link>} />}
    </PageShell>
  );
}
