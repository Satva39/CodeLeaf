import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowUpRight, BookOpen, ExternalLink, Lightbulb, Search } from "lucide-react";
import { API_BASE } from "../lib/demoState.js";
import { useCourseCatalog } from "../lib/useCourseCatalog.js";
import { EmptyState, PageShell } from "../components/common.jsx";
import CourseOverview from "../components/course/CourseOverview.jsx";
import { buildReferenceDetails, flattenCourseOutline, safeExternalHref } from "../lib/referenceDetails.js";
import "../styles/reference-enrichment.css";

export default function ReferencePage() {
  const { courseSlug, referenceSlug } = useParams();
  const courses = useCourseCatalog();
  const course = courses.find((item) => item.slug === courseSlug);
  const [items, setItems] = useState([]);
  const [checkedOn, setCheckedOn] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [outlineLessons, setOutlineLessons] = useState([]);
  const [outlineLoading, setOutlineLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setItems([]);
    apiFetch(`${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/references`, {
      credentials: "include",
      signal: controller.signal,
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "References could not be loaded.");
        return payload;
      })
      .then((payload) => {
        setItems(Array.isArray(payload.items) ? payload.items : []);
        setCheckedOn(payload.checked_on || "");
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message || "References could not be loaded.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [courseSlug]);

  useEffect(() => {
    const controller = new AbortController();
    if (!courseSlug || !referenceSlug) {
      setOutlineLessons([]);
      setOutlineLoading(false);
      return () => controller.abort();
    }

    setOutlineLoading(true);
    apiFetch(`${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/outline`, {
      credentials: "include",
      signal: controller.signal,
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "Course lessons could not be loaded.");
        return payload;
      })
      .then((payload) => setOutlineLessons(flattenCourseOutline(payload.modules)))
      .catch((err) => {
        if (err.name !== "AbortError") setOutlineLessons([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setOutlineLoading(false);
      });
    return () => controller.abort();
  }, [courseSlug, referenceSlug]);

  const filteredItems = useMemo(() => items.filter((item) =>
    `${item.title} ${item.publisher || ""} ${item.source_type || ""} ${item.supports || ""}`
      .toLowerCase().includes(query.trim().toLowerCase())), [items, query]);
  const selectedReference = referenceSlug ? items.find((item) => item.slug === referenceSlug) : null;
  const selectedReferenceDetails = selectedReference
    ? buildReferenceDetails(selectedReference, course, outlineLessons)
    : null;
  const selectedReferenceHref = safeExternalHref(selectedReference?.url);

  if (!course) {
    return (
      <PageShell>
        <EmptyState title="Course not found" detail="Choose a reference library from the References catalog." action={<Link to="/references" className="button button-primary">Browse references</Link>} />
      </PageShell>
    );
  }

  return (
    <PageShell className="course-collection-detail">
      <CourseOverview
        course={course}
        sectionLabel="COURSE REFERENCE LIBRARY"
        pageSuffix="Reference"
        backTo="/references"
        backLabel="All references"
        actionTo={`/learn/${course.slug}`}
        actionLabel="Open tutorial"
        showLearningSections={false}
      />
      {!referenceSlug && <div className="collection-detail-toolbar">
        <div>
          <h2>{course.title.replace(/\s+[—–-]\s+From Beginner to Professional.*$/i, "")} reference links</h2>
          <p>Open an entry for a short explanation, example, and links to related lessons.</p>
        </div>
        <label className="catalog-search panel collection-detail-search">
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search references..." aria-label="Search references" />
          <span>{filteredItems.length}</span>
        </label>
      </div>}
      {checkedOn && <p className="collection-checked-note">Reference index last checked: {checkedOn}</p>}
      {referenceSlug && !loading && !error && selectedReference && selectedReferenceDetails && <article className="panel reference-entry-detail reference-entry-enriched">
        <div className="reference-resource-meta">
          <span>{String(selectedReference.source_type || "reference").replaceAll("_", " ")}</span>
          {selectedReference.publisher && <span>{selectedReference.publisher}</span>}
        </div>
        <h2>{selectedReference.title}</h2>

        <section className="reference-detail-section" aria-labelledby="reference-about-heading">
          <div className="reference-detail-heading">
            <span className="reference-detail-icon"><BookOpen size={17} aria-hidden="true" /></span>
            <div>
              <span className="reference-detail-kicker">RESOURCE GUIDE</span>
              <h3 id="reference-about-heading">About this resource</h3>
            </div>
          </div>
          <p>{selectedReferenceDetails.explanation}</p>
        </section>

        <section className="reference-detail-section reference-topics-section" aria-labelledby="reference-topics-heading">
          <div className="reference-detail-heading">
            <span className="reference-detail-icon"><Search size={17} aria-hidden="true" /></span>
            <div>
              <span className="reference-detail-kicker">AT A GLANCE</span>
              <h3 id="reference-topics-heading">Topics covered</h3>
            </div>
          </div>
          <div className="reference-topic-list">
            {selectedReferenceDetails.topics.map((topic) => <span className="reference-topic-chip" key={topic}>{topic}</span>)}
          </div>
        </section>

        <section className="reference-entry-example reference-example-enriched" aria-labelledby="reference-example-heading">
          <div className="reference-detail-heading">
            <span className="reference-detail-icon"><Lightbulb size={17} aria-hidden="true" /></span>
            <div>
              <span className="reference-detail-kicker">PUT IT TO USE</span>
              <h3 id="reference-example-heading">Example or practical use</h3>
            </div>
          </div>
          <p className="reference-example-text">{selectedReferenceDetails.example}</p>
        </section>

        <div className="reference-resource-actions reference-resource-actions-enriched">
          {selectedReferenceHref ? <a href={selectedReferenceHref} target="_blank" rel="noreferrer noopener">Open official source <ExternalLink size={14} /></a> : <span className="reference-source-unavailable">Official source link is not available.</span>}
          <Link to={`/reference/${encodeURIComponent(course.slug)}`}>Back to reference index <ArrowUpRight size={14} /></Link>
        </div>

        <section className="reference-related-lessons reference-related-lessons-enriched" aria-labelledby="reference-related-heading">
          <div className="reference-related-heading-row">
            <div>
              <span className="reference-detail-kicker">CONTINUE LEARNING</span>
              <h3 id="reference-related-heading">{selectedReferenceDetails.usedFallbackLessons ? "Start with these lessons" : "Related lessons"}</h3>
            </div>
            {selectedReferenceDetails.relatedLessons.length > 0 && <span className="reference-related-count">{selectedReferenceDetails.relatedLessons.length} lessons</span>}
          </div>
          {outlineLoading ? (
            <p className="reference-related-status">Finding matching lessons…</p>
          ) : selectedReferenceDetails.relatedLessons.length ? (
            <div className="reference-related-lesson-grid">
              {selectedReferenceDetails.relatedLessons.map((lesson) => (
                <Link key={lesson.slug} className="reference-related-lesson" to={`/learn/${encodeURIComponent(course.slug)}/${encodeURIComponent(lesson.slug)}`}>
                  <span>{lesson.title}</span><ArrowUpRight size={14} aria-hidden="true" />
                </Link>
              ))}
            </div>
          ) : (
            <p className="reference-related-status">The lesson outline is not available right now. Open the tutorial to continue learning this topic.</p>
          )}
          <Link className="reference-open-tutorial" to={`/learn/${encodeURIComponent(course.slug)}`}>Explore the full tutorial <ArrowUpRight size={14} /></Link>
        </section>
      </article>}
      {referenceSlug && !loading && !error && !selectedReference && <EmptyState title="Reference entry not found" detail="This entry is not present in the course reference index. Return to the index to choose an available entry." action={<Link to={`/reference/${course.slug}`} className="button button-secondary">Back to references</Link>} />}
      {loading ? (
        <div className="panel collection-state">Loading {course.title} references…</div>
      ) : error ? (
        <EmptyState title="References are not available yet" detail={`${error} Check that this course and its reference index have been imported and published.`} action={<Link to="/references" className="button button-secondary">Browse other references</Link>} />
      ) : referenceSlug ? null : filteredItems.length ? (
        <div className="reference-resource-grid">
          {filteredItems.map((item, index) => (
            <article className="reference-resource-card panel" key={`${item.url}-${item.title}`}>
              <div className="reference-resource-number">{String(index + 1).padStart(2, "0")}</div>
              <div className="reference-resource-body">
                <div className="reference-resource-meta">
                  <span>{String(item.source_type || "reference").replaceAll("_", " ")}</span>
                  {item.publisher && <span>{item.publisher}</span>}
                </div>
                <h3><Link to={`/reference/${encodeURIComponent(course.slug)}/${encodeURIComponent(item.slug)}`}>{item.title}</Link></h3>
                {item.supports && <p>{item.supports}</p>}
                {item.checked_on && <small>Checked {item.checked_on}</small>}
                <div className="reference-resource-actions">
                  <Link to={`/reference/${encodeURIComponent(course.slug)}/${encodeURIComponent(item.slug)}`}>Read reference entry <ArrowUpRight size={14} /></Link>
                  {safeExternalHref(item.url) && <a href={safeExternalHref(item.url)} target="_blank" rel="noreferrer noopener">Open source <ExternalLink size={14} /></a>}
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title={query ? "No matching references" : "No published references yet"} detail={query ? "Try a different search term." : "This course will show its reference links when its reference index is published."} action={query ? <button className="button button-secondary" onClick={() => setQuery("")}>Clear search</button> : <Link to="/references" className="button button-secondary">All references</Link>} />
      )}
    </PageShell>
  );
}
