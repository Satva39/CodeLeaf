import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Award,
  Check,
  Code2,
  Flame,
  FolderKanban,
  Home,
  ListChecks,
  Monitor,
  Terminal,
  Trophy,
  Zap,
} from "lucide-react";
import { useCourseCatalog } from "../lib/useCourseCatalog.js";
import { getProfile, formatNumber } from "../lib/demoState.js";
import { useGamificationStats } from "../lib/useGamificationStats.js";
import { useLearnerProgress } from "../lib/useLearnerProgress.js";
import {
  PageShell,
  SectionHeading,
  CourseIcon,
  CourseCard,
  StatsRow,
  ArrowUpRightIcon,
  ToolCard,
  BookmarkButton,
} from "../components/common.jsx";
import { Avatar } from "../components/layout/Header.jsx";
import { selectLearningTarget } from "../lib/learningPath.js";
import "../styles/phase3-learning-loop.css";

export default function HomePage() {
  const stats = useGamificationStats();
  const learnerProgress = useLearnerProgress();
  const learningSteps = stats.completedLessons + stats.completedExercises;
  const [category, setCategory] = useState("All");
  const catalog = useCourseCatalog();
  const lastCourseSlug = getProfile().lastCourse;
  const resumeTarget = selectLearningTarget({
    courses: catalog,
    recentItems: learnerProgress.recentItems,
    lastCourseSlug,
  });
  const resumeCourse = resumeTarget.course || null;
  const done = resumeCourse ? learnerProgress.completedIds.filter((id) => id.startsWith(`${resumeCourse.slug}:`)).length : 0;
  const courseLessonCount = Number(resumeCourse?.lessons || 0);
  const courseProgressPercent = courseLessonCount ? Math.min(100, Math.round((done / courseLessonCount) * 100)) : 0;
  const resumeAvailable = Boolean(resumeCourse && ["Published", "Local preview"].includes(resumeCourse.status) && courseLessonCount > 0);
  const categories = ["All", ...new Set(catalog.map((course) => course.category).filter(Boolean).sort())];
  const courses = catalog.filter(
    (c) => category === "All" || c.category === category,
  );
  return (
    <PageShell className="home-page">
      <section className="hero-grid">
        <div className="hero-copy">
          <div className="hero-label">
            <span className="live-dot" /> YOUR NEXT SKILL STARTS HERE
          </div>
          <h1>
            Learn a little.
            <br />
            <span>Build a lot.</span>
          </h1>
          <p className="hero-description">
            Visual lessons, hands-on practice and real projects to help you move
            from curious beginner to confident builder.
          </p>
          <div className="hero-actions">
            <Link
              to={resumeAvailable ? resumeTarget.href : "/tutorials"}
              className="button button-primary"
            >
              {resumeAvailable ? resumeTarget.ctaLabel : "Explore courses"} <ArrowRight size={17} />
            </Link>
            <Link to="/tutorials" className="button button-secondary">
              Explore courses
            </Link>
          </div>
          <div className="hero-proof">
            <div className="proof-avatars">
              <Avatar size="xs" variant="orbit" />
              <Avatar size="xs" variant="code" />
              <Avatar size="xs" variant="spark" />
            </div>
            <span>
              <strong>{stats.mode === "loading" ? "…" : stats.mode === "unavailable" ? "—" : formatNumber(learningSteps)}</strong> learning steps
              completed
            </span>
          </div>
        </div>
        <div className="hero-visual panel">
          <div className="visual-topline">
            <span>
              <span className="live-dot" /> LEARNING SESSION
            </span>
            <span>01 / 04</span>
          </div>
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="visual-code-card">
            <div className="fake-window-bar">
              <span />
              <span />
              <span />
              <small>hello-world.html</small>
            </div>
            <div className="fake-code">
              <span className="code-purple">&lt;main&gt;</span>
              <br />
              &nbsp;&nbsp;<span className="code-green">&lt;h1&gt;</span>Hello,
              world!<span className="code-green">&lt;/h1&gt;</span>
              <br />
              &nbsp;&nbsp;<span className="code-green">&lt;p&gt;</span>Ideas
              become things.<span className="code-green">&lt;/p&gt;</span>
              <br />
              <span className="code-purple">&lt;/main&gt;</span>
            </div>
            <div className="fake-result">
              <span className="result-dot" /> Live preview{" "}
              <span className="result-underline">→</span>
            </div>
          </div>
          <div className="floating-badge badge-xp">
            <Zap size={17} />
            <span>
              <strong>+{stats.lessonXp} XP</strong>
              <small>Per lesson completed</small>
            </span>
          </div>
          <div className="floating-badge badge-streak">
            <Flame size={18} />
            <span>
              <strong>{stats.mode === "loading" ? "Checking streak…" : stats.mode === "unavailable" ? "Streak unavailable" : `${stats.currentStreak} day streak`}</strong>
              <small>
                {stats.mode === "loading"
                  ? "Loading recorded activity"
                  : stats.mode === "unavailable"
                    ? "Activity could not be verified right now"
                    : stats.currentStreak
                      ? "Take the pace that works for you"
                      : "Complete a lesson to begin"}
              </small>
            </span>
          </div>
          <div className="visual-caption">
            <span className="caption-square">
              <Code2 size={17} />
            </span>
            <span>
              <strong>Learn by doing</strong>
              <small>Every concept has a next step</small>
            </span>
            <ArrowUpRightIcon />
          </div>
        </div>
      </section>
      <section className="home-stats-section">
        <StatsRow />
      </section>
      <section className="section-block">
        <SectionHeading
          eyebrow="PICK UP WHERE YOU LEFT OFF"
          title="Your learning path"
          detail="Keep your momentum going with the next small step."
          action={
            <Link to="/progress" className="button button-quiet">
              View progress <ArrowRight size={14} />
            </Link>
          }
        />
        <div className="resume-grid">
          <div className="resume-card panel">
            <div className="resume-icon">
              <CourseIcon course={resumeCourse || catalog[0]} />
            </div>
            <div className="resume-content">
              <div className="eyebrow">{resumeTarget.eyebrow}</div>
              <h3>{resumeTarget.kind === "lesson" ? resumeTarget.lessonTitle : resumeAvailable ? resumeCourse.title.replace(/\s+[—–-]\s+From Beginner to Professional.*$/i, "") : "Choose your first learning path"}</h3>
              <p>
                {resumeTarget.kind === "lesson"
                  ? `${resumeTarget.completed ? "You completed" : "You last opened"} this lesson in ${resumeCourse.title}. Return directly to it, with course progress based on recorded activity.`
                  : resumeAvailable
                    ? (resumeCourse.desc || "Continue through this published course at your own pace.")
                    : "Course outlines and learning activities will appear as individual tracks are reviewed and published. Browse the catalog to choose an available path."}
              </p>
              {resumeTarget.kind === "lesson" && <div className="resume-last-lesson-meta"><span>{resumeCourse.title}</span><span>{resumeTarget.completed ? "Completed" : "Last opened"}</span></div>}
              <div className="resume-progress-label">
                <span>
                  {resumeAvailable ? `${done} of ${courseLessonCount} lessons completed` : "Published course not selected"}
                </span>
                <span>{resumeAvailable ? `${courseProgressPercent}%` : "—"}</span>
              </div>
              {resumeAvailable && <div className="progress-track"><span style={{ width: `${courseProgressPercent}%` }} /></div>}
              <Link to={resumeAvailable ? resumeTarget.href : "/tutorials"} className="button button-primary">
                {resumeAvailable ? resumeTarget.ctaLabel : "Browse course catalog"} <ArrowRight size={15} />
              </Link>
            </div>
            {resumeAvailable && resumeCourse.slug === "html" && <BookmarkButton
              id="html:introduction-to-html"
              label="Save Introduction to HTML"
            />}
          </div>
          <div className="daily-card panel">
            <div className="daily-card-head">
              <span className="daily-icon">
                <Flame size={20} />
              </span>
              <span className="pill pill-mint">DAILY PRACTICE</span>
            </div>
            <h3>Ten minutes count.</h3>
            <p>
              One tiny challenge can keep your learning streak moving forward.
            </p>
            <div className="daily-mini-chart">
              {stats.activityDays.map((day) => (
                <span
                  key={day.date}
                  className={day.active ? "active" : ""}
                  title={day.date}
                  style={{ height: `${day.active ? 90 : 18}%` }}
                />
              ))}
            </div>
            <Link to="/challenges" className="text-link">
              Try a challenge <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>
      <section className="section-block">
        <SectionHeading
          eyebrow="EXPLORE THE LIBRARY"
          title="Find your next skill"
          detail="Choose a path, learn the essentials, then put them to work."
          action={
            <Link to="/tutorials" className="text-link">
              All courses <ArrowRight size={14} />
            </Link>
          }
        />
        <div className="course-category-filter" aria-label="Filter courses by category">
          <div className="course-category-filter__select">
            <label htmlFor="home-course-category">Category</label>
            <select
              id="home-course-category"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              <option value="All">All categories</option>
              {categories.slice(1).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div className="course-category-filter__result" aria-live="polite">
            <strong>{courses.length}</strong> {courses.length === 1 ? "course" : "courses"}
          </div>
          {category !== "All" && (
            <button type="button" className="course-category-filter__clear" onClick={() => setCategory("All")}>
              Clear filter
            </button>
          )}
        </div>
        <div className="course-grid">
          {courses.slice(0, 8).map((course) => (
            <CourseCard key={course.slug} course={course} />
          ))}
        </div>
      </section>
      <section className="section-block build-banner panel">
        <div className="build-illustration">
          <div className="build-window">
            <div className="build-window-head">
              <span />
              <span />
              <span />
            </div>
            <div className="build-window-lines">
              <i />
              <i />
              <i />
              <i />
              <i />
            </div>
            <div className="build-window-preview">
              <Monitor size={33} />
            </div>
          </div>
          <span className="build-spark build-spark-a">✦</span>
          <span className="build-spark build-spark-b">✳</span>
        </div>
        <div className="build-copy">
          <div className="eyebrow">FROM KNOWING TO DOING</div>
          <h2>
            Don't just read the code.
            <br />
            <span>Make something with it.</span>
          </h2>
          <p>
            Follow guided milestones, keep your project files together and build
            a portfolio one project at a time.
          </p>
          <Link to="/projects" className="button button-primary">
            Explore projects <ArrowRight size={16} />
          </Link>
        </div>
        <div className="build-mini-stat">
          <FolderKanban size={22} />
          <strong>Guided</strong>
          <span>project paths</span>
        </div>
      </section>
      <section className="section-block tools-grid-section">
        <div>
          <SectionHeading
            eyebrow="YOUR LEARNING TOOLKIT"
            title="Everything in one workspace"
            detail="Move naturally from concept to practice to proof of progress."
          />
        </div>
        <div className="tool-grid">
          <ToolCard
            icon={Terminal}
            title="Code playground"
            desc="Edit starter code and preview web results."
            to="/playground"
            color="blue"
          />
          <ToolCard
            icon={ListChecks}
            title="Exercises"
            desc="Check understanding with small practical tasks."
            to="/challenges"
            color="green"
          />
          <ToolCard
            icon={Trophy}
            title="Weekly league"
            desc="Celebrate consistency and compare progress."
            to="/leaderboard"
            color="amber"
          />
          <ToolCard
            icon={Award}
            title="Certificates"
            desc="Prepare for an exam and verify your result."
            to="/certificates"
            color="purple"
          />
        </div>
      </section>
    </PageShell>
  );
}
