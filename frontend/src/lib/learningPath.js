const AVAILABLE_STATUSES = new Set(["Published", "Local preview"]);

function normalizedTimestamp(value) {
  const parsed = value ? Date.parse(value) : 0;
  return Number.isFinite(parsed) ? parsed : 0;
}

function courseIsAvailable(course) {
  return Boolean(
    course &&
      typeof course.slug === "string" &&
      course.slug.trim() &&
      AVAILABLE_STATUSES.has(course.status) &&
      Number(course.lessons) > 0,
  );
}

function courseHref(slug) {
  return `/learn/${encodeURIComponent(slug)}`;
}

function lessonHref(courseSlug, lessonSlug) {
  return `${courseHref(courseSlug)}/${encodeURIComponent(lessonSlug)}`;
}

/**
 * Pick a truthful home-page learning action from authoritative course status and
 * recorded progress. Never claims to resume a lesson if no recent lesson exists.
 */
export function selectLearningTarget({ courses = [], recentItems = [], lastCourseSlug = "" } = {}) {
  const safeCourses = Array.isArray(courses) ? courses : [];
  const availableCourses = safeCourses.filter(courseIsAvailable);
  const coursesBySlug = new Map(availableCourses.map((course) => [course.slug, course]));

  const recent = (Array.isArray(recentItems) ? recentItems : [])
    .filter((item) =>
      item &&
      typeof item.course_slug === "string" &&
      typeof item.lesson_slug === "string" &&
      item.lesson_slug.trim() &&
      coursesBySlug.has(item.course_slug),
    )
    .slice()
    .sort((a, b) => normalizedTimestamp(b.last_opened_at) - normalizedTimestamp(a.last_opened_at))[0];

  if (recent) {
    const course = coursesBySlug.get(recent.course_slug);
    return {
      kind: "lesson",
      course,
      lessonSlug: recent.lesson_slug,
      lessonTitle: String(recent.title || recent.lesson_slug.replaceAll("-", " ")),
      completed: recent.completed === true,
      href: lessonHref(recent.course_slug, recent.lesson_slug),
      ctaLabel: recent.completed ? "Review last lesson" : "Resume last lesson",
      eyebrow: recent.completed ? "YOUR LAST COMPLETED LESSON" : "PICK UP WHERE YOU LEFT OFF",
    };
  }

  const selectedCourse = coursesBySlug.get(lastCourseSlug);
  if (selectedCourse) {
    return {
      kind: "course",
      course: selectedCourse,
      lessonSlug: "",
      lessonTitle: "",
      completed: false,
      href: courseHref(selectedCourse.slug),
      ctaLabel: "Continue course",
      eyebrow: "YOUR LAST COURSE",
    };
  }

  // HTML remains the suggested first path when published, but is not represented
  // as prior progress. Otherwise use the first available API course.
  const firstCourse = coursesBySlug.get("html") || availableCourses[0] || null;
  if (firstCourse) {
    return {
      kind: "start",
      course: firstCourse,
      lessonSlug: "",
      lessonTitle: "",
      completed: false,
      href: courseHref(firstCourse.slug),
      ctaLabel: "Start learning",
      eyebrow: "A GOOD PLACE TO START",
    };
  }

  return {
    kind: "catalog",
    course: null,
    lessonSlug: "",
    lessonTitle: "",
    completed: false,
    href: "/tutorials",
    ctaLabel: "Explore courses",
    eyebrow: "EXPLORE LEARNING PATHS",
  };
}

export function formatLearningStat(value, mode) {
  if (mode === "loading") return "Loading…";
  if (mode === "unavailable") return "Unavailable";
  const number = Number(value);
  return Number.isFinite(number) ? number.toLocaleString() : "0";
}
