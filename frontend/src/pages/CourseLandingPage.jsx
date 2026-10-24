import { Link, useParams } from "react-router-dom";
import { ArrowRight, BookMarked, Code2, FolderKanban, Search } from "lucide-react";
import { PageShell, EmptyState } from "../components/common.jsx";
import CourseOverview from "../components/course/CourseOverview.jsx";
import { useCourseCatalogState } from "../lib/useCourseCatalog.js";

export default function CourseLandingPage() {
  const { courseSlug } = useParams();
  const { courses, loading, error } = useCourseCatalogState();
  const course = courses.find((item) => item.slug === courseSlug);

  if (!course && (loading || error)) {
    return <PageShell><div className="panel collection-state" role="status">{loading ? "Loading course details…" : "Course details could not be loaded. Try the course directory."}</div></PageShell>;
  }
  if (!course) {
    return <PageShell><EmptyState icon={Search} title="Course not found" detail="This course is not in the current catalog. Browse the available learning paths to find another track." action={<Link to="/tutorials" className="button button-primary">Browse courses <ArrowRight size={15} /></Link>} /></PageShell>;
  }

  const tracks = [
    { label: "References", to: `/reference/${encodeURIComponent(course.slug)}`, count: Number(course.references) || 0, noun: "published entries", icon: BookMarked, detail: "Definitions, APIs, syntax and official documentation." },
    { label: "Projects", to: `/projects/${encodeURIComponent(course.slug)}`, count: Number(course.projects) || 0, noun: "published guides", icon: FolderKanban, detail: "Guided build pages with milestones and review criteria." },
    { label: "Practice", to: `/practice/${encodeURIComponent(course.slug)}`, count: Number(course.practice) || 0, noun: "published tasks", icon: Code2, detail: "Exercises linked to lessons in this course." },
  ];
  return (
    <PageShell className="course-landing-page">
      <CourseOverview
        course={course}
        sectionLabel="CODELEAF LEARNING PATH"
        pageSuffix="Course overview"
        backTo="/tutorials"
        backLabel="All courses"
        actionTo={`/learn/${encodeURIComponent(course.slug)}`}
        actionLabel="Start Learning"
        allowUnavailableAction
        showLearningSections
      />
      <section className="course-track-section">
        <div className="section-heading">
          <div><div className="eyebrow">LEARN, BUILD, REFERENCE</div><h2>Explore this course</h2><p>Each area stays scoped to {course.title}; item counts reflect records exposed by the course API.</p></div>
        </div>
        <div className="course-track-grid">
          {tracks.map(({ label, to, count, noun, icon: Icon, detail }) => (
            <Link key={label} to={to} className="course-track-card panel">
              <span className="course-track-icon"><Icon size={22} /></span>
              <h3>{label}</h3>
              <p>{detail}</p>
              <div><strong>{count}</strong><span>{noun}</span><ArrowRight size={16} /></div>
            </Link>
          ))}
        </div>
      </section>
    </PageShell>
  );
}
