import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Bookmark, Filter, RefreshCw, Search, X } from "lucide-react";
import { COURSE_CATALOG, flattenGroups, groupsForCourse } from "../data.js";
import { getBookmarks } from "../lib/demoState.js";
import { useCourseCatalogState } from "../lib/useCourseCatalog.js";
import { useBookmarkState, loadBookmarkState } from "../lib/bookmarkState.js";
import { PageShell, CourseIcon, BookmarkButton, EmptyState } from "../components/common.jsx";
import "../styles/phase3c-personal-learning.css";

function friendlyLessonSlug(slug) {
  return String(slug || "Saved lesson").replaceAll("-", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function buildGuestEntries(courses) {
  return getBookmarks().map((id) => {
    const [courseSlug, lessonSlug] = String(id).split(":");
    const course = courses.find((item) => item.slug === courseSlug) || COURSE_CATALOG.find((item) => item.slug === courseSlug);
    if (!course || !lessonSlug) return null;
    const lesson = flattenGroups(groupsForCourse(courseSlug)).find((item) => item.slug === lessonSlug);
    return {
      id,
      course_slug: courseSlug,
      lesson_slug: lessonSlug,
      title: lesson?.title || friendlyLessonSlug(lessonSlug),
      group: lesson?.group || "Saved lesson",
      course_title: course.title,
    };
  }).filter(Boolean);
}

export default function BookmarksPage() {
  const bookmarkState = useBookmarkState();
  const { courses } = useCourseCatalogState();
  const [query, setQuery] = useState("");
  const [courseFilter, setCourseFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("course");

  const entries = useMemo(() => {
    if (bookmarkState.mode === "remote") {
      return bookmarkState.items.map((item) => {
        const course = courses.find((candidate) => candidate.slug === item.course_slug) || COURSE_CATALOG.find((candidate) => candidate.slug === item.course_slug);
        return {
          ...item,
          id: `${item.course_slug}:${item.lesson_slug}`,
          title: item.title || friendlyLessonSlug(item.lesson_slug),
          course_title: course?.title || friendlyLessonSlug(item.course_slug),
          group: item.group || "Saved lesson",
        };
      });
    }
    return bookmarkState.mode === "guest" ? buildGuestEntries(courses) : [];
  }, [bookmarkState.mode, bookmarkState.items, bookmarkState.ids, courses]);

  const courseOptions = useMemo(() => {
    const unique = new Map();
    entries.forEach((entry) => {
      const slug = entry.course_slug;
      if (slug && !unique.has(slug)) unique.set(slug, { slug, title: entry.course_title || friendlyLessonSlug(slug) });
    });
    return [...unique.values()].sort((a, b) => a.title.localeCompare(b.title));
  }, [entries]);

  const filteredEntries = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return entries.filter((entry) => {
      if (courseFilter !== "all" && entry.course_slug !== courseFilter) return false;
      if (!normalized) return true;
      return [entry.title, entry.lesson_slug, entry.course_title, entry.course_slug, entry.group]
        .some((value) => String(value || "").toLowerCase().includes(normalized));
    }).sort((a, b) => {
      if (sortOrder === "title") return String(a.title).localeCompare(String(b.title));
      const courseCompare = String(a.course_title).localeCompare(String(b.course_title));
      return courseCompare || String(a.title).localeCompare(String(b.title));
    });
  }, [entries, query, courseFilter, sortOrder]);

  const activeFilters = Boolean(query.trim() || courseFilter !== "all");
  const clearFilters = () => { setQuery(""); setCourseFilter("all"); setSortOrder("course"); };
  const bookmarkModeLabel = bookmarkState.mode === "remote" ? "Synced to your account" : "Saved on this device";

  return (
    <PageShell>
      <section className="phase3c-bookmarks-hero panel" aria-labelledby="bookmarks-title">
        <div className="phase3c-bookmarks-hero-copy">
          <div className="eyebrow">YOUR LEARNING LIBRARY</div>
          <h1 id="bookmarks-title">Bookmarks</h1>
          <p>Keep useful lessons close. Search your saved items or narrow the list to one course.</p>
          <div className="phase3c-bookmarks-meta">
            <span><Bookmark size={15} aria-hidden="true" /> {entries.length} saved {entries.length === 1 ? "lesson" : "lessons"}</span>
            <span>{courseOptions.length} {courseOptions.length === 1 ? "course" : "courses"}</span>
            <span>{bookmarkModeLabel}</span>
          </div>
        </div>
        <div className="phase3c-bookmarks-hero-icon" aria-hidden="true"><Bookmark size={32} /></div>
      </section>

      {bookmarkState.mode === "loading" || bookmarkState.mode === "idle" ? (
        <div className="panel collection-state" role="status">Loading your saved lessons…</div>
      ) : bookmarkState.mode === "unavailable" ? (
        <EmptyState icon={Bookmark} title="Bookmarks are temporarily unavailable" detail="We could not confirm whether account bookmarks are available. No local data was substituted for authenticated records." action={<button type="button" className="button button-secondary" onClick={() => void loadBookmarkState({ force: true })}><RefreshCw size={14} /> Retry</button>} />
      ) : entries.length === 0 ? (
        <EmptyState
          icon={Bookmark}
          title="Your learning library starts here"
          detail={bookmarkState.mode === "remote" ? "Save lessons with the bookmark control while learning, and they'll be available here across your signed-in devices." : "Save a lesson with its bookmark control and it will remain available in this browser. Sign in to sync bookmarks across devices."}
          action={<Link to="/tutorials" className="button button-primary">Explore courses <ArrowRight size={15} /></Link>}
        />
      ) : (
        <section className="phase3c-bookmarks-workspace" aria-label="Saved lesson library">
          <div className="panel phase3c-bookmarks-controls">
            <label className="phase3c-bookmark-search">
              <span className="phase3c-sr-only">Search saved lessons</span>
              <Search size={17} aria-hidden="true" />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search lessons or courses…" type="search" />
              {query && <button type="button" className="phase3c-clear-search" onClick={() => setQuery("")} aria-label="Clear search"><X size={15} /></button>}
            </label>
            <label className="phase3c-bookmark-select">
              <span><Filter size={14} aria-hidden="true" /> Course</span>
              <select value={courseFilter} onChange={(event) => setCourseFilter(event.target.value)}>
                <option value="all">All courses</option>
                {courseOptions.map((course) => <option key={course.slug} value={course.slug}>{course.title}</option>)}
              </select>
            </label>
            <label className="phase3c-bookmark-select">
              <span>Sort by</span>
              <select value={sortOrder} onChange={(event) => setSortOrder(event.target.value)}>
                <option value="course">Course</option>
                <option value="title">Lesson title</option>
              </select>
            </label>
          </div>

          <div className="phase3c-bookmarks-results-bar">
            <p role="status" aria-live="polite">Showing <strong>{filteredEntries.length}</strong> of <strong>{entries.length}</strong> saved {entries.length === 1 ? "lesson" : "lessons"}</p>
            {activeFilters && <button type="button" className="phase3c-reset-filters" onClick={clearFilters}>Clear filters <X size={14} /></button>}
          </div>

          {filteredEntries.length === 0 ? (
            <EmptyState icon={Search} title="No matching bookmarks" detail="Try another lesson name or select a different course." action={<button type="button" className="button button-secondary" onClick={clearFilters}>Clear filters</button>} />
          ) : (
            <div className="phase3c-bookmark-list">
              {filteredEntries.map((entry) => {
                const course = courses.find((item) => item.slug === entry.course_slug) || COURSE_CATALOG.find((item) => item.slug === entry.course_slug);
                return (
                  <article key={entry.id} className="phase3c-bookmark-card">
                    <CourseIcon course={course} size="md" />
                    <div className="phase3c-bookmark-card-copy">
                      <p className="phase3c-bookmark-course">{entry.course_title || course?.title || entry.course_slug}</p>
                      <h2>{entry.title || friendlyLessonSlug(entry.lesson_slug)}</h2>
                      <p className="phase3c-bookmark-context">{entry.group || "Saved lesson"}</p>
                    </div>
                    <div className="phase3c-bookmark-actions">
                      <Link className="button button-secondary button-small" to={`/learn/${encodeURIComponent(entry.course_slug)}/${encodeURIComponent(entry.lesson_slug)}`}>Open lesson <ArrowRight size={14} /></Link>
                      <BookmarkButton id={entry.id} small />
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      )}
    </PageShell>
  );
}
