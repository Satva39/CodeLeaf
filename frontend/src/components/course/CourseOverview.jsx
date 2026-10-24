import { apiFetch } from "../../lib/apiClient.js";
import { useEffect, useId, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  Clock3,
  GraduationCap,
  Layers3,
  ListChecks,
  Route,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { API_BASE } from "../../lib/demoState.js";
import { CourseIcon } from "../common.jsx";

function shortCourseTitle(course) {
  return String(course?.title || course?.slug || "Course")
    .replace(/\s+[—–-]\s+From Beginner to Professional.*$/i, "")
    .replace(/\s+Tutorial$/i, "")
    .trim();
}

function asItems(value) {
  if (Array.isArray(value))
    return value.filter((item) => typeof item === "string" && item.trim());
  return typeof value === "string" && value.trim() ? [value.trim()] : [];
}

function DetailCard({
  kind,
  title,
  subtitle,
  items,
  icon: Icon,
  marker = "dot",
}) {
  if (!items.length) return null;
  return (
    <section className={`course-detail-card course-detail-card-${kind}`}>
      <div className="course-detail-card-heading">
        <span className="course-detail-card-icon">
          <Icon size={19} aria-hidden="true" />
        </span>
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
      </div>
      <ul className={`course-detail-list course-detail-list-${marker}`}>
        {items.map((item, index) => (
          <li key={`${kind}-${index}-${item}`}>
            {marker === "check" && (
              <CheckCircle2 size={15} aria-hidden="true" />
            )}
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
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
  showLearningSections = false,
}) {
  const shortTitle = shortCourseTitle(course);
  const available = ["Published", "Local preview"].includes(course?.status);
  const [outline, setOutline] = useState(null);
  const [outlineError, setOutlineError] = useState(false);
  const [expandedModule, setExpandedModule] = useState("");
  const outlineId = useId();

  useEffect(() => {
    const controller = new AbortController();
    setOutline(null);
    setOutlineError(false);
    setExpandedModule("");
    if (!showLearningSections || !course?.slug || !available)
      return () => controller.abort();
    apiFetch(
      `${API_BASE}/api/courses/${encodeURIComponent(course.slug)}/outline`,
      {
        credentials: "include",
        signal: controller.signal,
      },
    )
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok)
          throw new Error(payload.detail || "Outline unavailable");
        return payload;
      })
      .then((payload) => {
        setOutline(payload);
        const firstModule = Array.isArray(payload.modules)
          ? payload.modules[0]
          : null;
        setExpandedModule(firstModule?.slug || firstModule?.id || "");
      })
      .catch((error) => {
        if (error.name !== "AbortError") setOutlineError(true);
      });
    return () => controller.abort();
  }, [course?.slug, available, showLearningSections]);

  const audience = asItems(course?.audience);
  const prerequisites = asItems(course?.prerequisites);
  const outcomes = asItems(course?.learningOutcomes);
  const modules = Array.isArray(outline?.modules) ? outline.modules : [];
  const statusLabel = course?.status || "Roadmap";
  const actionCanOpenCourse = available || allowUnavailableAction;
  const resolvedActionTo = actionCanOpenCourse
    ? actionTo || `/learn/${encodeURIComponent(course.slug)}`
    : "/tutorials";
  const resolvedActionLabel = actionCanOpenCourse
    ? actionLabel
    : "Browse learning paths";
  const shownModules = modules.slice(0, 8);

  return (
    <div className="course-overview-stack">
      <section className="course-overview panel">
        <div className="course-overview-main">
          <div className="course-overview-head">
            <CourseIcon course={course} size="xl" />
            <div className="course-overview-copy">
              <div className="eyebrow">{sectionLabel}</div>
              <h1>
                <span>{shortTitle}</span>
                {pageSuffix && (
                  <span className="course-overview-title-suffix">
                    {pageSuffix}
                  </span>
                )}
              </h1>
              <p>
                {course?.desc ||
                  `Course information for ${shortTitle} will be shown when it is published.`}
              </p>
              <div className="course-overview-meta">
                <span>{course?.category || "Learning path"}</span>
                <span>{course?.level || "Level not set"}</span>
                <span
                  className={`course-status-pill course-status-${statusLabel.toLowerCase().replaceAll(" ", "-")}`}
                >
                  {statusLabel}
                </span>
              </div>
            </div>
          </div>
          <div
            className="course-overview-counts"
            aria-label="Course content summary"
          >
            <span>
              <BookOpen size={16} aria-hidden="true" />
              <strong>{Number(course?.lessons) || 0}</strong>
              <span>lessons</span>
            </span>
            <span>
              <Layers3 size={16} aria-hidden="true" />
              <strong>{Number(course?.modules) || 0}</strong>
              <span>modules</span>
            </span>
            <span>
              <ListChecks size={16} aria-hidden="true" />
              <strong>{Number(course?.practice) || 0}</strong>
              <span>practice tasks</span>
            </span>
            {Number(course?.estimatedMinutes) > 0 && (
              <span>
                <Clock3 size={16} aria-hidden="true" />
                <strong>{Math.ceil(course.estimatedMinutes / 60)}h</strong>
                <span>estimated</span>
              </span>
            )}
          </div>
        </div>
        <div className="course-overview-actions">
          {backTo && (
            <Link
              className="button button-secondary course-overview-back"
              to={backTo}
            >
              <ArrowLeft size={15} /> {backLabel || "All courses"}
            </Link>
          )}
          <Link
            className="button button-primary course-overview-start"
            to={resolvedActionTo}
          >
            <BookOpen size={17} aria-hidden="true" /> {resolvedActionLabel}{" "}
            <ArrowRight size={16} aria-hidden="true" />
          </Link>
          {actionCanOpenCourse && (
            <span className="course-overview-action-note">
              <CheckCircle2 size={13} aria-hidden="true" /> Your next step
              starts here
            </span>
          )}
        </div>
      </section>

      {showLearningSections &&
        (audience.length > 0 ||
          prerequisites.length > 0 ||
          outcomes.length > 0) && (
          <section
            className="course-overview-details"
            aria-label="Course fit and outcomes"
          >
            <DetailCard
              kind="audience"
              title="Who this is for"
              subtitle="Find your place on the path"
              items={audience.slice(0, 4)}
              icon={UsersRound}
            />
            <DetailCard
              kind="prerequisites"
              title="Prerequisites"
              subtitle="What helps before you begin"
              items={prerequisites.slice(0, 4)}
              icon={GraduationCap}
            />
            <DetailCard
              kind="outcomes"
              title="Learning outcomes"
              subtitle="What you will be able to do"
              items={outcomes.slice(0, 5)}
              icon={Sparkles}
              marker="check"
            />
          </section>
        )}

      {showLearningSections && available && (
        <section
          className="course-module-outline panel"
          aria-labelledby={`${outlineId}-title`}
        >
          <div className="course-outline-header">
            <div className="course-outline-heading-copy">
              <span className="course-outline-icon">
                <Route size={19} aria-hidden="true" />
              </span>
              <div>
                <div className="eyebrow">YOUR LEARNING PATH</div>
                <h2 id={`${outlineId}-title`}>Course outline</h2>
                <p>
                  Preview each module and see what you will learn before jumping
                  in.
                </p>
              </div>
            </div>
            <div className="course-outline-total">
              <strong>{modules.length || Number(course?.modules) || 0}</strong>
              <span>modules</span>
            </div>
          </div>

          {modules.length > 0 ? (
            <div className="course-roadmap-list">
              {shownModules.map((module, index) => {
                const moduleKey = module.slug || module.id || `module-${index}`;
                const isExpanded = expandedModule === moduleKey;
                const lessons = Array.isArray(module.lessons)
                  ? module.lessons
                  : [];
                const modulePanelId = `${outlineId}-${String(moduleKey).replace(/[^a-zA-Z0-9_-]/g, "-")}`;
                return (
                  <article
                    className={`course-roadmap-module${isExpanded ? " is-expanded" : ""}`}
                    key={moduleKey}
                  >
                    <button
                      type="button"
                      className="course-roadmap-trigger"
                      aria-expanded={isExpanded}
                      aria-controls={modulePanelId}
                      onClick={() =>
                        setExpandedModule((current) =>
                          current === moduleKey ? "" : moduleKey,
                        )
                      }
                    >
                      <span className="course-roadmap-number">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span className="course-roadmap-module-copy">
                        <strong>{module.title}</strong>
                        <small>{module.track || "CORE MODULE"}</small>
                      </span>
                      <span className="course-roadmap-lesson-count">
                        <BookOpen size={14} aria-hidden="true" />{" "}
                        {lessons.length} lessons
                      </span>
                      <ChevronDown
                        className="course-roadmap-chevron"
                        size={18}
                        aria-hidden="true"
                      />
                    </button>
                    {isExpanded && (
                      <div
                        className="course-roadmap-lessons"
                        id={modulePanelId}
                      >
                        {lessons.slice(0, 4).map((lesson, lessonIndex) => (
                          <div
                            className="course-roadmap-lesson"
                            key={
                              lesson.slug ||
                              lesson.id ||
                              `${moduleKey}-lesson-${lessonIndex}`
                            }
                          >
                            <span
                              className="course-roadmap-lesson-dot"
                              aria-hidden="true"
                            />
                            <span>{lesson.title}</span>
                            {Number(lesson.estimated_minutes) > 0 && (
                              <small>{lesson.estimated_minutes} min</small>
                            )}
                          </div>
                        ))}
                        {lessons.length > 4 && (
                          <p className="course-roadmap-extra">
                            Plus {lessons.length - 4} more lessons in this
                            module.
                          </p>
                        )}
                        {!lessons.length && (
                          <p className="course-roadmap-extra">
                            Lesson previews are not available for this module
                            yet.
                          </p>
                        )}
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="course-outline-state" role="status">
              {outlineError
                ? "The course outline could not be loaded right now."
                : outline
                  ? "No published module outline is available yet."
                  : "Loading the published course outline…"}
            </p>
          )}
          {modules.length > 8 && (
            <p className="course-outline-more">
              Showing 8 of {modules.length} modules. Start learning to explore
              the complete course.
            </p>
          )}
          {modules.length > 0 && (
            <div className="course-outline-footer">
              <span>
                <Layers3 size={15} aria-hidden="true" />{" "}
                {outline?.lesson_count ||
                  modules.reduce(
                    (total, module) =>
                      total +
                      (Array.isArray(module.lessons)
                        ? module.lessons.length
                        : 0),
                    0,
                  )}{" "}
                lessons across this path
              </span>
              <Link
                className="course-outline-footer-link"
                to={resolvedActionTo}
              >
                Explore lessons <ArrowRight size={15} aria-hidden="true" />
              </Link>
            </div>
          )}
        </section>
      )}

      {!available && (
        <p className="course-roadmap-note">
          This track is planned or not yet published. Its live lessons and
          activities will appear here after release.
        </p>
      )}
    </div>
  );
}
