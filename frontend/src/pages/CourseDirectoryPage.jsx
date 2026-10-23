import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, Search, BookMarked, FolderKanban, Code2 } from "lucide-react";
import { PageShell, CourseIcon, EmptyState } from "../components/common.jsx";
import { useCourseCatalogState } from "../lib/useCourseCatalog.js";
import {
  filterCourseCatalog,
  COURSE_AVAILABILITY_FILTERS,
  COURSE_LEVEL_FILTERS,
  COURSE_SORT_OPTIONS,
} from "../lib/courseCatalogFilters.js";

const COLLECTIONS = {
  references: {
    eyebrow: "REFERENCE LIBRARY",
    title: "Explore references by course",
    description: "Choose a language, framework, or tool to open its own reference library. Published entries show their real counts and link to source-specific explanations.",
    noun: "Reference",
    plural: "References",
    route: (slug) => `/reference/${encodeURIComponent(slug)}`,
    icon: BookMarked,
    emptyTitle: "No matching reference courses",
  },
  projects: {
    eyebrow: "PROJECT WORKSHOP",
    title: "Build projects by course",
    description: "Pick the technology you are learning, then explore that course’s published project guides and milestones instead of mixing projects from different tracks.",
    noun: "Projects",
    plural: "Projects",
    route: (slug) => `/projects/${encodeURIComponent(slug)}`,
    icon: FolderKanban,
    emptyTitle: "No matching project courses",
  },
  practice: {
    eyebrow: "PRACTICE LIBRARY",
    title: "Practise one course at a time",
    description: "Select a course to find its published exercises and coding challenges. Unpublished tracks stay clearly marked as roadmap or local preview.",
    noun: "Practice",
    plural: "Practice",
    route: (slug) => `/practice/${encodeURIComponent(slug)}`,
    icon: Code2,
    emptyTitle: "No matching practice courses",
  },
};

function shortTitle(course) {
  return String(course?.title || course?.slug || "Course")
    .replace(/\s+[—–-]\s+From Beginner to Professional.*$/i, "")
    .replace(/\s+Tutorial$/i, "")
    .trim();
}

export default function CourseDirectoryPage({ collection = "references" }) {
  const config = COLLECTIONS[collection] || COLLECTIONS.references;
  const { courses, loading, error } = useCourseCatalogState();
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") || "";
  const category = searchParams.get("category") || "All";
  const level = searchParams.get("level") || "All levels";
  const status = searchParams.get("status") || "All availability";
  const sort = searchParams.get("sort") || "name-asc";
  const [filtersOpen, setFiltersOpen] = useState(false);
  const categories = useMemo(
    () => ["All", ...new Set(courses.map((course) => course.category).filter(Boolean).sort())],
    [courses],
  );
  const filtered = useMemo(
    () => filterCourseCatalog(courses, { query, category, level, status, sort }),
    [courses, query, category, level, status, sort],
  );
  const CollectionIcon = config.icon;
  const updateFilter = (key, value) => {
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      if (!value || value === "All" || value === "All levels" || value === "All availability" || value === "name-asc") next.delete(key);
      else next.set(key, value);
      return next;
    }, { replace: true });
  };
  const clearFilters = () => setSearchParams({}, { replace: true });

  return (
    <PageShell className="course-directory-page">
      <section className="collection-hero panel">
        <div className="collection-hero-icon"><CollectionIcon size={25} /></div>
        <div className="eyebrow">{config.eyebrow}</div>
        <h1>{config.title}</h1>
        <p>{config.description}</p>
        <div className="collection-hero-foot">
          <span><strong>{courses.length}</strong> course tracks</span>
          <span>Grouped by technology</span>
          <span>Course-specific pages</span>
        </div>
      </section>

      {error && <p className="catalog-status-note" role="status">Live availability could not be refreshed. The local list is shown as a roadmap until the API is available.</p>}
      <label className="catalog-search panel collection-search">
        <Search size={17} />
        <input
          value={query}
          onChange={(event) => updateFilter("q", event.target.value)}
          placeholder={`Search ${config.plural.toLowerCase()} by language, framework, or tool...`}
          aria-label={`Search ${config.plural.toLowerCase()} by course`}
        />
        <span>{filtered.length} courses</span>
      </label>

      <div className="collection-filter-toolbar collection-directory-toolbar">
        <label className="collection-category-picker">
          <span>Learning path</span>
          <select value={category} onChange={(event) => updateFilter("category", event.target.value)} aria-label="Filter by learning path">
            {categories.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <button type="button" className="button button-secondary button-small" aria-expanded={filtersOpen} onClick={() => setFiltersOpen((value) => !value)}>
          {filtersOpen ? "Hide filters" : "More filters & sort"}
        </button>
        <span>{loading ? "Refreshing catalog…" : `${filtered.length} of ${courses.length} tracks`}</span>
        {(category !== "All" || level !== "All levels" || status !== "All availability" || sort !== "name-asc" || query) && <button type="button" className="text-link" onClick={clearFilters}>Clear filters</button>}
      </div>
      {filtersOpen && <div className="collection-filter-grid collection-secondary-filter-grid panel" aria-label="Additional course filters">
        <label>Skill level
          <select value={level} onChange={(event) => updateFilter("level", event.target.value)}>
            {COURSE_LEVEL_FILTERS.map((item) => <option key={item} value={item}>{item}</option>)}
            {!COURSE_LEVEL_FILTERS.includes(level) && <option value={level}>{level}</option>}
          </select>
        </label>
        <label>Availability
          <select value={status} onChange={(event) => updateFilter("status", event.target.value)}>
            {COURSE_AVAILABILITY_FILTERS.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label>Sort by
          <select value={sort} onChange={(event) => updateFilter("sort", event.target.value)}>
            {COURSE_SORT_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
          </select>
        </label>
      </div>}
      {filtered.length ? (
        <div className="collection-course-grid">
          {filtered.map((course) => {
            const title = shortTitle(course);
            const contentCount = collection === "references" ? course.references : collection === "projects" ? course.projects : course.practice;
            const contentLabel = collection === "references" ? "references" : collection === "projects" ? "projects" : "practice tasks";
            return (
              <Link to={config.route(course.slug)} className="collection-course-card panel" key={course.slug}>
                <div className="collection-course-card-top">
                  <CourseIcon course={course} size="xl" />
                  <span className={`course-status-pill course-status-${course.status.toLowerCase().replaceAll(" ", "-")}`}>{course.status}</span>
                </div>
                <span className="collection-course-category">{course.category || "Technology"}</span>
                <h2>{title} {config.noun}</h2>
                <div className="collection-content-counts" aria-label="Published content counts">
                  <span>{course.lessons} lessons</span>
                  <span>{contentCount} {contentLabel}</span>
                  {collection !== "projects" && <span>{course.projects} projects</span>}
                </div>
                <div className="collection-course-card-foot">
                  <span>{course.status === "Roadmap" ? `Explore ${title} roadmap` : collection === "references" ? `Open ${title} references` : collection === "projects" ? `View ${title} projects` : `Practice ${title}`}</span>
                  <ArrowRight size={16} />
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={Search}
          title={config.emptyTitle}
          detail="No course matches these filters. Try another search or clear the filters."
          action={<button className="button button-secondary" onClick={clearFilters}>Clear filters</button>}
        />
      )}
    </PageShell>
  );
}
