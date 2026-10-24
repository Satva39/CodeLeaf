const STOP_WORDS = new Set([
  "a", "about", "an", "and", "api", "are", "as", "at", "be", "best", "by",
  "chapter", "check", "documentation", "docs", "for", "from", "guide", "how",
  "in", "index", "into", "is", "it", "its", "learn", "learning", "of", "on",
  "or", "official", "overview", "page", "reference", "resource", "the", "this",
  "to", "tutorial", "use", "using", "with", "www",
]);

function asText(value) {
  if (Array.isArray(value)) return value.filter(Boolean).map(String).join(", ");
  return value == null ? "" : String(value).trim();
}

/** Allow only ordinary web links from reference metadata; never render executable schemes. */
export function safeExternalHref(value) {
  const candidate = asText(value);
  if (!candidate) return "";
  try {
    const parsed = new URL(candidate);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : "";
  } catch {
    return "";
  }
}

function words(value) {
  return asText(value)
    .normalize("NFKD")
    .toLowerCase()
    .match(/[a-z0-9]+/g)?.filter((word) => word.length > 1 && !STOP_WORDS.has(word)) || [];
}

function keyForSlug(value) {
  return asText(value)
    .toLowerCase()
    .replace(/^\d{1,4}-/, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function humanize(value) {
  return asText(value)
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim() || "reference";
}

export function splitReferenceTopics(value) {
  const raw = Array.isArray(value)
    ? value.flatMap((entry) => String(entry).split(/[;|,\n]+/))
    : asText(value).split(/[;|,\n]+/);
  const seen = new Set();
  return raw.map((topic) => topic.trim().replace(/^[-•\s]+|[-•\s]+$/g, ""))
    .filter((topic) => {
      const key = topic.toLowerCase();
      if (!topic || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 12);
}

export function flattenCourseOutline(modules) {
  if (!Array.isArray(modules)) return [];
  return modules.flatMap((module) => {
    if (!module || !Array.isArray(module.lessons)) return [];
    return module.lessons.filter((lesson) => lesson && lesson.slug).map((lesson) => ({
      slug: String(lesson.slug),
      title: String(lesson.title || humanize(lesson.slug)),
      sequence: Number(lesson.sequence) || 0,
      moduleTitle: String(module.title || ""),
      keywords: Array.isArray(lesson.keywords) ? lesson.keywords : [],
    }));
  });
}

function sourceDescription(item, courseTitle, topics) {
  const title = asText(item.title) || "This resource";
  const publisher = asText(item.publisher);
  const sourceType = humanize(item.source_type);
  const context = topics.length ? topics.join(", ") : title;
  const publisherPhrase = publisher && !publisher.toLowerCase().includes(courseTitle.toLowerCase())
    ? ` published by ${publisher}`
    : "";
  const coursePhrase = courseTitle ? ` In the ${courseTitle} course` : " In this course";
  return `The resource “${title}” is listed as ${sourceType}${publisherPhrase}.${coursePhrase}, use it to verify ${context}. Compare the relevant guidance with the version, constraints, and requirements of your own project before adopting an API, command, or configuration.`;
}

function practicalExample(item, courseTitle, topics) {
  const title = asText(item.title) || "this resource";
  const context = topics.length ? topics.slice(0, 3).join(", ") : title;
  const combined = `${title} ${context} ${asText(item.source_type)}`.toLowerCase();
  if (/version|release|compatib|migration|upgrade|deprecat/.test(combined)) {
    return `Before choosing or upgrading a ${courseTitle || "project"} dependency, compare the supported versions and any runtime or toolchain constraints documented here with your current setup. Make the change in a branch, then run the relevant checks before merging it.`;
  }
  if (/security|privacy|auth|permission|vulnerab|cryptograph|threat/.test(combined)) {
    return `During a security review, identify the part of your ${courseTitle || "application"} that relates to ${context}. Compare its trust boundary and configuration with this guidance, then test both an allowed case and a rejected case without exposing credentials or private data.`;
  }
  if (/test|validat|checker|diagnostic|lint|debug|inspect|audit/.test(combined)) {
    return `Run the relevant checker, test, or diagnostic from this resource against a small representative ${courseTitle || "project"} example. Review its findings, correct the highest-priority issue, and run the check again so the result is repeatable.`;
  }
  if (/api|syntax|property|method|function|endpoint|command|cli|expression|reference/.test(combined)) {
    return `While implementing ${context} in ${courseTitle || "your project"}, locate the exact API, option, or rule in this resource. Verify its inputs, constraints, and expected behavior, then adapt the smallest suitable example and test it with the version your project uses.`;
  }
  return `When working on ${context} in ${courseTitle || "your project"}, open the relevant section of this resource, verify the documented rules and limitations, then apply one small change and test the result. Keep the resource handy when reviewing or maintaining that implementation.`;
}

function scoreRelatedLessons(item, outlineLessons, courseTitle) {
  const urlPath = (() => {
    try { return new URL(item.url).pathname.replaceAll("/", " "); }
    catch { return ""; }
  })();
  const courseWords = new Set(words(courseTitle));
  const titleWords = new Set(words(item.title).filter((word) => !courseWords.has(word)));
  const topicWords = new Set(words(item.supports).filter((word) => !courseWords.has(word)));
  const urlWords = new Set(words(urlPath).filter((word) => !courseWords.has(word)));
  const normalizedTitle = keyForSlug(item.title);

  return outlineLessons.map((lesson) => {
    const lessonWords = new Set(words(`${lesson.title} ${lesson.slug} ${lesson.moduleTitle} ${lesson.keywords.join(" ")}`));
    let score = 0;
    for (const word of titleWords) if (lessonWords.has(word)) score += 5;
    for (const word of topicWords) if (lessonWords.has(word)) score += 3;
    for (const word of urlWords) if (lessonWords.has(word)) score += 1.5;
    if (titleWords.size >= 2 && [...titleWords].every((word) => lessonWords.has(word))) score += 8;
    if (keyForSlug(lesson.title) === normalizedTitle || keyForSlug(lesson.slug) === normalizedTitle) score += 20;
    return { ...lesson, score };
  }).filter((lesson) => lesson.score > 0)
    .sort((a, b) => b.score - a.score || a.sequence - b.sequence);
}

export function buildReferenceDetails(item, course, outlineLessons = []) {
  const reference = item || {};
  const fullCourseTitle = asText(course?.title);
  const courseTitle = fullCourseTitle.replace(/\s+[—–-]\s+From Beginner to Professional.*$/i, "")
    || fullCourseTitle || "this course";
  const topics = splitReferenceTopics(reference.supports);
  if (!topics.length) topics.push(asText(reference.title) || "resource guidance");

  const providedExplanation = asText(reference.explanation);
  const providedSupports = asText(reference.supports);
  const explanationLooksAuthored = Boolean(providedExplanation)
    && (providedExplanation !== providedSupports || (providedExplanation.length > 120 && /[.!?]\s+[A-Z]/.test(providedExplanation)));
  const explanation = explanationLooksAuthored
    ? providedExplanation
    : sourceDescription(reference, courseTitle, topics);

  const providedExample = asText(reference.example);
  const example = providedExample || practicalExample(reference, courseTitle, topics);

  const lessonsBySlug = new Map(outlineLessons.map((lesson) => [keyForSlug(lesson.slug), lesson]));
  const explicitSlugs = Array.isArray(reference.related_lesson_slugs)
    ? reference.related_lesson_slugs
    : Array.isArray(reference.related_lessons)
      ? reference.related_lessons
      : [];
  const relatedLessons = [];
  const used = new Set();
  for (const slugValue of explicitSlugs) {
    const slug = asText(slugValue);
    const match = lessonsBySlug.get(keyForSlug(slug));
    const normalized = keyForSlug(match?.slug || slug);
    if (!normalized || used.has(normalized)) continue;
    used.add(normalized);
    relatedLessons.push({ slug: match?.slug || slug, title: match?.title || humanize(slug), explicit: true });
  }

  const scoredLessons = scoreRelatedLessons(reference, outlineLessons, courseTitle);
  for (const lesson of scoredLessons) {
    if (relatedLessons.length >= 4) break;
    const normalized = keyForSlug(lesson.slug);
    if (used.has(normalized)) continue;
    used.add(normalized);
    relatedLessons.push({ slug: lesson.slug, title: lesson.title, explicit: false });
  }

  let usedFallbackLessons = false;
  if (!relatedLessons.length && outlineLessons.length) {
    usedFallbackLessons = true;
    outlineLessons.slice(0, 3).forEach((lesson) => {
      relatedLessons.push({ slug: lesson.slug, title: lesson.title, explicit: false });
    });
  }

  return {
    explanation,
    topics,
    example,
    relatedLessons,
    usedFallbackLessons,
    hasAuthoredExplanation: explanationLooksAuthored,
    hasAuthoredExample: Boolean(providedExample),
  };
}
