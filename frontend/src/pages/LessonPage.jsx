import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Award,
  BookMarked,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Crown,
  ExternalLink,
  FileCode2,
  FolderKanban,
  Home,
  ListChecks,
  LoaderCircle,
  AlertCircle,
  Menu,
  Play,
  Rocket,
  ShieldCheck,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import { COURSE_CATALOG, flattenGroups, groupsForCourse } from "../data.js";
import {
  API_BASE,
  writeDemo,
  getProfile,
  recordCompletionLocally,
  rememberRemoteCompletion,
  publishRemoteStats,
  publishGuestStats,
} from "../lib/demoState.js";
import { useGamificationStats } from "../lib/useGamificationStats.js";
import {
  useLearnerProgress,
  confirmRemoteLessonCompletion,
} from "../lib/useLearnerProgress.js";
import { BookmarkButton } from "../components/common.jsx";
import { KnowledgeCheck } from "../components/KnowledgeCheck.jsx";
import {
  apiGetJson,
  peekApiJson,
  invalidateApiCache,
} from "../lib/apiCache.js";

import { defaultCode, getLessonContent } from "../data/lessonContent.js";
import DynamicDiagram from "../components/diagrams/DynamicDiagram.jsx";

const CONCEPT_STEP_ICONS = [FileCode2, BookMarked, Zap, CheckCircle2];

// Be tolerant of legacy or imported reference metadata: some courses store
// `supports` as a string while newer course content uses an array of strings.
function formatSourceSupports(supports) {
  if (Array.isArray(supports)) {
    return supports
      .filter((item) => typeof item === "string" && item.trim())
      .join(", ");
  }
  return typeof supports === "string" ? supports.trim() : "";
}

