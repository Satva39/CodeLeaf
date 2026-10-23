import { defaultSourceForLanguage, resolveLanguage } from "../lib/languageWorkspace.js";
import { COURSE_CATALOG } from "../data.js";

export function defaultCode(slug) {
  if (slug === "html")
    return "<main>\n  <h1>Hello, world!</h1>\n  <p>Ideas become things.</p>\n</main>";
  if (slug === "css")
    return "main {\n  max-width: 70rem;\n  margin: 0 auto;\n  padding: 2rem;\n}";
  if (slug === "python") return 'name = "CodeLeaf"\nprint(f"Hello, {name}!")';
  if (slug === "php")
    return '<?php\n$name = "CodeLeaf";\necho "Learning " . $name . PHP_EOL;';
  if (slug === "r") return "scores <- c(72, 85, 91)\nmean(scores)";
  if (slug === "sql" || slug === "postgresql")
    return "SELECT title, level\nFROM courses\nWHERE level = 'Beginner'\nORDER BY title;";
  return defaultSourceForLanguage(resolveLanguage(slug).key);
}

export function getLessonContent(courseSlug, lessonSlug, title) {
  const course =
    COURSE_CATALOG.find((c) => c.slug === courseSlug) || COURSE_CATALOG[0];
  const generic = {
    intro: `${title} introduces one building block of ${course.title}. Learn the idea, test it with a small example, and use it in a practical task.`,
    outcomes: [
      `Explain the purpose of ${title.toLowerCase()}.`,
      "Recognize where this idea fits in a real project.",
      "Modify a small example and check the result.",
    ],
    visualTitle: "From idea to working result",
    visualDescription:
      "A simple learning loop helps connect the concept to something you can see and test.",
    visualSteps: [
      "Understand",
      "Inspect example",
      "Try a change",
      "Check result",
    ],
    paragraphs: [
      `${title} is easier to understand when you connect it to a concrete problem. Start with the smallest version that demonstrates the concept, then change one part at a time.`,
      `In a real project, the same idea usually appears alongside other features. Keep each piece focused and verify the behavior instead of relying on assumptions.`,
      `Use the official reference when you need exact syntax or edge-case behavior. This lesson is a starting point, not a replacement for version-specific documentation.`,
    ],
    tip: "Make one change at a time. The difference between the original and updated output is a clue to how the feature works.",
    task: `Create a small ${course.title} example that demonstrates ${title.toLowerCase()}, then compare your output with the expected behavior.`,
    checks: [
      "Use the correct syntax or structure.",
      "Run or inspect the example.",
      "Explain what changed and why.",
    ],
    solution:
      "Begin with the provided example. Change one variable, tag, query or rule; run it again; then explain the observed difference in one sentence.",
    output:
      "Example result\nConcept rendered successfully\nNext: modify one thing and compare.",
    mistakes: [
      [
        "Changing too many things at once",
        "It becomes difficult to identify the cause of a result.",
        "Change one part, rerun, and compare.",
      ],
      [
        "Ignoring the tool/runtime version",
        "Features can behave differently across versions or environments.",
        "Check the official versioned reference.",
      ],
      [
        "Skipping the output check",
        "A successful-looking example can still behave incorrectly.",
        "Verify expected output and test an edge case.",
      ],
    ],
    recap: [
      "Start from a minimal valid example.",
      "Use the correct tool/runtime for the technology.",
      "Test the change and explain the result.",
    ],
  };
  if (courseSlug === "r")
    return {
      ...generic,
      intro:
        "Use your own local R interpreter for execution. Code shown here is a reference example; CodeLeaf does not execute R in the browser.",
      visualTitle: "From data to verified result",
      visualDescription:
        "Define the question, inspect the input, compute a result, then verify assumptions and edge cases.",
      visualAlt:
        "A learning loop from a question through R code and output checks to a documented conclusion.",
      visualSteps: [
        "Define question",
        "Inspect data",
        "Compute",
        "Verify",
        "Document",
      ],
      paragraphs: [
        "R is a language for statistical computing, data analysis and graphics. Use short base-R examples first, then inspect data structures and outputs.",
        "This browser preview does not execute R. Use a local R console or a reviewed R-aware environment to run code; compare actual output with the reference and test edge cases.",
        "For analytical work, preserve data provenance and document missing-value rules, assumptions, uncertainty and limitations.",
      ],
      tip: "Do not treat the displayed reference output as proof that your own runtime executed the code.",
      task: "Run the example in a local R session, verify its output and test one change or edge case.",
      checks: [
        "Use valid R syntax.",
        "Compare actual output with the expected result.",
        "Document an edge case and one limitation.",
      ],
      codeSample: "scores <- c(72, 85, 91)\\nmean(scores)",
      output: "[1] 82.66667",
      runMode: "static-validation",
      sources: [
        "https://www.r-project.org/",
        "https://cran.r-project.org/doc/manuals/r-release/R-intro.html",
      ],
    };
  if (courseSlug === "html") {
    if (lessonSlug === "introduction-to-html")
      return {
        ...generic,
        intro:
          "Discover what HTML is, where it fits on the web, and how a browser turns markup into a page.",
        visualTitle: "From source file to visible page",
        visualDescription:
          "A browser receives a document and interprets its markup to create the structure you see.",
        visualSteps: [
          "HTML file",
          "Browser parser",
          "Document tree",
          "Rendered page",
        ],
        paragraphs: [
          "HTML stands for HyperText Markup Language. It describes the structure and meaning of web content using elements and attributes.",
          "HTML is a markup language rather than a general-purpose programming language. It is commonly paired with CSS for presentation and JavaScript for behavior.",
          "This path starts with the document structure, then moves through text, links, media, tables, forms, semantics, accessibility and professional practices.",
        ],
        outcomes: [
          "Define HTML in your own words.",
          "Distinguish markup from styling and programming behavior.",
          "Trace the basic path from an HTML file to a browser page.",
        ],
        task: "Create a page with a descriptive title, one main heading and one paragraph.",
        checks: [
          "Include the document declaration.",
          "Add head and body sections.",
          "Use a meaningful page title.",
        ],
        solution:
          "Start with the HTML document skeleton and place visible text in the body. The title belongs in the head.",
        output: "A browser page with a title, one heading and a paragraph.",
        recap: [
          "HTML is used to describe page structure.",
          "Elements and attributes communicate meaning and configuration.",
          "The browser interprets the document and renders a page.",
        ],
      };
  }
  if (courseSlug === "python" && lessonSlug === "python-variables")
    return {
      ...generic,
      visualTitle: "A name points to a value",
      visualSteps: ["Name", "Assignment", "Value", "Use value"],
    };
  if (courseSlug === "sql" && lessonSlug === "sql-select")
    return {
      ...generic,
      visualTitle: "Request → filter → result",
      visualSteps: [
        "SELECT columns",
        "FROM table",
        "WHERE filter",
        "Result rows",
      ],
    };
  return generic;
}
