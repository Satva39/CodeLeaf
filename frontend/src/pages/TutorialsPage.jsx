import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { useCourseCatalogState } from "../lib/useCourseCatalog.js";
import {
  filterCourseCatalog,
  COURSE_AVAILABILITY_FILTERS,
  COURSE_LEVEL_FILTERS,
  COURSE_SORT_OPTIONS,
} from "../lib/courseCatalogFilters.js";
import {
  PageShell,
  SectionHeading,
  CourseCard,
  EmptyState,
} from "../components/common.jsx";

export default function TutorialsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { courses, loading, error } = useCourseCatalogState();
  const query = searchParams.get("q") || "";
  const category = searchParams.get("category") || "All";
  const level = searchParams.get("level") || "All levels";
  const status = searchParams.get("status") || "All availability";
  const sort = searchParams.get("sort") || "name-asc";
  const categories = useMemo(
    () => ["All", ...new Set(courses.map((course) => course.category).filter(Boolean).sort())],
    [courses],
  );
  const filtered = useMemo(
    () => filterCourseCatalog(courses, { query, category, level, status, sort }),
    [courses, query, category, level, status, sort],
  );
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
    <PageShell className="tutorials-page">
      <SectionHeading
        eyebrow="THE CODELEAF LIBRARY"
        title="Choose what to learn"
        detail="Follow a clear path, practise the basics, then build something of your own. Course availability reflects the published catalog, not a placeholder claim."
      />
      {error && <p className="catalog-status-note" role="status">The live catalog could not be refreshed. These tracks are shown as roadmap until availability can be checked.</p>}
      <label className="catalog-search panel">
        <Search size={17} />
        <input
          value={query}
          onChange={(event) => updateFilter("q", event.target.value)}
          placeholder="Find a language, framework or tool..."
          aria-label="Search courses"
        />
        <span>{filtered.length} courses</span>
      </label>
      <div className="collection-filter-grid panel tutorial-filter-grid" aria-label="Course filters">
        <label>Learning path
          <select value={category} onChange={(event) => updateFilter("category", event.target.value)}>
            {categories.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
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
      </div>
      {loading && <p className="catalog-status-note" role="status">Refreshing course availability…</p>}
      <div className="course-grid course-grid-catalog">
        {filtered.map((course) => <CourseCard key={course.slug} course={course} showDescription={false} />)}
      </div>
      {!filtered.length && (
        <EmptyState
          icon={Search}
          title="No matching course"
          detail="Try another search term or choose a different learning path, skill level, or availability."
          action={<button type="button" onClick={clearFilters} className="button button-secondary">Clear filters</button>}
        />
      )}
    </PageShell>
  );
}
