import assert from "node:assert/strict";
import {
  buildReferenceDetails,
  flattenCourseOutline,
  splitReferenceTopics,
} from "../src/lib/referenceDetails.js";

const outline = flattenCourseOutline([
  {
    title: "Templates and control flow",
    lessons: [
      { slug: "introduction-to-templates", title: "Introduction to Templates", sequence: 1, keywords: ["template basics"] },
      { slug: "template-control-flow", title: "Template Control Flow", sequence: 2, keywords: ["conditionals", "loops"] },
      { slug: "forms-and-validation", title: "Forms and Validation", sequence: 3, keywords: ["forms", "validation"] },
      { slug: "secure-templates", title: "Template Security", sequence: 4, keywords: ["security", "sanitization"] },
    ],
  },
]);

assert.deepEqual(splitReferenceTopics(["components", "templates; control flow", "templates"]), ["components", "templates", "control flow"]);
assert.equal(outline.length, 4);

const sparseReference = {
  slug: "control-flow",
  title: "Template control flow",
  url: "https://angular.dev/guide/templates/control-flow",
  publisher: "Angular documentation",
  source_type: "official_documentation",
  supports: "control flow",
  explanation: "control flow",
  example: "",
  related_lesson_slugs: [],
};
const generated = buildReferenceDetails(sparseReference, { title: "Angular — From Beginner to Professional" }, outline);
assert.match(generated.explanation, /resource “Template control flow” is listed as official documentation/i);
assert.match(generated.explanation, /control flow/);
assert.match(generated.example, /While implementing|When working on/);
assert.ok(generated.relatedLessons.some((lesson) => lesson.slug === "template-control-flow"));
assert.equal(generated.hasAuthoredExplanation, false);
assert.equal(generated.hasAuthoredExample, false);

const authoredReference = {
  slug: "custom-reference",
  title: "Custom reference",
  url: "https://example.com/reference",
  publisher: "Example publisher",
  source_type: "official_reference",
  supports: "custom behavior",
  explanation: "This carefully authored explanation should remain exactly as supplied for the learner.",
  example: "Use the documented option in a small test project.",
  related_lesson_slugs: ["forms-and-validation"],
};
const authored = buildReferenceDetails(authoredReference, { title: "Example Course" }, outline);
assert.equal(authored.explanation, authoredReference.explanation);
assert.equal(authored.example, authoredReference.example);
assert.equal(authored.relatedLessons[0].slug, "forms-and-validation");
assert.equal(authored.relatedLessons[0].title, "Forms and Validation");
assert.equal(authored.hasAuthoredExplanation, true);
assert.equal(authored.hasAuthoredExample, true);

const noMatch = buildReferenceDetails({
  title: "Unmatched resource", url: "https://example.com/zzz", source_type: "reference", supports: "unmatched concepts",
}, { title: "Example Course" }, outline);
assert.equal(noMatch.usedFallbackLessons, true);
assert.equal(noMatch.relatedLessons.length, 3);

console.log("Reference detail enrichment tests passed.");
