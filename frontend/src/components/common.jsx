import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Award,
  Bookmark,
  BookMarked,
  BookOpen,
  Compass,
  Flame,
  FolderKanban,
  ShieldCheck,
  Sparkles,
  UserRound,
  Code2,
  Zap,
} from "lucide-react";
import { getProfile, formatNumber } from "../lib/demoState.js";
import { useGamificationStats } from "../lib/useGamificationStats.js";
import { useLearnerProgress } from "../lib/useLearnerProgress.js";
import { getCourseLogoUrl } from "../lib/courseLogos.js";
import {
  useBookmarkState,
  loadBookmarkState,
  toggleBookmarkKey,
} from "../lib/bookmarkState.js";

export function PageShell({ children, className = "" }) {
  return <main className={`page-shell ${className}`}>{children}</main>;
}

export function SectionHeading({ eyebrow, title, detail, action }) {
  return (
    <div className="section-heading">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h2>{title}</h2>
        {detail && <p>{detail}</p>}
      </div>
      {action}
    </div>
  );
}

export function SectionTitle({ title, action, to = "/" }) {
  return (
    <div className="section-title-row">
      <h3>{title}</h3>
      {action && (
        <Link to={to} className="text-link">
          {action} <ArrowRight size={14} />
        </Link>
      )}
    </div>
  );
}

export function CourseIcon({ course, size = "lg" }) {
  const [logoFailed, setLogoFailed] = useState(false);
  const logoUrl = getCourseLogoUrl(course);
  useEffect(() => setLogoFailed(false), [course?.slug, logoUrl]);
  return (
    <span
      className={`course-icon course-icon-${size} ${logoUrl && !logoFailed ? "course-icon-with-logo" : ""}`}
      style={{ "--course-color": course.color || "#27d6a0" }}
      aria-hidden="true"
    >
      {logoUrl && !logoFailed ? (
        <img
          src={logoUrl}
          alt=""
          loading="lazy"
          decoding="async"
          onError={() => setLogoFailed(true)}
        />
      ) : (
        course.icon ||
        String(course.title || "CO")
          .slice(0, 3)
          .toUpperCase()
      )}
    </span>
  );
}

export function CourseCard({ course, showDescription = true }) {
  const progress = useLearnerProgress();
  const canShowProgress =
    progress.mode === "remote" || progress.mode === "guest";
  const done = canShowProgress
    ? progress.completedIds.filter((id) => id.startsWith(`${course.slug}:`))
        .length
    : 0;
  const pct =
    course.lessons > 0
      ? Math.min(100, Math.round((done / course.lessons) * 100))
      : 0;
  const available =
    course.status === "Published" || course.status === "Local preview";
  return (
    <Link
      className="course-card panel"
      to={`/courses/${encodeURIComponent(course.slug)}`}
    >
      <div className="course-card-top">
        <CourseIcon course={course} />
        <span
          className={`course-status-pill course-status-${String(
            course.status || "Roadmap",
          )
            .toLowerCase()
            .replaceAll(" ", "-")}`}
        >
          {course.status || "Roadmap"}
        </span>
      </div>
      <h3>{course.title}</h3>
      {showDescription && course.desc && <p>{course.desc}</p>}
      <div className="course-card-bottom">
        <span>
          {available
            ? `${course.lessons} published lessons`
            : "Planned learning path"}
        </span>
        <span className="course-go">
          Course overview <ArrowRight size={14} />
        </span>
      </div>
      {canShowProgress && pct > 0 && (
        <div className="progress-track">
          <span style={{ width: `${pct}%` }} />
        </div>
      )}
    </Link>
  );
}

export function StatsRow({ compact = false }) {
  const statsData = useGamificationStats();
  const stats = [
    {
      icon: Zap,
      value: formatNumber(statsData.totalXp),
      label: "Total XP",
      color: "gold",
    },
    {
      icon: Flame,
      value: String(statsData.currentStreak),
      label: "Day streak",
      color: "orange",
    },
    {
      icon: BookOpen,
      value: formatNumber(statsData.completedLessons),
      label: "Lessons",
      color: "mint",
    },
    {
      icon: Bookmark,
      value: formatNumber(statsData.bookmarks),
      label: "Bookmarks",
      color: "purple",
    },
  ];
  return (
    <div className={`stats-grid ${compact ? "stats-grid-compact" : ""}`}>
      {stats.map((s) => (
        <div className="stat-card panel" key={s.label}>
          <span className={`stat-icon ${s.color}`}>
            <s.icon size={18} />
          </span>
          <div className="stat-value">{s.value}</div>
          <div className="stat-label">{s.label}</div>
        </div>
      ))}
    </div>
  );
}

export function ArrowUpRightIcon() {
  return (
    <span className="arrow-up-right">
      <ArrowRight size={14} />
    </span>
  );
}

export function ToolCard({ icon: Icon, title, desc, to, color }) {
  return (
    <Link className="tool-card panel" to={to}>
      <span className={`tool-icon ${color}`}>
        <Icon size={20} />
      </span>
      <h3>{title}</h3>
      <p>{desc}</p>
      <span className="tool-card-arrow">
        <ArrowRight size={15} />
      </span>
    </Link>
  );
}

export function BookmarkButton({
  id,
  label = "Bookmark lesson",
  small = false,
}) {
  const bookmarkState = useBookmarkState();
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState("");
  const saved =
    bookmarkState.mode === "remote" || bookmarkState.mode === "guest"
      ? bookmarkState.ids.includes(id)
      : false;

  const toggle = async () => {
    if (busy) return;
    setBusy(true);
    setFeedback("");
    try {
      await loadBookmarkState();
      await toggleBookmarkKey(id);
    } catch (error) {
      setFeedback(error?.message || "Bookmark could not be saved. Try again.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <span className="bookmark-control-wrap">
      <button
        type="button"
        className={`bookmark-button ${small ? "bookmark-button-small" : ""} ${saved ? "saved" : ""}`}
        onClick={toggle}
        disabled={busy}
        aria-pressed={saved}
        aria-label={saved ? "Remove bookmark" : label}
        title={saved ? "Remove bookmark" : label}
      >
        {saved ? <BookMarked size={18} /> : <Bookmark size={18} />}
      </button>
      {feedback && (
        <span className="bookmark-feedback" role="status">
          {feedback}
        </span>
      )}
    </span>
  );
}

export function LockIcon() {
  return <ShieldCheck size={18} />;
}

export function EmptyState({ icon: Icon, title, detail, action }) {
  const EmptyIcon = Icon || Compass;
  return (
    <div className="empty-state panel">
      <span className="empty-icon" aria-hidden="true">
        <EmptyIcon size={27} />
      </span>
      <h2>{title}</h2>
      <p>{detail}</p>
      {action}
    </div>
  );
}
