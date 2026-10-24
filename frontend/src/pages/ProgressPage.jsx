import { useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  Check,
  ChevronRight,
  Flame,
  GraduationCap,
} from "lucide-react";
import { useLearnerProgress } from "../lib/useLearnerProgress.js";
import { useCourseCatalogState } from "../lib/useCourseCatalog.js";
import { useGamificationStats } from "../lib/useGamificationStats.js";
import { formatLearningStat } from "../lib/learningPath.js";
import "../styles/phase3-learning-loop.css";
import {
  PageShell,
  SectionTitle,
  CourseIcon,
  EmptyState,
} from "../components/common.jsx";

export default function ProgressPage() {
  const stats = useGamificationStats();
  const learnerProgress = useLearnerProgress();
  const completedIds = learnerProgress.completedIds;
  const recentItems = Array.isArray(learnerProgress.recentItems) ? learnerProgress.recentItems : [];
  const {
    courses: catalog,
    loading: catalogLoading,
    error: catalogError,
  } = useCourseCatalogState();

  const rows = useMemo(
    () =>
      catalog
        .map((course) => {
          const courseDone = completedIds.filter((id) =>
            id.startsWith(`${course.slug}:`),
          ).length;
          // Never substitute legacy static lesson groups for the imported course.
          // A zero here means the API catalog is still loading or unavailable.
          const lessonCount =
            Number(course.lessons) > 0 ? Number(course.lessons) : 0;
          return {
            ...course,
            done: courseDone,
            lessonCount,
            pct: lessonCount
              ? Math.min(100, Math.round((courseDone / lessonCount) * 100))
              : null,
          };
        })
        .filter((course) => course.done > 0)
        .sort((a, b) => b.done - a.done || a.title.localeCompare(b.title)),
    [completedIds, catalog],
  );

  const latestRecorded = recentItems[0] || null;
  const latestCourse = latestRecorded ? catalog.find((course) => course.slug === latestRecorded.course_slug) : null;
  const latestDate = latestRecorded?.last_opened_at ? new Date(latestRecorded.last_opened_at) : null;
  const quickStats = [
    ["Total XP", formatLearningStat(stats.totalXp, stats.mode)],
    ["Lessons completed", formatLearningStat(stats.completedLessons, stats.mode)],
    ["Exercises completed", formatLearningStat(stats.completedExercises, stats.mode)],
    ["Exercise attempts", formatLearningStat(stats.exercisesAttempted, stats.mode)],
    ["Exams passed", formatLearningStat(stats.examsPassed || 0, stats.mode)],
    ["Certificates", formatLearningStat(stats.certificates, stats.mode)],
  ];

  return (
    <PageShell>
      <div className="page-heading-card panel">
        <div>
          <div className="eyebrow">YOUR LEARNING DATA</div>
          <h1>My progress</h1>
          <p>
            Your totals update as lessons and verified exercises are completed.
          </p>
        </div>
        <div className="page-heading-art">
          <Activity size={28} />
        </div>
        <div className="progress-stat-row">
          {quickStats.map(([label, value]) => (
            <div key={label}>
              <small>{label}</small>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>
      {stats.mode === "loading" && <p role="status" className="phase3-data-note">Loading your latest recorded learning statistics…</p>}
      {stats.mode === "unavailable" && <p role="status" className="phase3-data-note phase3-data-note-warning">We couldn't verify your latest account statistics. Values are shown as unavailable rather than as zero.</p>}
      {learnerProgress.mode === "unavailable" && (
        <p role="status" className="project-empty-note">
          Progress is temporarily unavailable. The page will not infer account
          activity from local browser data.
        </p>
      )}
      {learnerProgress.mode === "guest" && (
        <p role="status" className="catalog-status-note">Guest progress is stored on this device only. Sign in to keep account progress in sync across devices.</p>
      )}
      <div className="progress-resume-grid">
        <section className="panel progress-resume-card">
          <div className="eyebrow">CONTINUE LEARNING</div>
          <h2>{latestRecorded ? (latestRecorded.completed ? "Review a recent lesson" : "Return to your last lesson") : "Choose your next step"}</h2>
          {latestRecorded && latestCourse ? <>
            <p><strong>{latestRecorded.title}</strong> · {latestCourse.title}</p>
            {latestDate && !Number.isNaN(latestDate.getTime()) && <small>Last recorded {latestDate.toLocaleDateString()}</small>}
            <div className="progress-next-actions">
              <Link className="button button-primary" to={`/learn/${encodeURIComponent(latestRecorded.course_slug)}/${encodeURIComponent(latestRecorded.lesson_slug)}`}>Open lesson <ArrowRight size={14} /></Link>
              <Link className="button button-secondary" to={`/practice/${encodeURIComponent(latestRecorded.course_slug)}`}>Practise this course <Activity size={14} /></Link>
            </div>
          </> : <>
            <p>{learnerProgress.mode === "guest" ? "Complete a lesson to start a local learning history. Your guest records remain separate from account data." : "Your most recently opened lesson will appear here when a server progress record is available."}</p>
            <Link className="button button-secondary" to="/tutorials">Browse published courses <ArrowRight size={14} /></Link>
          </>}
        </section>
        <section className="panel progress-recent-card">
          <div className="eyebrow">RECENTLY RECORDED</div>
          <h2>Lesson history</h2>
          {recentItems.length ? <div className="progress-recent-list">
            {recentItems.slice(0, 4).map((item) => <Link key={`${item.course_slug}:${item.lesson_slug}`} to={`/learn/${encodeURIComponent(item.course_slug)}/${encodeURIComponent(item.lesson_slug)}`}>
              <span><strong>{item.title}</strong><small>{item.completed ? "Completed lesson" : "Lesson activity"}</small></span>
              <ArrowRight size={14} />
            </Link>)}
          </div> : <p>{learnerProgress.mode === "guest" ? "Recent timestamps are not stored for guest activity." : "No recent lesson records yet."}</p>}
        </section>
      </div>
      <div className="content-two-col">
        <div className="panel progress-list-panel">
          <SectionTitle
            title="Courses in progress"
            action="Browse courses"
            to="/tutorials"
          />
          {rows.length ? (
            rows.map((course) => (
              <Link
                to={`/learn/${course.slug}`}
                className="progress-course-row"
                key={course.slug}
              >
                <CourseIcon course={course} size="md" />
                <div className="progress-course-info">
                  <div>
                    <strong>{course.title}</strong>
                    <span>
                      {course.lessonCount > 0
                        ? `${course.done} / ${course.lessonCount} · ${course.pct}%`
                        : catalogLoading
                          ? "Loading course details…"
                          : catalogError
                            ? "Course details unavailable"
                            : `${course.done} lessons completed`}
                    </span>
                  </div>
                  {course.lessonCount > 0 && (
                    <div className="progress-track">
                      <span style={{ width: `${course.pct}%` }} />
                    </div>
                  )}
                </div>
                <ChevronRight size={17} />
              </Link>
            ))
          ) : (
            <EmptyState
              icon={Activity}
              title="Your learning history will appear here"
              detail="Complete a published lesson to start tracking course progress."
              action={
                <Link to="/tutorials" className="button button-primary">
                  Browse courses <ArrowRight size={15} />
                </Link>
              }
            />
          )}
        </div>
        <div className="side-stack">
          <div className="panel habit-panel">
            <div className="habit-top">
              <Flame size={20} />
              <span className="pill pill-mint">LEARNING STREAK</span>
            </div>
            <h3>
              {stats.currentStreak} day{stats.currentStreak === 1 ? "" : "s"}
            </h3>
            <p>
              Your streak counts days with recorded learning activity. Take the pace that works for you. Longest streak: {stats.longestStreak} day
              {stats.longestStreak === 1 ? "" : "s"}.
            </p>
            <div className="streak-days">
              {stats.activityDays.map((day) => (
                <div
                  key={day.date}
                  className={day.active ? "done" : ""}
                  title={day.date}
                >
                  <span>{day.label}</span>
                  <b>{day.active ? <Check size={13} /> : "·"}</b>
                </div>
              ))}
            </div>
          </div>
          <div className="panel next-step-panel">
            <GraduationCap size={22} />
            <h3>Next milestone</h3>
            <p>
              Complete lessons, practise the exercises, then take an available
              skills exam.
            </p>
            <Link to="/certificates" className="text-link">
              Explore exams <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
