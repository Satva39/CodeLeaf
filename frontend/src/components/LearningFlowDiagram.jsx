import {
  ArrowRight,
  BookMarked,
  CheckCircle2,
  FileCode2,
  Zap,
} from "lucide-react";

const DEFAULT_STEPS = [
  { title: "Understand", Icon: FileCode2 },
  { title: "Inspect example", Icon: BookMarked },
  { title: "Try a change", Icon: Zap },
  { title: "Check result", Icon: CheckCircle2 },
];

function plainText(value) {
  if (typeof value !== "string") return "";
  return value.replace(/\s+/g, " ").trim();
}

function shorten(value, max = 104) {
  const text = plainText(value);
  if (!text) return "";
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1).trimEnd()}…`;
}

function getStepDetail(
  index,
  { lessonTitle, topicHints, task, expectedOutput },
) {
  const hints = (Array.isArray(topicHints) ? topicHints : [])
    .map((item) => (typeof item === "string" ? item : item?.title))
    .map(plainText)
    .filter(Boolean);

  if (index === 0) {
    return lessonTitle
      ? `Start with the central idea behind ${lessonTitle}.`
      : "Get clear on the central idea before moving on.";
  }
  if (index === 1) {
    return hints[0]
      ? `Notice how ${hints[0]} fits into the example.`
      : "Read the example and notice its important parts.";
  }
  if (index === 2) {
    return (
      shorten(task) ||
      (hints[1]
        ? `Apply the idea to ${hints[1]}.`
        : "Change one small part and predict the effect.")
    );
  }
  const output = shorten(expectedOutput, 90);
  return output
    ? `Compare with: ${output}`
    : "Compare your result with the expected behavior.";
}

function normalizeSteps(steps, context) {
  const hasFourSteps = Array.isArray(steps) && steps.length === 4;
  return DEFAULT_STEPS.map((phase, index) => {
    const candidate = hasFourSteps ? steps[index] : null;
    const candidateTitle =
      typeof candidate === "string" ? candidate : candidate?.title;
    const candidateDescription =
      typeof candidate === "object" && candidate
        ? candidate.description || candidate.detail
        : "";

    return {
      title: shorten(candidateTitle || phase.title, 44),
      description: shorten(
        candidateDescription || getStepDetail(index, context),
        112,
      ),
      Icon: phase.Icon,
    };
  });
}

/**
 * A responsive, accessible, CSS-rendered learning diagram.
 * Older `asset_path` diagrams and new `steps` diagrams share this presentation.
 */
export default function LearningFlowDiagram({
  steps,
  lessonTitle,
  topicHints = [],
  task,
  expectedOutput,
  caption,
  altText,
}) {
  const context = { lessonTitle, topicHints, task, expectedOutput };
  const visualSteps = normalizeSteps(steps, context);
  const accessibleLabel =
    plainText(altText) ||
    `Four connected learning steps for ${plainText(lessonTitle) || "this lesson"}: ${visualSteps.map((step) => step.title).join(", ")}.`;

  return (
    <div className="learning-flow-visual">
      <div
        className="concept-flow learning-flow"
        role="list"
        aria-label={accessibleLabel}
      >
        {visualSteps.map((step, index) => {
          const StepIcon = step.Icon;
          return (
            <div
              className="concept-node-wrap"
              key={`${index}-${step.title}`}
              role="listitem"
            >
              <article className={`concept-node node-${index}`}>
                <div className="concept-node-topline">
                  <span className="concept-node-number">
                    STEP {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="concept-node-icon" aria-hidden="true">
                    <StepIcon size={19} strokeWidth={2.1} />
                  </span>
                </div>
                <div className="concept-node-copy">
                  <strong>{step.title}</strong>
                  <p className="concept-node-detail">{step.description}</p>
                </div>
              </article>
              {index !== visualSteps.length - 1 && (
                <div className="concept-arrow" aria-hidden="true">
                  <ArrowRight size={17} strokeWidth={2.2} />
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div className="diagram-caption">
        <span className="diagram-caption-dot" aria-hidden="true" />
        {plainText(caption) ||
          "Move through each step, then check what changed."}
      </div>
    </div>
  );
}
