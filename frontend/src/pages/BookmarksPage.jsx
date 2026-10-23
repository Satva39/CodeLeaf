import { useMemo } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Bookmark, RefreshCw } from "lucide-react";
import { COURSE_CATALOG, flattenGroups, groupsForCourse } from "../data.js";
import { getBookmarks } from "../lib/demoState.js";
import { useCourseCatalogState } from "../lib/useCourseCatalog.js";
import { useBookmarkState, loadBookmarkState } from "../lib/bookmarkState.js";
import { PageShell, CourseIcon, BookmarkButton, EmptyState } from "../components/common.jsx";

function friendlyLessonSlug(slug) {
  return String(slug || "Saved lesson").replaceAll("-", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function BookmarksPage() {
  const bookmarkState = useBookmarkState();
  const { courses } = useCourseCatalogState();
  const guestEntries = useMemo(() => getBookmarks().map((id) => {
    const [courseSlug, lessonSlug] = id.split(":");
    const course = courses.find((item) => item.slug === courseSlug) || COURSE_CATALOG.find((item) => item.slug === courseSlug);
    if (!course || !lessonSlug) return null;
    const lesson = flattenGroups(groupsForCourse(courseSlug)).find((item) => item.slug === lessonSlug);
    return { id, course_slug: courseSlug, lesson_slug: lessonSlug, title: lesson?.title || friendlyLessonSlug(lessonSlug), group: lesson?.group || "Saved lesson", course_title: course.title };
  }).filter(Boolean), [courses, bookmarkState.mode, bookmarkState.ids]);

  const entries = bookmarkState.mode === "remote"
    ? bookmarkState.items.map((item) => {
      const course = courses.find((candidate) => candidate.slug === item.course_slug) || COURSE_CATALOG.find((candidate) => candidate.slug === item.course_slug);
      return { ...item, id: `${item.course_slug}:${item.lesson_slug}`, course_title: course?.title || friendlyLessonSlug(item.course_slug), group: "Account bookmark" };
    })
    : bookmarkState.mode === "guest"
      ? guestEntries
      : [];

  return (
    <PageShell>
      <div className="wide-page-heading panel">
        <div>
          <div className="eyebrow">KEEP WHAT MATTERS</div>
          <h1>Bookmarks</h1>
          <p>Saved lessons are kept with your account when signed in. Guest bookmarks stay on this device.</p>
        </div>
        <Bookmark size={35} />
      </div>
      {bookmarkState.mode === "loading" || bookmarkState.mode === "idle" ? (
        <div className="panel collection-state" role="status">Loading saved lessons…</div>
      ) : bookmarkState.mode === "unavailable" ? (
        <EmptyState icon={Bookmark} title="Bookmarks are temporarily unavailable" detail="We could not confirm whether account bookmarks are available. No local data was substituted for authenticated records." action={<button type="button" className="button button-secondary" onClick={() => void loadBookmarkState({ force: true })}><RefreshCw size={14} /> Retry</button>} />
      ) : entries.length ? (
        <div className="saved-list panel">
          {entries.map((entry) => {
            const course = courses.find((item) => item.slug === entry.course_slug) || COURSE_CATALOG.find((item) => item.slug === entry.course_slug);
            return <div key={entry.id} className="saved-row">
              <CourseIcon course={course} size="md" />
              <div>
                <strong>{entry.title || friendlyLessonSlug(entry.lesson_slug)}</strong>
                <p>{entry.course_title || course?.title || entry.course_slug} · {entry.group || "Saved lesson"}</p>
              </div>
              <Link className="button button-secondary button-small" to={`/learn/${encodeURIComponent(entry.course_slug)}/${encodeURIComponent(entry.lesson_slug)}`}>
                Open lesson <ArrowRight size={14} />
              </Link>
              <BookmarkButton id={entry.id} small />
            </div>;
          })}
        </div>
      ) : (
        <EmptyState
          icon={Bookmark}
          title="No saved lessons yet"
          detail={bookmarkState.mode === "remote" ? "Your account has no saved lessons. Use the bookmark control in a lesson to save one across devices." : "Save a lesson with its bookmark icon and it will remain available in this browser."}
          action={<Link to="/tutorials" className="button button-primary">Explore courses <ArrowRight size={15} /></Link>}
        />
      )}
    </PageShell>
  );
}
