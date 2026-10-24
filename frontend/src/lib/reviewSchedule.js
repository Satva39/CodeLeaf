/** Build a lesson URL that carries the account-scoped review target through to the rating prompt. */
export function buildReviewLessonHref(item) {
  const courseSlug = String(item?.course_slug || "").trim();
  const itemType = item?.item_type === "exercise" ? "exercise" : item?.item_type === "lesson" ? "lesson" : "";
  const itemSlug = String(item?.item_slug || "").trim();
  const lessonSlug = String(item?.lesson_slug || (itemType === "lesson" ? itemSlug : "")).trim();
  if (!courseSlug || !lessonSlug || !itemType || !itemSlug || !item?.id) {
    return courseSlug ? `/practice/${encodeURIComponent(courseSlug)}` : "/review";
  }
  const query = new URLSearchParams({
    reviewId: String(item.id),
    reviewType: itemType,
    reviewItemSlug: itemSlug,
  });
  return `/learn/${encodeURIComponent(courseSlug)}/${encodeURIComponent(lessonSlug)}?${query.toString()}`;
}

export function formatReviewDueDate(value, now = new Date()) {
  const dueDate = new Date(value);
  if (Number.isNaN(dueDate.getTime())) return "Schedule date unavailable";
  const diff = dueDate.getTime() - now.getTime();
  const day = 24 * 60 * 60 * 1000;
  if (diff <= 0) return "Due now";
  if (diff < day) return "Due in less than a day";
  const days = Math.ceil(diff / day);
  if (days === 1) return "Due tomorrow";
  if (days <= 7) return `Due in ${days} days`;
  return `Due ${dueDate.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
}
