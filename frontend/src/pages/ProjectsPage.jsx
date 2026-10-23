import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, FolderKanban, ListChecks, Search, Terminal } from "lucide-react";

import { PageShell, EmptyState } from "../components/common.jsx";
import { API_BASE } from "../lib/demoState.js";
import { useCourseCatalog } from "../lib/useCourseCatalog.js";
import CourseOverview from "../components/course/CourseOverview.jsx";

function ProjectCard({ project, courseSlug }) {
  const milestoneCount = Array.isArray(project.milestones) ? project.milestones.length : 0;
  const skills = Array.isArray(project.skills) ? project.skills : [];
  const projectSlug = project.slug || project.id;
  return (
    <article className="project-card panel project-card-course" key={project.id || projectSlug}>
      <div className="project-course-card-head">
        <span className="project-course-symbol"><FolderKanban size={20} /></span>
        <span className="collection-course-category">{String(project.tier || project.difficulty || "CORE").replaceAll("_", " ")}</span>
      </div>
      <div className="project-card-body">
        <h3>{project.title}</h3>
        <p>{project.objective || project.description || "A practical project that applies the concepts from this course."}</p>
        {!!skills.length && <div className="project-tags">{skills.slice(0, 5).map((skill) => <span key={skill}>{skill}</span>)}</div>}
        <div className="project-card-footer">
          <span><ListChecks size={14} /> {milestoneCount} milestones</span>
          <Link className="button button-secondary button-small" to={`/projects/${encodeURIComponent(courseSlug)}/${encodeURIComponent(projectSlug)}`}>
            Open guide <ArrowRight size={13} />
          </Link>
        </div>
      </div>
    </article>
  );
}

export default function ProjectsPage() {
  const { courseSlug } = useParams();
  const courses = useCourseCatalog();
  const course = courses.find((item) => item.slug === courseSlug);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [tier, setTier] = useState("All levels");

  useEffect(() => {
    const controller = new AbortController();
    setProjects([]);
    setLoading(true);
    setError("");
    apiFetch(`${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/projects`, { credentials: "include", signal: controller.signal })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "Projects could not be loaded.");
        return payload;
      })
      .then((payload) => setProjects(Array.isArray(payload.items) ? payload.items : []))
      .catch((err) => { if (err.name !== "AbortError") setError(err.message || "Projects could not be loaded."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [courseSlug]);

  const tiers = useMemo(() => ["All levels", ...new Set(projects.map((project) => String(project.tier || project.difficulty || "Core").replaceAll("_", " ")).filter(Boolean))], [projects]);
  const filtered = useMemo(() => projects.filter((project) => {
    const level = String(project.tier || project.difficulty || "Core").replaceAll("_", " ");
    const text = `${project.title || ""} ${project.objective || ""} ${(project.skills || []).join(" ")}`.toLowerCase();
    return (tier === "All levels" || level.toLowerCase() === tier.toLowerCase()) && text.includes(query.trim().toLowerCase());
  }), [projects, tier, query]);

  if (!course) return <PageShell><EmptyState title="Course not found" detail="Choose a course from the Projects catalog." action={<Link to="/projects" className="button button-primary">Browse projects</Link>} /></PageShell>;

  return (
    <PageShell className="course-collection-detail">
      <CourseOverview course={course} sectionLabel="GUIDED PROJECT WORKSHOP" pageSuffix="Projects" backTo="/projects" backLabel="All project courses" actionTo={`/learn/${course.slug}`} actionLabel="Open tutorial" />
      <div className="collection-detail-toolbar">
        <div><h2>{course.title.replace(/\s+[—–-]\s+From Beginner to Professional.*$/i, "")} projects</h2><p>Open any guide for a separate build page with milestones, folder structure, file-by-file starter code, setup commands, and verification checks.</p></div>
        <label className="catalog-search panel collection-detail-search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search projects..." aria-label="Search projects" /><span>{filtered.length}</span></label>
      </div>
      <div className="collection-action-row"><span><FolderKanban size={15} /> {projects.length} published project guides</span><Link className="button button-secondary button-small" to="/playground"><Terminal size={14} /> Open playground</Link></div>
      {!!projects.length && <div className="category-tabs collection-category-tabs">{tiers.map((value) => <button key={value} type="button" onClick={() => setTier(value)} className={tier === value ? "active" : ""}>{value}</button>)}</div>}
      {loading ? <div className="panel collection-state">Loading {course.title} projects…</div> : error ? <EmptyState title="Projects are not available yet" detail={`${error} The course and its project files must be imported and published before they appear here.`} action={<Link to="/projects" className="button button-secondary">Browse other courses</Link>} /> : filtered.length ? <div className="project-grid course-project-grid">{filtered.map((project) => <ProjectCard project={project} courseSlug={course.slug} key={project.id || project.slug} />)}</div> : <EmptyState icon={FolderKanban} title={query ? "No matching projects" : "No published projects yet"} detail={query ? "Try another search or level." : `The ${course.title} project guides will appear here when their project files are published.`} action={query ? <button className="button button-secondary" onClick={() => { setQuery(""); setTier("All levels"); }}>Clear filters</button> : <Link to={`/learn/${course.slug}`} className="button button-primary">Open tutorial <ArrowRight size={14} /></Link>} />}
    </PageShell>
  );
}
