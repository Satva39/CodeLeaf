const AVAILABILITY_RANK = {
  Published: 0,
  "Local preview": 1,
  Roadmap: 2,
};

function normalText(value) {
  return String(value ?? "").trim().toLocaleLowerCase();
}

/** Pure catalog filtering keeps the Tutorials and collection directories consistent. */
export function filterCourseCatalog(courses, filters = {}) {
  const query = normalText(filters.query);
  const category = filters.category || "All";
  const level = filters.level || "All levels";
  const status = filters.status || "All availability";
  const sort = filters.sort || "name-asc";

  const filtered = (Array.isArray(courses) ? courses : []).filter((course) => {
    const searchable = [
      course?.title,
      course?.desc,
      course?.category,
      course?.level,
      course?.slug,
      course?.status,
      ...(Array.isArray(course?.audience) ? course.audience : []),
      ...(Array.isArray(course?.learningOutcomes) ? course.learningOutcomes : []),
    ].map(normalText).join(" ");

    return (
      (!query || searchable.includes(query)) &&
      (category === "All" || course?.category === category) &&
      (level === "All levels" || course?.level === level) &&
      (status === "All availability" || course?.status === status)
    );
  });

  return filtered.sort((a, b) => {
    if (sort === "lessons-desc") {
      return (Number(b.lessons) || 0) - (Number(a.lessons) || 0) ||
        String(a.title || "").localeCompare(String(b.title || ""));
    }
    if (sort === "availability") {
      return (AVAILABILITY_RANK[a.status] ?? 3) - (AVAILABILITY_RANK[b.status] ?? 3) ||
        (Number(b.lessons) || 0) - (Number(a.lessons) || 0) ||
        String(a.title || "").localeCompare(String(b.title || ""));
    }
    if (sort === "name-desc") {
      return String(b.title || "").localeCompare(String(a.title || ""));
    }
    return String(a.title || "").localeCompare(String(b.title || ""));
  });
}


/** Map catalog metadata from the backend only; local records are presentation fallbacks. */
export function mapAuthoritativeCourseCatalog(remoteItems, fallbackCourses = []) {
  if (!Array.isArray(remoteItems)) throw new Error("Course catalog response is invalid.");
  const fallbackBySlug = new Map((Array.isArray(fallbackCourses) ? fallbackCourses : []).map((course) => [course.slug, course]));
  const list = (value) => Array.isArray(value) ? value.filter((item) => typeof item === "string") : [];
  return remoteItems
    .filter((remote) => remote && typeof remote.slug === "string" && remote.slug.trim())
    .map((remote) => {
      const fallback = fallbackBySlug.get(remote.slug) || {};
      const lessonCount = Math.max(0, Number(remote.lesson_count) || 0);
      const rawStatus = String(remote.status || "roadmap").toLowerCase();
      const available = lessonCount > 0 && ["published", "preview"].includes(rawStatus);
      return {
        ...fallback,
        slug: remote.slug,
        title: remote.title || fallback.title || remote.slug || "Course",
        desc: remote.description || fallback.desc || "Course details are not available yet.",
        icon: fallback.icon || remote.slug.slice(0, 4).toUpperCase(),
        color: fallback.color || "#64748b",
        category: remote.category || fallback.category || "Programming",
        level: remote.level || fallback.level || "Beginner",
        lessons: available ? lessonCount : 0,
        modules: available ? Math.max(0, Number(remote.module_count) || 0) : 0,
        references: Math.max(0, Number(remote.reference_count) || 0),
        projects: Math.max(0, Number(remote.project_count) || 0),
        practice: Math.max(0, Number(remote.practice_count) || 0),
        estimatedMinutes: available ? Math.max(0, Number(remote.estimated_minutes) || 0) : 0,
        audience: list(remote.audience),
        prerequisites: list(remote.prerequisites),
        learningOutcomes: list(remote.learning_outcomes),
        rawStatus,
        status: rawStatus === "preview" && available
          ? "Local preview"
          : rawStatus === "published" && available
            ? "Published"
            : "Roadmap",
      };
    });
}

export const COURSE_LEVEL_FILTERS = ["All levels", "Beginner", "Intermediate", "Advanced", "Beginner to Advanced"];
export const COURSE_AVAILABILITY_FILTERS = ["All availability", "Published", "Local preview", "Roadmap"];
export const COURSE_SORT_OPTIONS = [
  { value: "name-asc", label: "Name (A–Z)" },
  { value: "name-desc", label: "Name (Z–A)" },
  { value: "lessons-desc", label: "Most lessons" },
  { value: "availability", label: "Availability first" },
];
