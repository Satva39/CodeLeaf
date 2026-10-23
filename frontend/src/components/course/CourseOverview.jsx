import { apiFetch } from "../../lib/apiClient.js";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, BookOpen, Clock3, Layers3, ListChecks } from "lucide-react";
import { API_BASE } from "../../lib/demoState.js";
import { CourseIcon } from "../common.jsx";

function shortCourseTitle(course) {
  return String(course?.title || course?.slug || "Course")
    .replace(/\s+[—–-]\s+From Beginner to Professional.*$/i, "")
    .replace(/\s+Tutorial$/i, "")
    .trim();
}

function asItems(value) {
  if (Array.isArray(value)) return value.filter((item) => typeof item === "string" && item.trim());
  return typeof value === "string" && value.trim() ? [value.trim()] : [];
}

export default function CourseOverview({
  course,
  sectionLabel,
  pageSuffix,
  backTo,
  backLabel,
  actionTo,
  actionLabel = "Open tutorial",
  allowUnavailableAction = false,
}) {
  const shortTitle = shortCourseTitle(course);
  const available = ["Published", "Local preview"].includes(course?.status);
  const [outline, setOutline] = useState(null);
  const [outlineError, setOutlineError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setOutline(null);
    setOutlineError(false);
    if (!course?.slug || !available) return () => controller.abort();
    apiFetch(`${API_BASE}/api/courses/${encodeURIComponent(course.slug)}/outline`, {
      credentials: "include",
      signal: controller.signal,
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "Outline unavailable");
        return payload;
      })
      .then((payload) => setOutline(payload))
      .catch((error) => {
        if (error.name !== "AbortError") setOutlineError(true);
      });
    return () => controller.abort();
  }, [course?.slug, available]);

  const audience = asItems(course?.audience);
  const prerequisites = asItems(course?.prerequisites);
  const outcomes = asItems(course?.learningOutcomes);
  const modules = Array.isArray(outline?.modules) ? outline.modules : [];
  const statusLabel = course?.status || "Roadmap";
  const actionCanOpenCourse = available || allowUnavailableAction;
  const resolvedActionTo = actionCanOpenCourse
    ? (actionTo || `/learn/${encodeURIComponent(course.slug)}`)
    : "/tutorials";
  const resolvedActionLabel = actionCanOpenCourse ? actionLabel : "Browse learning paths";

  return (
    <section className="course-overview panel">
      <div className="course-overview-main">
        <div className="course-overview-head">
          <CourseIcon course={course} size="xl" />
          <div className="course-overview-copy">
            <div className="eyebrow">{sectionLabel}</div>
            <h1>{shortTitle} {pageSuffix}</h1>
            <p>{course?.desc || `Course information for ${shortTitle} will be shown when it is published.`}</p>
            <div className="course-overview-meta">
              <span>{course?.category || "Learning path"}</span>
              <span>{course?.level || "Level not set"}</span>
              <span className={`course-status-pill course-status-${statusLabel.toLowerCase().replaceAll(" ", "-")}`}>{statusLabel}</span>
            </div>
          </div>
        </div>
        <div className="course-overview-counts" aria-label="Course content summary">
          <span><BookOpen size={15} /><strong>{Number(course?.lessons) || 0}</strong> lessons</span>
          <span><Layers3 size={15} /><strong>{Number(course?.modules) || 0}</strong> modules</span>
          <span><ListChecks size={15} /><strong>{Number(course?.practice) || 0}</strong> practice tasks</span>
          {Number(course?.estimatedMinutes) > 0 && <span><Clock3 size={15} /><strong>{Math.ceil(course.estimatedMinutes / 60)}h</strong> estimated</span>}
        </div>
        {(audience.length > 0 || prerequisites.length > 0 || outcomes.length > 0) && <div className="course-overview-details">
          {audience.length > 0 && <section><h2>Who this is for</h2><ul>{audience.slice(0, 4).map((item) => <li key={item}>{item}</li>)}</ul></section>}
          {prerequisites.length > 0 && <section><h2>Prerequisites</h2><ul>{prerequisites.slice(0, 4).map((item) => <li key={item}>{item}</li>)}</ul></section>}
          {outcomes.length > 0 && <section><h2>Learning outcomes</h2><ul>{outcomes.slice(0, 5).map((item) => <li key={item}>{item}</li>)}</ul></section>}
        </div>}
        {available && <section className="course-module-outline">
          <h2>Course outline</h2>
          {modules.length > 0 ? <ol>{modules.slice(0, 8).map((module) => <li key={module.slug || module.id}><strong>{module.title}</strong><span>{Array.isArray(module.lessons) ? module.lessons.length : 0} lessons</span></li>)}</ol> : <p role="status">{outlineError ? "The course outline could not be loaded right now." : outline ? "No published module outline is available yet." : "Loading the published course outline…"}</p>}
          {modules.length > 8 && <p className="course-outline-more">And {modules.length - 8} more modules in the full outline.</p>}
        </section>}
        {!available && <p className="course-roadmap-note">This track is planned or not yet published. Its live lessons and activities will appear here after release.</p>}
      </div>
      <div className="course-overview-actions">
        {backTo && <Link className="button button-secondary" to={backTo}><ArrowLeft size={15} /> {backLabel || "All courses"}</Link>}
        <Link className="button button-primary" to={resolvedActionTo}><BookOpen size={15} /> {resolvedActionLabel} <ArrowRight size={14} /></Link>
      </div>
    </section>
  );
}