function CourseSidebar({
  courseSlug,
  currentSlug,
  onNavigate,
  courseGroups,
  courseTitle,
  completedIds,
  progressMode,
}) {
  const groups = courseGroups || groupsForCourse(courseSlug);
  const [expanded, setExpanded] = useState(() =>
    Object.fromEntries(groups.map((g) => [g.title, true])),
  );
  const allItems = flattenGroups(groups);
  const progressEnabled = progressMode === "remote" || progressMode === "guest";
  const completedCount = progressEnabled
    ? allItems.reduce(
        (count, item) =>
          count +
          ((completedIds || []).includes(`${courseSlug}:${item.slug}`) ? 1 : 0),
        0,
      )
    : 0;
  const progressPercent = Math.round(
    (completedCount / Math.max(1, allItems.length)) * 100,
  );
  useEffect(() => {
    // Keep each module's expansion state independent. When the outline data
    // refreshes, preserve the learner's open/closed choices and only initialize
    // newly appearing modules. Opening one module must never collapse another.
    setExpanded((previous) => {
      const next = { ...previous };
      for (const group of groups) {
        if (!Object.prototype.hasOwnProperty.call(next, group.title)) {
          next[group.title] = true;
        }
      }
      return next;
    });
  }, [groups]);
  return (
    <aside className="course-sidebar" aria-label="Course lessons">
      <div className="sidebar-course-heading">
        <span className="sidebar-eyebrow">COURSE PATH</span>
        <h3>
          {courseTitle ||
            (
              COURSE_CATALOG.find((c) => c.slug === courseSlug) ||
              COURSE_CATALOG[0]
            ).title}
        </h3>
        <span className="sidebar-course-type">Tutorial</span>
        <div className="sidebar-progress-meta">
          <span>LESSONS COMPLETED</span>
          <strong>
            {completedCount}
            <span> / {allItems.length}</span>
          </strong>
        </div>
        <div className="sidebar-mini-progress">
          <span style={{ width: `${progressPercent}%` }} />
        </div>
      </div>
      {groups.map((g) => (
        <div className="sidebar-group" key={g.title}>
          <button
            className="sidebar-group-title"
            type="button"
            aria-expanded={Boolean(expanded[g.title])}
            onClick={() =>
              setExpanded((p) => ({ ...p, [g.title]: !p[g.title] }))
            }
          >
            <span className="sidebar-group-title-text">{g.title}</span>
            <span
              className="sidebar-group-count"
              aria-label={`${g.items.length} lessons`}
            >
              {g.items.length}
            </span>
            <ChevronDown
              size={14}
              className={expanded[g.title] ? "" : "collapsed"}
              aria-hidden="true"
            />
          </button>
          {expanded[g.title] && (
            <div className="sidebar-items">
              {g.items.map(([slug, title]) => {
                const completed = (completedIds || []).includes(
                  `${courseSlug}:${slug}`,
                );
                const active = currentSlug === slug;
                return (
                  <Link
                    key={slug}
                    onClick={onNavigate}
                    to={`/learn/${courseSlug}/${slug}`}
                    className={`sidebar-item ${active ? "active" : ""} ${completed ? "completed" : ""}`}
                    aria-current={active ? "page" : undefined}
                    title={title}
                  >
                    <span className="sidebar-item-mark">
                      {completed ? (
                        <Check size={13} />
                      ) : active ? (
                        <span className="active-bar" />
                      ) : null}
                    </span>
                    <span className="sidebar-item-label">{title}</span>
                    {title.toLowerCase().includes("exam") && (
                      <span className="sidebar-lock">
                        <ShieldCheck size={12} />
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      ))}
      <div className="sidebar-bottom-card">
        <span className="sidebar-bottom-icon">
          <Rocket size={16} />
        </span>
        <strong>Ready for a project?</strong>
        <p>Turn what you learn into something real.</p>
        <Link to="/projects">
          View projects <ArrowRight size={13} />
        </Link>
      </div>
    </aside>
  );
}

function contentFromPublishedLesson(apiLesson, fallback) {
  if (!apiLesson?.content) return fallback;
  const doc = apiLesson.content;
  const blocks = Array.isArray(doc.content_blocks) ? doc.content_blocks : [];
  const normalizedType = (block) =>
    String(block?.type || "")
      .toLowerCase()
      .replaceAll("-", "_");
  const diagram = blocks.find((block) => normalizedType(block) === "diagram");
  const codeBlock = blocks.find((block) => normalizedType(block) === "code");
  const listBlock = blocks.find((block) => normalizedType(block) === "list");
  const callout = blocks.find((block) =>
    ["callout", "note", "tip", "warning"].includes(normalizedType(block)),
  );
  const paragraphs = blocks
    .filter(
      (block) =>
        ["paragraph", "text"].includes(normalizedType(block)) &&
        (block.text || block.content),
    )
    .map((block) => ({
      title: block.title || "",
      text: block.text || block.content,
    }));
  const sections = Array.isArray(listBlock?.items) ? listBlock.items : [];
  const handledTypes = new Set([
    "diagram",
    "paragraph",
    "text",
    "list",
    "code",
    "callout",
    "note",
    "tip",
    "warning",
  ]);
  const extraBlocks = blocks.filter(
    (block) => !handledTypes.has(normalizedType(block)),
  );
  const mistakes = (doc.common_mistakes || []).map((mistake) => [
    mistake.problem || "Common mistake",
    mistake.why || "It can make the result confusing or incorrect.",
    mistake.fix ||
      "Use the documented HTML pattern and check the browser result.",
  ]);
  return {
    ...fallback,
    intro: doc.intro || fallback.intro,
    outcomes: apiLesson.learning_outcomes?.length
      ? apiLesson.learning_outcomes
      : fallback.outcomes,
    visualTitle: diagram?.title || fallback.visualTitle,
    visualDescription: diagram?.caption || fallback.visualDescription,
    visualAlt: diagram?.alt_text || "",
    visualAsset: diagram?.asset_path || "",
    visualCaption: diagram?.caption || "",
    visualSteps: fallback.visualSteps,
    paragraphs: paragraphs.length ? paragraphs : fallback.paragraphs,
    sections,
    sectionsTitle: listBlock?.title || "Key ideas",
    tip: callout?.text || callout?.content || fallback.tip,
    tipTitle: callout?.title || "Remember this",
    codeSample: codeBlock?.code || fallback.codeSample,
    codeLanguage: codeBlock?.language || "",
    codeInstructions:
      codeBlock?.run_instructions || codeBlock?.instructions || "",
    codeResetSteps: Array.isArray(codeBlock?.reset_steps)
      ? codeBlock.reset_steps
      : [],
    extraBlocks,
    output:
      codeBlock?.expected_output ||
      codeBlock?.output ||
      doc.expected_output ||
      fallback.output,
    task: doc.task || fallback.task,
    checks: doc.task_acceptance_criteria?.length
      ? doc.task_acceptance_criteria
      : fallback.checks,
    solution:
      [
        ...(doc.hints || []),
        ...(doc.solution_notes ? [doc.solution_notes] : []),
      ].join(" ") || fallback.solution,
    mistakes: mistakes.length ? mistakes : fallback.mistakes,
    recap: doc.summary?.length ? doc.summary : fallback.recap,
    sources: apiLesson.sources || doc.references || [],
    runMode: doc.run_mode || "browser-preview",
  };
}

function structuredBlockType(block) {
  return String(block?.type || "text")
    .toLowerCase()
    .replaceAll("-", "_");
}

function safeExternalUrl(value) {
  if (typeof value !== "string") return "";
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:"
      ? parsed.href
      : "";
  } catch {
    return "";
  }
}

function encodeAssetSegments(path) {
  return String(path || "")
    .replace(/^\/+/, "")
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function StructuredContentBlock({ block, courseSlug, index }) {
  if (!block || typeof block !== "object") return null;
  const type = structuredBlockType(block);
  const title =
    typeof block.title === "string"
      ? block.title
      : typeof block.heading === "string"
        ? block.heading
        : "";
  const text =
    [block.text, block.content, block.description].find(
      (value) => typeof value === "string" && value.trim(),
    ) || "";
  const externalUrl = safeExternalUrl(block.url || block.href || block.src);
  const assetPath =
    typeof block.asset_path === "string" ? block.asset_path : "";
  const localAsset =
    assetPath &&
    !assetPath.split("/").includes("..") &&
    !assetPath.startsWith("/")
      ? `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/assets/${encodeAssetSegments(assetPath)}`
      : "";
  const mediaUrl = externalUrl || localAsset;
  const key = block.id || `${type}-${index}`;
  const heading = title ? <h3>{title}</h3> : null;
  if (["heading", "h2", "h3", "section_heading"].includes(type)) {
    const HeadingTag = type === "h2" ? "h2" : "h3";
    return (
      <section className="lesson-structured-block" key={key}>
        <HeadingTag>{title || text}</HeadingTag>
        {title && text && <p>{text}</p>}
      </section>
    );
  }
  if (["paragraph", "text", "description"].includes(type))
    return (
      <section className="lesson-structured-block" key={key}>
        {heading}
        <p>{text}</p>
      </section>
    );
  if (type === "code")
    return (
      <section className="lesson-structured-block" key={key}>
        {heading}
        <pre>
          <code>{String(block.code || block.source || text)}</code>
        </pre>
      </section>
    );
  if (["output", "expected_output", "result"].includes(type))
    return (
      <section className="lesson-structured-block" key={key}>
        {heading}
        <pre>{String(block.output || block.value || text)}</pre>
      </section>
    );
  if (["list", "bulleted_list", "ordered_list"].includes(type)) {
    const items = Array.isArray(block.items) ? block.items : [];
    const ListTag = type === "ordered_list" || block.ordered ? "ol" : "ul";
    return (
      <section className="lesson-structured-block" key={key}>
        {heading}
        <ListTag>
          {items.map((item, itemIndex) => (
            <li
              key={
                typeof item === "string"
                  ? `${itemIndex}-${item}`
                  : item.id || `${itemIndex}-${item.title || "item"}`
              }
            >
              {typeof item === "string" ? (
                item
              ) : (
                <>
                  {item.title && <strong>{item.title} </strong>}
                  {item.text || item.description || item.label || ""}
                </>
              )}
            </li>
          ))}
        </ListTag>
      </section>
    );
  }
  if (type === "table") {
    const columns = Array.isArray(block.headers)
      ? block.headers
      : Array.isArray(block.columns)
        ? block.columns
        : [];
    const rows = Array.isArray(block.rows) ? block.rows : [];
    return (
      <section className="lesson-structured-block" key={key}>
        {heading}
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {columns.map((column, columnIndex) => (
                  <th key={`${columnIndex}-${String(column)}`}>
                    {typeof column === "string"
                      ? column
                      : column.label || column.title || "Column"}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={row.id || rowIndex}>
                  {(Array.isArray(row)
                    ? row
                    : columns.map(
                        (column) =>
                          row?.[
                            typeof column === "string" ? column : column.key
                          ],
                      )
                  ).map((cell, cellIndex) => (
                    <td key={cellIndex}>
                      {typeof cell === "string" || typeof cell === "number"
                        ? cell
                        : JSON.stringify(cell ?? "")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    );
  }
  if (["image", "media", "video", "audio"].includes(type)) {
    if (!mediaUrl)
      return (
        <section className="lesson-structured-block" key={key}>
          {heading}
          <p>
            {text ||
              "This media asset is unavailable or has an unsupported URL."}
          </p>
        </section>
      );
    if (type === "audio" || block.media_type === "audio")
      return (
        <section className="lesson-structured-block" key={key}>
          {heading}
          <audio controls preload="metadata" src={mediaUrl}>
            {text || "Your browser cannot play this audio."}
          </audio>
        </section>
      );
    if (type === "video" || block.media_type === "video")
      return (
        <section className="lesson-structured-block" key={key}>
          {heading}
          <video
            controls
            preload="metadata"
            poster={safeExternalUrl(block.poster)}
            src={mediaUrl}
          >
            {text || "Your browser cannot play this video."}
          </video>
        </section>
      );
    return (
      <figure className="lesson-structured-block" key={key}>
        {heading}
        <img
          src={mediaUrl}
          alt={String(block.alt || block.alt_text || "")}
          loading="lazy"
        />
        {(block.caption || text) && (
          <figcaption>{block.caption || text}</figcaption>
        )}
      </figure>
    );
  }
  if (["reference", "source", "link"].includes(type)) {
    const url = safeExternalUrl(block.url || block.href);
    return (
      <section className="lesson-structured-block" key={key}>
        {heading}
        {text && <p>{text}</p>}
        {url && (
          <a href={url} target="_blank" rel="noreferrer noopener">
            {block.label || url}
          </a>
        )}
      </section>
    );
  }
  if (["callout", "note", "tip", "warning"].includes(type))
    return (
      <aside className="insight-box lesson-structured-block" key={key}>
        <div>
          <strong>{title || type.replaceAll("_", " ")}</strong>
          <p>{text}</p>
        </div>
      </aside>
    );
  // Unknown block types still show their authored plain-text content instead of silently disappearing.
  if (title || text)
    return (
      <section className="lesson-structured-block" key={key}>
        {heading}
        {text && <p>{text}</p>}
      </section>
    );
  return null;
}

export default function LessonPage() {
  const { courseSlug = "html", lessonSlug } = useParams();
  const navigate = useNavigate();
  const [drawer, setDrawer] = useState(false);
  const [showAnswer, setShowAnswer] = useState(false);
  const [code, setCode] = useState("");
  const [runResult, setRunResult] = useState(false);
  const [adsSuppressed, setAdsSuppressed] = useState(false);
  const [exercises, setExercises] = useState([]);
  const [exerciseAnswers, setExerciseAnswers] = useState({});
  const [exerciseFeedback, setExerciseFeedback] = useState({});
  const [exerciseBusy, setExerciseBusy] = useState({});
  const [exerciseLoading, setExerciseLoading] = useState(true);
  const initialOutlineUrl = `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/outline`;
  const [remoteOutline, setRemoteOutline] = useState(
    () => peekApiJson(initialOutlineUrl, "same-origin", true) || null,
  );
  const [outlineStatus, setOutlineStatus] = useState(() =>
    peekApiJson(initialOutlineUrl, "same-origin", true)?.modules?.length
      ? "ready"
      : "loading",
  );
  const [outlineRetry, setOutlineRetry] = useState(0);
  const [apiLesson, setApiLesson] = useState(null);
  const [lessonContentStatus, setLessonContentStatus] = useState("idle");
  const [lessonRetry, setLessonRetry] = useState(0);
  const stats = useGamificationStats();
  const learnerProgress = useLearnerProgress();
  const [completionError, setCompletionError] = useState("");
  const [completionBusy, setCompletionBusy] = useState(false);
  const [completionNotice, setCompletionNotice] = useState("");
  const catalogCourse =
    COURSE_CATALOG.find((c) => c.slug === courseSlug) || COURSE_CATALOG[0];
  const activeOutline =
    remoteOutline?.slug === courseSlug && remoteOutline?.modules?.length
      ? remoteOutline
      : null;
  const course = activeOutline?.title
    ? { ...catalogCourse, title: activeOutline.title }
    : catalogCourse;
  const groups = useMemo(() => {
    if (activeOutline?.modules?.length) {
      return activeOutline.modules.map((module) => ({
        title: module.title,
        items: module.lessons.map((lesson) => [lesson.slug, lesson.title]),
      }));
    }
    return courseSlug === "html" ? [] : groupsForCourse(course.slug);
  }, [activeOutline, course.slug, courseSlug]);
  const lessons = useMemo(() => {
    if (activeOutline?.modules?.length) {
      return activeOutline.modules.flatMap((module) =>
        module.lessons.map((lesson) => ({ ...lesson, group: module.title })),
      );
    }
    return flattenGroups(groups);
  }, [activeOutline, groups]);
  const currentIndex = Math.max(
    0,
    lessons.findIndex((l) => l.slug === (lessonSlug || lessons[0]?.slug)),
  );
  const current = lessons[currentIndex] || lessons[0] || null;
  const next = lessons[currentIndex + 1];
  const prev = lessons[currentIndex - 1];
  useEffect(() => {
    let active = true;
    const outlineUrl = `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/outline`;
    const cachedOutline = peekApiJson(outlineUrl, "same-origin", true);
    if (cachedOutline?.slug === courseSlug && cachedOutline?.modules?.length) {
      setRemoteOutline(cachedOutline);
      setOutlineStatus("ready");
    } else {
      setRemoteOutline(null);
      setOutlineStatus("loading");
    }
    apiGetJson(outlineUrl, { ttlMs: 300_000, persist: true })
      .then((payload) => {
        if (payload?.slug !== courseSlug || !payload?.modules?.length)
          throw new Error("The course has no available lessons.");
        if (active) {
          setRemoteOutline(payload);
          setOutlineStatus("ready");
        }
      })
      .catch(() => {
        if (active) {
          setRemoteOutline(null);
          setOutlineStatus("error");
        }
      });
    return () => {
      active = false;
    };
  }, [courseSlug, outlineRetry]);
  useEffect(() => {
    if (!activeOutline?.modules?.length || !lessons.length) return;
    if (!lessonSlug || !lessons.some((lesson) => lesson.slug === lessonSlug)) {
      navigate(`/learn/${courseSlug}/${lessons[0].slug}`, { replace: true });
    }
  }, [activeOutline, lessons, lessonSlug, courseSlug, navigate]);
  useEffect(() => {
    let active = true;
    if (!activeOutline || !current?.slug) {
      setApiLesson(null);
      setLessonContentStatus("idle");
      return () => {
        active = false;
      };
    }
    const lessonUrl = `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(current.slug)}`;
    const cachedLesson = peekApiJson(lessonUrl, "same-origin", true);
    setApiLesson(cachedLesson?.slug === current.slug ? cachedLesson : null);
    setLessonContentStatus(
      cachedLesson?.slug === current.slug ? "ready" : "loading",
    );
    apiGetJson(lessonUrl, { ttlMs: 300_000, persist: true })
      .then((payload) => {
        if (payload?.slug !== current.slug)
          throw new Error("Lesson content did not match the requested lesson.");
        if (active) {
          setApiLesson(payload);
          setLessonContentStatus("ready");
        }
      })
      .catch(() => {
        if (active) {
          setApiLesson(null);
          setLessonContentStatus("error");
        }
      });
    return () => {
      active = false;
    };
  }, [activeOutline, courseSlug, current?.slug, lessonRetry]);
  useEffect(() => {
    if (!apiLesson || apiLesson.slug !== current?.slug) return;
    const blocks = apiLesson.content?.content_blocks || [];
    const codeBlock = blocks.find((block) => block.type === "code");
    if (codeBlock?.code) setCode(codeBlock.code);
  }, [apiLesson, current?.slug]);
  useEffect(() => {
    if (!current?.slug) return;
    writeDemo({
      profile: {
        ...getProfile(),
        lastCourse: course.slug,
        lastLesson: current.slug,
      },
    });
    setCode(defaultCode(course.slug));
    setShowAnswer(false);
    setRunResult(false);
    setCompletionError("");
    setCompletionNotice("");
  }, [course.slug, current?.slug]);
  useEffect(() => {
    let active = true;
    apiGetJson(`${API_BASE}/api/me/billing`, {
      credentials: "include",
      ttlMs: 30_000,
    })
      .then((data) => {
        if (!active || !data) return;
        const adFree = (data.entitlements || []).some((item) =>
          ["max", "full_access"].includes(item.plan_id),
        );
        setAdsSuppressed(adFree);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);
  const fallbackContent = getLessonContent(
    course.slug,
    current?.slug,
    current?.title || course.title,
  );
  const content =
    apiLesson?.slug === current?.slug
      ? contentFromPublishedLesson(apiLesson, fallbackContent)
      : fallbackContent;
  const id = current?.slug ? `${course.slug}:${current.slug}` : "";
  const progressAvailable =
    learnerProgress.mode === "remote" || learnerProgress.mode === "guest";
  const completed =
    Boolean(id) &&
    progressAvailable &&
    learnerProgress.completedIds.includes(id);
  useEffect(() => {
    let active = true;
    setExerciseAnswers({});
    setExerciseFeedback({});
    if (!current?.slug) {
      setExercises([]);
      setExerciseLoading(false);
      return () => {
        active = false;
      };
    }
    // Avoid requesting exercises for the static fallback lesson while a
    // non-HTML course outline is still loading (for example, `sass-home`).
    if (courseSlug !== "html" && !activeOutline && outlineStatus !== "error") {
      setExercises([]);
      setExerciseLoading(outlineStatus === "loading");
      return () => {
        active = false;
      };
    }
    const exercisesUrl = `${API_BASE}/api/courses/${encodeURIComponent(course.slug)}/lessons/${encodeURIComponent(current.slug)}/exercises`;
    const cachedExercises = peekApiJson(exercisesUrl, "same-origin", true);
    setExercises(cachedExercises?.items || []);
    setExerciseLoading(!cachedExercises);
    apiGetJson(exercisesUrl, { ttlMs: 300_000, persist: true })
      .then((data) => {
        if (active) setExercises(data.items || []);
      })
      .catch(() => {
        if (active && !cachedExercises) setExercises([]);
      })
      .finally(() => {
        if (active) setExerciseLoading(false);
      });
    return () => {
      active = false;
    };
  }, [
    activeOutline?.slug,
    course.slug,
    courseSlug,
    current?.slug,
    id,
    outlineStatus,
  ]);

  const markComplete = async () => {
    if (!current?.slug || completionBusy) return;
    if (completed) {
      navigate(next ? `/learn/${course.slug}/${next.slug}` : "/projects");
      return;
    }
    setCompletionError("");
    setCompletionNotice("");

    // Guest progress is explicitly local and can be recorded without a failing
    // authenticated round-trip. Account XP is always confirmed by the server.
    if (learnerProgress.mode === "guest") {
      const result = recordCompletionLocally("lesson", id);
      publishGuestStats(result.stats);
      setCompletionNotice(
        result.xpAwarded > 0
          ? `+${result.xpAwarded} XP earned and saved in this browser.`
          : "This lesson was already completed; no duplicate XP was awarded.",
      );
      return;
    }
    if (learnerProgress.mode !== "remote") {
      setCompletionError(
        "Progress is still connecting. Please wait a moment and retry.",
      );
      return;
    }

    setCompletionBusy(true);
    try {
      const response = await apiFetch(
        `${API_BASE}/api/me/progress/${encodeURIComponent(course.slug)}/${encodeURIComponent(current.slug)}`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            time_spent_seconds: 0,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
          }),
        },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok || data.ok === false) {
        if (response.status === 401) {
          setCompletionError(
            "Your session has expired. Sign in again to save account progress and XP.",
          );
        } else {
          setCompletionError(
            data.detail || "Progress was not saved. Please retry.",
          );
        }
        return;
      }

      // Apply the server-confirmed completion and stats synchronously so shared
      // header/progress components update before the learner continues.
      invalidateApiCache("/api/me/progress");
      invalidateApiCache("/api/me/stats");
      rememberRemoteCompletion("lesson", id);
      confirmRemoteLessonCompletion(id);
      if (data.stats) publishRemoteStats(data.stats);
      setCompletionNotice(
        Number(data.xp_awarded) > 0
          ? `+${Number(data.xp_awarded)} XP earned. Your progress is saved.`
          : "Your progress is saved. This lesson has already been rewarded, so no duplicate XP was added.",
      );
    } catch {
      setCompletionError(
        "The API could not be reached, so this lesson was not marked complete. Check the backend and retry.",
      );
    } finally {
      setCompletionBusy(false);
    }
  };

  const submitExercise = async (exercise) => {
    const key = exercise.slug;
    setExerciseBusy((previous) => ({ ...previous, [key]: true }));
    setExerciseFeedback((previous) => ({ ...previous, [key]: null }));
    const answer = exerciseAnswers[key] ?? (exercise.starter?.code || "");
    const isCode =
      Boolean(exercise.starter?.code) && exercise.type !== "choice";
    if (!String(answer).trim()) {
      setExerciseFeedback((previous) => ({
        ...previous,
        [key]: { tone: "error", message: "Enter an answer before submitting." },
      }));
      setExerciseBusy((previous) => ({ ...previous, [key]: false }));
      return;
    }
    try {
      const response = await apiFetch(
        `${API_BASE}/api/me/exercises/${encodeURIComponent(course.slug)}/${encodeURIComponent(current.slug)}/${encodeURIComponent(key)}/submit`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            answer: isCode ? null : answer,
            source_code: isCode ? answer : null,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
          }),
        },
      );
      const data = await response.json().catch(() => ({}));
      if (response.ok && data.ok) {
        if (data.completed) {
          rememberRemoteCompletion(
            "exercise",
            `${course.slug}:${current.slug}:${key}`,
          );
        }
        if (data.stats) publishRemoteStats(data.stats);
        setExerciseFeedback((previous) => ({
          ...previous,
          [key]: {
            tone: data.correct ? "success" : "error",
            message: data.correct
              ? data.xp_awarded
                ? `Correct! ${data.xp_awarded} XP awarded.`
                : "Correct! This exercise has already been rewarded."
              : `Not quite. Review the hint and try again. ${data.xp_awarded ? `${data.xp_awarded} XP awarded.` : ""}`,
          },
        }));
      } else {
        const message =
          response.status === 401
            ? "Sign in to submit a graded exercise and save XP."
            : data.detail || "This exercise could not be graded.";
        setExerciseFeedback((previous) => ({
          ...previous,
          [key]: { tone: "error", message },
        }));
      }
    } catch {
      setExerciseFeedback((previous) => ({
        ...previous,
        [key]: {
          tone: "error",
          message: "The API is not reachable. Start the backend and try again.",
        },
      }));
    } finally {
      setExerciseBusy((previous) => ({ ...previous, [key]: false }));
    }
  };
  const runCode = () => setRunResult(true);
  const resetCode = () => {
    setCode(content.codeSample || defaultCode(course.slug));
    setRunResult(false);
  };

  // Prefer imported API content for any course that has it. While the outline
  // request is pending, avoid flashing static fallback lessons from another schema.
  if (
    (courseSlug === "html" || outlineStatus === "loading") &&
    (outlineStatus !== "ready" || !activeOutline?.modules?.length)
  ) {
    const failed = outlineStatus === "error";
    const unpublished = failed && catalogCourse.status === "Roadmap";
    return (
      <main className="course-resolution-page" aria-live="polite">
        <section className="course-resolution-card panel">
          <div
            className={`course-resolution-icon ${failed ? "is-error" : "is-loading"}`}
          >
            {failed ? (
              <AlertCircle size={25} />
            ) : (
              <LoaderCircle size={25} className="course-resolution-spinner" />
            )}
          </div>
          <h1>
            {failed
              ? unpublished
                ? `${course.title} learning is coming soon`
                : `${course.title} course could not be loaded`
              : `Loading your ${course.title} course…`}
          </h1>
          <p>
            {failed
              ? unpublished
                ? "This learning path is listed in the catalog, but its lessons have not been published yet. Choose a published course to start learning now."
                : "The imported course outline is unavailable right now. Retry, or use the catalog to choose another course."
              : "Fetching the current course outline and lessons. This should only take a moment."}
          </p>
          {failed ? (
            <div className="course-resolution-actions">
              <button
                className="button button-primary"
                onClick={() => setOutlineRetry((value) => value + 1)}
              >
                Retry loading <ArrowRight size={15} />
              </button>
              <Link to="/tutorials" className="button button-secondary">
                {unpublished ? "Explore available courses" : "Browse courses"}
              </Link>
            </div>
          ) : (
            <span className="course-resolution-note">
              Loading the published or local-preview course data…
            </span>
          )}
        </section>
      </main>
    );
  }

  if (
    (courseSlug === "html" || activeOutline) &&
    current?.slug &&
    (lessonContentStatus !== "ready" || apiLesson?.slug !== current.slug)
  ) {
    const failed = lessonContentStatus === "error";
    return (
      <main className="course-resolution-page" aria-live="polite">
        <section className="course-resolution-card panel">
          <div
            className={`course-resolution-icon ${failed ? "is-error" : "is-loading"}`}
          >
            {failed ? (
              <AlertCircle size={25} />
            ) : (
              <LoaderCircle size={25} className="course-resolution-spinner" />
            )}
          </div>
          <h1>
            {failed
              ? "This lesson could not be loaded"
              : `Loading ${current.title}…`}
          </h1>
          <p>
            {failed
              ? "The lesson content could not be retrieved. We have hidden fallback content to avoid showing material that is not part of the imported course."
              : "Fetching the current lesson content and references."}
          </p>
          {failed ? (
            <div className="course-resolution-actions">
              <button
                className="button button-primary"
                onClick={() => setLessonRetry((value) => value + 1)}
              >
                Retry lesson <ArrowRight size={15} />
              </button>
              <Link
                to={`/learn/${course.slug}`}
                className="button button-secondary"
              >
                Return to course start
              </Link>
            </div>
          ) : (
            <span className="course-resolution-note">
              This usually takes only a moment…
            </span>
          )}
        </section>
      </main>
    );
  }

  return (
    <div className="learning-layout">
      <div className={`course-sidebar-wrap ${drawer ? "drawer-open" : ""}`}>
        <button
          className="drawer-close icon-button"
          onClick={() => setDrawer(false)}
          aria-label="Close course navigation"
        >
          <X size={18} />
        </button>
        <CourseSidebar
          key={course.slug}
          courseSlug={course.slug}
          currentSlug={current.slug}
          courseGroups={groups}
          courseTitle={course.title}
          completedIds={learnerProgress.completedIds}
          progressMode={learnerProgress.mode}
          onNavigate={() => setDrawer(false)}
        />
      </div>
      {drawer && (
        <button
          className="drawer-backdrop"
          aria-label="Close sidebar"
          onClick={() => setDrawer(false)}
        />
      )}
      <article className="lesson-main">
        <div className="lesson-breadcrumb">
          <button
            className="mobile-outline-trigger"
            onClick={() => setDrawer(true)}
          >
            <Menu size={16} /> Course outline
          </button>
          <Link to="/tutorials">Tutorials</Link>
          <ChevronRight size={13} />
          <Link to={`/learn/${course.slug}`}>{course.title}</Link>
          <ChevronRight size={13} />
          <span>{current.title}</span>
        </div>
        <div className="lesson-title-row">
          <div>
            <div className="eyebrow">{current.group}</div>
            <h1>
              {current.title === `${course.title} Home`
                ? `${course.title} Tutorial`
                : current.title}
            </h1>
            <p className="lesson-deck">{content.intro}</p>
          </div>
          <BookmarkButton id={id} />
        </div>
        <div className="lesson-navigation">
          <Link
            className={`button button-secondary button-small ${!prev ? "disabled" : ""}`}
            to={prev ? `/learn/${course.slug}/${prev.slug}` : "#"}
            onClick={(e) => !prev && e.preventDefault()}
          >
            <ChevronLeft size={15} /> Previous
          </Link>
          <span className="lesson-count">
            Lesson {currentIndex + 1} of {lessons.length}
          </span>
          <Link
            className={`button button-primary button-small ${!next ? "disabled" : ""}`}
            to={next ? `/learn/${course.slug}/${next.slug}` : "/projects"}
            onClick={(e) => !next && e.preventDefault()}
          >
            {next ? "Next lesson" : "Explore projects"}{" "}
            <ChevronRight size={15} />
          </Link>
        </div>
        <section className="lesson-content-block">
          <h2>What you'll learn</h2>
          <div className="outcome-grid">
            {content.outcomes.map((o, i) => (
              <div key={o} className="outcome-item">
                <span>{String(i + 1).padStart(2, "0")}</span>
                {o}
              </div>
            ))}
          </div>
        </section>
        <section className="visual-explainer">
          <div className="visual-explainer-head">
            <span className="visual-label">
              <Sparkles size={14} /> VISUAL EXPLANATION
            </span>
            <span className="diagram-type">CONCEPT MAP</span>
          </div>
          <h2>{content.visualTitle}</h2>
          <p>{content.visualDescription}</p>
          {content.visualAsset ? (
            <DynamicDiagram
              courseSlug={course.slug}
              assetPath={content.visualAsset}
              title={content.visualTitle}
              description={content.visualDescription}
              caption={content.visualCaption}
              alt={content.visualAlt || content.visualTitle}
            />
          ) : (
            <>
              <div
                className="concept-flow"
                role="list"
                aria-label="Concept steps, in order"
              >
                {content.visualSteps.map((step, i) => {
                  const StepIcon =
                    CONCEPT_STEP_ICONS[i % CONCEPT_STEP_ICONS.length];
                  return (
                    <div
                      className="concept-node-wrap"
                      key={`${i}-${step}`}
                      role="listitem"
                    >
                      <div className={`concept-node node-${i % 4}`}>
                        <div className="concept-node-topline">
                          <span className="concept-node-number">
                            STEP {String(i + 1).padStart(2, "0")}
                          </span>
                          <span
                            className="concept-node-icon"
                            aria-hidden="true"
                          >
                            <StepIcon size={17} strokeWidth={2.1} />
                          </span>
                        </div>
                        <strong>{step}</strong>
                      </div>
                      {i !== content.visualSteps.length - 1 && (
                        <div className="concept-arrow" aria-hidden="true">
                          <ArrowRight size={16} strokeWidth={2.2} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              <div className="diagram-caption">
                <span className="diagram-caption-dot" /> Move from one step to
                the next, then check what changed.
              </div>
            </>
          )}
        </section>
        <section className="lesson-content-block">
          <h2>Understand the idea</h2>
          {content.paragraphs.map((paragraph, paragraphIndex) => {
            const item =
              typeof paragraph === "string"
                ? { title: "", text: paragraph }
                : paragraph;
            return (
              <div
                className="lesson-paragraph"
                key={`${paragraphIndex}-${item.title || item.text}`}
              >
                {item.title && <h3>{item.title}</h3>}
                <p>{item.text}</p>
              </div>
            );
          })}
          {content.sections?.length > 0 && (
            <div className="lesson-topic-sections">
              {content.sectionsTitle && <h3>{content.sectionsTitle}</h3>}
              {content.sections.map((section, sectionIndex) => (
                <section key={section.id || `${sectionIndex}-${section.title}`}>
                  <h3>{section.title || `Key idea ${sectionIndex + 1}`}</h3>
                  <p>{section.text || section.description || ""}</p>
                </section>
              ))}
            </div>
          )}
          <div className="insight-box">
            <div className="insight-icon">
              <CircleHelp size={18} />
            </div>
            <div>
              <strong>{content.tipTitle || "Remember this"}</strong>
              <p>{content.tip}</p>
            </div>
          </div>
          {!!content.extraBlocks?.length && (
            <div className="lesson-extra-content-blocks">
              {content.extraBlocks.map((block, blockIndex) => (
                <StructuredContentBlock
                  key={block.id || `${block.type || "block"}-${blockIndex}`}
                  block={block}
                  courseSlug={course.slug}
                  index={blockIndex}
                />
              ))}
            </div>
          )}
        </section>
        <section className="lesson-content-block">
          <div className="section-title-row">
            <div>
              <h2>See it in code</h2>
              <p>
                {content.runMode === "static-validation"
                  ? "Inspect the example and compare the reference output; use the local interpreter for execution."
                  : "Change the example and run it to explore the result."}
              </p>
            </div>
            <span className="language-badge">
              <span className="language-badge-dot" />
              {course.title}
            </span>
          </div>
          <div className="code-play-card">
            <div className="code-toolbar">
              <div className="code-file">
                <FileCode2 size={15} />{" "}
                {course.slug === "html"
                  ? "index.html"
                  : course.slug === "css"
                    ? "styles.css"
                    : course.slug === "python"
                      ? "main.py"
                      : course.slug === "sql"
                        ? "query.sql"
                        : course.slug === "php"
                          ? "example.php"
                          : course.slug === "swift"
                            ? "main.swift"
                            : course.slug === "sqlite"
                              ? content.codeLanguage === "python"
                                ? "main.py"
                                : "query.sql"
                              : "example.js"}
              </div>
              <div className="code-toolbar-actions">
                <button
                  onClick={() => {
                    navigator.clipboard?.writeText(code).catch(() => {});
                  }}
                >
                  <BookMarked size={14} /> Copy
                </button>
                <button onClick={resetCode}>Reset</button>
                <button className="run-code-button" onClick={runCode}>
                  <Play size={13} fill="currentColor" />{" "}
                  {content.runMode === "static-validation"
                    ? "Show expected output"
                    : "Run example"}
                </button>
              </div>
            </div>
            <div className="code-editor-area">
              <label htmlFor="lesson-code" className="sr-only">
                Edit example code
              </label>
              <textarea
                id="lesson-code"
                spellCheck="false"
                value={code}
                onChange={(e) => {
                  setCode(e.target.value);
                  setRunResult(false);
                }}
              />
              {runResult && (
                <div className="code-result-panel">
                  <div className="code-result-head">
                    <span>
                      <CheckCircle2 size={14} />{" "}
                      {content.runMode === "static-validation"
                        ? "Reference output — not executed"
                        : "Preview updated"}
                    </span>
                    <button
                      onClick={() => setRunResult(false)}
                      aria-label="Close preview status"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  <pre>{content.output}</pre>
                  <small>
                    {content.runMode === "static-validation"
                      ? `Reference output only: this page does not execute ${course.slug === "php" ? "PHP" : course.slug === "python" ? "Python" : course.slug === "sqlite" ? (content.codeLanguage === "python" ? "Python" : "SQL") : "learner code"}. Copy the example and run it in your local interpreter; actual in-page execution requires a separately isolated runner.`
                      : "Demo mode: this starter shows a sample expected result. Production execution must use the appropriate isolated runner."}
                  </small>
                </div>
              )}
            </div>
            {(content.codeInstructions ||
              (content.codeResetSteps?.length || 0) > 0) && (
              <div className="lesson-code-instructions">
                {content.codeInstructions && <p>{content.codeInstructions}</p>}
                {!!content.codeResetSteps.length && (
                  <details>
                    <summary>Reset steps</summary>
                    <ol>
                      {content.codeResetSteps.map((step, stepIndex) => (
                        <li key={`${stepIndex}-${step}`}>{step}</li>
                      ))}
                    </ol>
                  </details>
                )}
              </div>
            )}
            <div className="code-card-footer">
              <span>
                <ShieldCheck size={14} /> Safe learning workspace
              </span>
              <Link to="/playground">
                Open playground <ExternalLink size={13} />
              </Link>
            </div>
          </div>
        </section>
        {exercises.length > 0 && (
          <section className="lesson-content-block exercise-section">
            <div className="section-title-row">
              <div>
                <h2>Practice exercises</h2>
                <p>
                  Complete an exercise correctly to earn its base XP once. The
                  server checks the answer.
                </p>
              </div>
              <span className="language-badge">
                <Zap size={13} /> {stats.exerciseXp} XP each
              </span>
            </div>
            {exercises.map((exercise) => (
              <div className="exercise-card panel" key={exercise.slug}>
                <div className="exercise-card-head">
                  <div>
                    <span className="eyebrow">
                      {exercise.difficulty || "PRACTICE"}
                    </span>
                    <h3>{exercise.title}</h3>
                  </div>
                  <span className="challenge-xp">
                    <Zap size={13} /> {stats.exerciseXp} XP
                  </span>
                </div>
                <p>{exercise.prompt}</p>
                {exercise.type === "choice" &&
                Array.isArray(exercise.starter?.options) ? (
                  <div className="exercise-options">
                    {exercise.starter.options.map((option) => (
                      <label key={option} className="exercise-option">
                        <input
                          type="radio"
                          name={`answer-${exercise.slug}`}
                          value={option}
                          checked={exerciseAnswers[exercise.slug] === option}
                          onChange={() =>
                            setExerciseAnswers((previous) => ({
                              ...previous,
                              [exercise.slug]: option,
                            }))
                          }
                        />
                        {option}
                      </label>
                    ))}
                  </div>
                ) : (
                  <label className="exercise-answer-label">
                    Your answer
                    <textarea
                      rows={exercise.starter?.code ? 5 : 2}
                      spellCheck="false"
                      placeholder={
                        exercise.starter?.code || "Write your answer…"
                      }
                      value={
                        exerciseAnswers[exercise.slug] ??
                        (exercise.starter?.code || "")
                      }
                      onChange={(event) =>
                        setExerciseAnswers((previous) => ({
                          ...previous,
                          [exercise.slug]: event.target.value,
                        }))
                      }
                    />
                  </label>
                )}
                {Array.isArray(exercise.hints) && exercise.hints.length > 0 && (
                  <details className="exercise-hints">
                    <summary>Show hint</summary>
                    {exercise.hints.map((hint) => (
                      <p key={hint}>{hint}</p>
                    ))}
                  </details>
                )}
                <div className="exercise-submit-row">
                  <button
                    className="button button-primary button-small"
                    disabled={Boolean(exerciseBusy[exercise.slug])}
                    onClick={() => submitExercise(exercise)}
                  >
                    {exerciseBusy[exercise.slug] ? "Checking…" : "Check answer"}
                  </button>
                  {exerciseFeedback[exercise.slug] && (
                    <p
                      className={`exercise-feedback ${exerciseFeedback[exercise.slug].tone}`}
                      role="status"
                    >
                      {exerciseFeedback[exercise.slug].message}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </section>
        )}
        {!exerciseLoading && exercises.length === 0 && (
          <section className="lesson-content-block exercise-section exercise-empty">
            <h2>Practice exercises</h2>
            <p>
              {courseSlug === "html"
                ? "There is no exercise attached to this lesson yet. Continue learning or browse the available practice challenges."
                : "Exercises will appear here once this course content and its answer checker have been imported and published."}
            </p>
            <Link to="/challenges" className="text-link">
              Browse published exercises <ArrowRight size={14} />
            </Link>
          </section>
        )}
        <section className="lesson-content-block task-block">
          <div className="task-topline">
            <span className="task-icon">
              <ListChecks size={18} />
            </span>
            <div>
              <span className="eyebrow">YOUR TURN</span>
              <h2>Try it yourself</h2>
            </div>
            <span className="task-xp">
              <Zap size={13} /> +{stats.lessonXp} XP
            </span>
          </div>
          <p>{content.task}</p>
          <div className="task-checklist">
            {content.checks.map((x) => (
              <div key={x}>
                <CheckCircle2 size={15} />
                {x}
              </div>
            ))}
          </div>
          <button
            className="button button-secondary"
            onClick={() => setShowAnswer((v) => !v)}
          >
            {showAnswer
              ? "Hide suggested approach"
              : "Show hint & suggested approach"}{" "}
            <ChevronDown size={15} className={showAnswer ? "rotate-180" : ""} />
          </button>
          {showAnswer && (
            <div className="answer-reveal">
              <strong>Suggested approach</strong>
              <p>{content.solution}</p>
            </div>
          )}
        </section>
        <KnowledgeCheck courseSlug={course.slug} lessonSlug={current.slug} />
        <section className="lesson-content-block mistakes-block">
          <h2>Common mistakes</h2>
          <div className="table-scroll">
            <table className="mistakes-table">
              <thead>
                <tr>
                  <th>Watch out for</th>
                  <th>Why it causes trouble</th>
                  <th>Better approach</th>
                </tr>
              </thead>
              <tbody>
                {content.mistakes.map((m) => (
                  <tr key={m[0]}>
                    <td>{m[0]}</td>
                    <td>{m[1]}</td>
                    <td>{m[2]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        {content.sources?.length > 0 && (
          <section className="lesson-content-block lesson-references">
            <h2>References & further reading</h2>
            <ul>
              {content.sources.map((source) => (
                <li key={`${source.url}-${source.title}`}>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {source.title} <ExternalLink size={12} aria-hidden="true" />
                  </a>
                  <span>
                    {source.publisher || "Official reference"}
                    {source.checked_on ? ` · checked ${source.checked_on}` : ""}
                  </span>
                  {formatSourceSupports(source.supports) && (
                    <p>{formatSourceSupports(source.supports)}</p>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}
        <section className="lesson-content-block recap-block">
          <h2>Quick recap</h2>
          <div className="recap-list">
            {content.recap.map((item) => (
              <div key={item}>
                <CheckCircle2 size={16} />
                {item}
              </div>
            ))}
          </div>
          <div className="lesson-complete-bar">
            <div>
              <strong>
                {completed ? "Lesson completed" : "Ready for the next step?"}
              </strong>
              <p>
                {completed
                  ? learnerProgress.mode === "remote"
                    ? "Your account progress is saved on the server."
                    : "Your guest learning progress is saved in this browser."
                  : "Mark this lesson complete to update your learning path."}
              </p>
            </div>
            <button
              onClick={markComplete}
              className="button button-primary"
              disabled={learnerProgress.mode === "loading"}
            >
              {completed
                ? next
                  ? "Continue learning"
                  : "View projects"
                : "Mark complete"}{" "}
              <ArrowRight size={15} />
            </button>
          </div>
        </section>
        <div className="lesson-bottom-nav">
          <Link
            to={prev ? `/learn/${course.slug}/${prev.slug}` : "#"}
            onClick={(e) => !prev && e.preventDefault()}
            className={!prev ? "disabled" : ""}
          >
            <ArrowLeft size={15} /> {prev ? prev.title : "Course start"}
          </Link>
          <Link
            to={next ? `/learn/${course.slug}/${next.slug}` : "/projects"}
            className={!next ? "disabled" : ""}
          >
            {next ? next.title : "Explore projects"} <ArrowRight size={15} />
          </Link>
        </div>
      </article>
      <aside className="lesson-right-rail">
        <div className="right-rail-card rail-tip">
          <div className="rail-top">
            <span className="rail-card-icon">
              <Sparkles size={16} />
            </span>
            <span className="pill pill-mint">LEARNING TIP</span>
          </div>
          <h3>Small steps add up.</h3>
          <p>
            Run the example, change one thing, and observe what happens before
            moving on.
          </p>
        </div>
        {!adsSuppressed && (
          <div className="rail-ad-slot">
            <span className="ad-label">ADVERTISEMENT SLOT</span>
            <div className="ad-art">
              <div className="ad-art-orbit" />
              <span>
                Learn. Build.
                <br />
                <strong>Repeat.</strong>
              </span>
              <small>Sample ad placement</small>
            </div>
            <p>Limited sponsored placements help support free learning.</p>
          </div>
        )}
        <div className="right-rail-card related-card">
          <div className="eyebrow">KEEP EXPLORING</div>
          <h3>Useful next steps</h3>
          <Link to="/challenges">
            <span>
              <ListChecks size={16} /> Practice exercises
            </span>
            <ChevronRight size={15} />
          </Link>
          <Link to="/projects">
            <span>
              <FolderKanban size={16} /> Guided projects
            </span>
            <ChevronRight size={15} />
          </Link>
          <Link to="/certificates">
            <span>
              <Award size={16} /> Skills exam
            </span>
            <ChevronRight size={15} />
          </Link>
        </div>
        {!adsSuppressed && (
          <div className="rail-upgrade-card">
            <Crown size={18} />
            <div>
              <strong>Go ad-free with Max</strong>
              <p>Focus on the lesson, not the noise.</p>
              <Link to="/plans">
                Compare plans <ArrowRight size={13} />
              </Link>
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
