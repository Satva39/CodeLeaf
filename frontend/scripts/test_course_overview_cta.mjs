import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(process.cwd());
const overview = readFileSync(resolve(root, "src/components/course/CourseOverview.jsx"), "utf8");
const landing = readFileSync(resolve(root, "src/pages/CourseLandingPage.jsx"), "utf8");
const lessonPage = readFileSync(resolve(root, "src/pages/LessonPage.jsx"), "utf8");

function check(condition, message) {
  if (!condition) throw new Error(`FAIL ${message}`);
  console.log(`PASS ${message}`);
}

check(/allowUnavailableAction\s*=\s*false/.test(overview), "course overview supports an explicit CTA override for roadmap courses");
check(/showLearningSections\s*=\s*false/.test(overview), "learning details and course outline are opt-in by default");
check(/showLearningSections\s*&&\s*\(audience\.length/.test(overview), "audience, prerequisites, and outcomes render only when learning sections are enabled");
check(/showLearningSections\s*&&\s*available\s*&&/.test(overview), "course outline renders only when learning sections are enabled");
check(/showLearningSections/.test(landing), "tutorial course landing enables learning details and course outline");
check(/const actionCanOpenCourse\s*=\s*available\s*\|\|\s*allowUnavailableAction/.test(overview), "CTA route resolution preserves normal availability rules by default");
check(/actionTo=\{`\/learn\/\$\{encodeURIComponent\(course\.slug\)\}`\}/.test(landing), "course landing Start Learning links to the selected course");
check(/actionLabel="Start Learning"/.test(landing) && /allowUnavailableAction/.test(landing), "course landing always renders the requested Start Learning action");
check(/learning is coming soon/.test(lessonPage) && /lessons have not been published yet/.test(lessonPage), "unpublished roadmap courses explain why lessons are not available");
console.log("All course overview CTA tests passed.");
