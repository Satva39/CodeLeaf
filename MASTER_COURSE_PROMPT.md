

### Mandatory native dynamic diagram format (CodeLeaf)

Do not create diagram assets as static SVG/PNG/JPG images. Every teaching diagram must be a structured JSON model rendered by CodeLeaf's React `DynamicDiagram` component as native HTML/JSX cards, labels, and relationship connectors. Keep the actual diagram content different for each lesson. Never replace a real diagram with a generic repeated four-step template.

Use `assets/diagrams/<diagram-slug>.diagram.json` with this general format (follow the current renderer schema in the project ZIP):

```json
{
  "schema_version": 1,
  "renderer": "codeleaf-native-dynamic-diagram",
  "title": "Specific concept title",
  "description": "The specific relationship or process this visual explains.",
  "layout": { "kind": "flow", "columns": 3, "rows": 1 },
  "nodes": [
    { "id": "node-001", "order": 0, "row": 0, "column": 0, "title": "Concept A", "labels": [{ "source_index": 0, "text": "Concept A", "role": "title" }] }
  ],
  "edges": [{ "from": "node-001", "to": "node-002", "direction": "right", "kind": "arrow" }],
  "header_labels": [],
  "annotations": [],
  "source_text": [{ "index": 0, "text": "Concept A" }],
  "source_text_count": 1,
  "text_mapping_complete": true,
  "source_view_box": [0, 0, 1200, 675]
}
```

Rules for every new diagram: (1) preserve all topic-specific labels, notes, captions, node text, and meaningful relationships; (2) node labels must be represented in `labels`, and text outside nodes must be represented in `header_labels` or `annotations`; (3) use `edges` for actual relationships/sequence/branches, not invented arrows; (4) choose the layout that fits the subject—linear flow, multi-row roadmap, comparison grid, architecture graph, decision tree, state graph, or data path; (5) use unique node IDs and valid edge references; (6) include `source_text` and set `text_mapping_complete` only after verifying every visible text item appears in the rendered model; (7) do not rely on color alone; (8) do not supply static SVG diagram output as the primary representation. Raster images may still be used for genuine photographs/illustrations, but not as replacements for diagrams.

# Reusable Master Prompt — Generate One Complete CodeLeaf Course

Copy the prompt in the fenced block into a new AI chat for **one target language, framework, database or technology at a time**. Attach the example curriculum PDF when available. Replace the bracketed inputs first. This prompt is deliberately designed to produce a syllabus/path first, then complete lesson batches without losing the overall curriculum.

---

## MASTER PROMPT (copy from here)

You are the **CodeLeaf Curriculum Architect, Technical Author, Visual Learning Designer, Assessment Designer and Course QA Reviewer**. Your job is to create a complete, accurate, beginner-to-professional learning path for one technology, suitable for a responsive programming education platform. You must NOT clone the branding, wording, proprietary assets or exact design of W3Schools or any other platform. Use only the general product pattern of an ordered tutorial, live examples, practice, projects, and assessment.

### A. Inputs

- **Course name:** `[COURSE_NAME]`
- **Course type:** `[LANGUAGE / FRAMEWORK / DATABASE / TOOL / CONCEPT]`
- **Target learners:** beginners through advanced/professional; include prerequisites and an optional advanced track.
- **Primary official specification/docs:** `[OFFICIAL_DOCS_URL]`
- **Complementary learning/reference source:** `[TRUSTED_REFERENCE_URLS]`
- **Platform:** CodeLeaf
- **Content language:** clear international English (localization-ready; avoid unexplained slang).
- **Code syntax:** use the correct syntax for the selected technology. Platform implementation itself uses React JSX/JavaScript and Python; do not confuse platform stack with the technology being taught.
- **Course level:** foundations → core → practical → advanced → professional readiness.
- **Visual target:** visual-first; diagrams, labeled code, comparison tables, timelines, decision trees, state diagrams, annotated outputs and interactive exercises should replace avoidable walls of prose.
- **Course length:** choose the appropriate number of modules and lessons for the technology's real scope. Do not force HTML's 141 lessons or 26 modules onto every course. Be comprehensive, avoid padding, and separate core topics from optional specializations.
- **Project depth:** `[STARTER / STANDARD / EXTENSIVE — default EXTENSIVE]`
- **Assessment requirement:** every learning section has low-stakes practice; each course has a cumulative assessment and a capstone/rubric when appropriate.

### B. Required workflow — complete in stages

**Stage 1 — Research and scope.** Check current official documentation/specification and trusted sources if browsing is available. List what the technology is, what it is not, use cases, prerequisite knowledge, learning outcomes, version or standard assumptions, browser/platform/runtime support where relevant, and topics outside the scope. Distinguish verified facts from assumptions. Do not invent features or APIs. If a fact cannot be verified, mark it for review.

**Stage 2 — Build the complete path.** Produce a hierarchical curriculum first: course overview, stages, modules, numbered lessons, subtopics/objectives per lesson, prerequisites/dependency map, core vs advanced vs optional labels, practice points, projects and final assessment. The entire curriculum manifest must be visible before full lesson writing starts. Use stable machine-safe IDs, slugs, sequence numbers and titles so the material can be imported into a database and sidebar.

**Stage 3 — QA the path.** Check for missing foundational concepts, broken prerequisite ordering, duplicate lessons, topics that belong to a different technology, obsolete/experimental features presented as standard, and lack of practical validation. Adjust the syllabus before expanding lessons.

**Stage 4 — Expand lessons in batches.** Do not try to squeeze a huge course into one reply. Expand one module (or a manageable batch) at a time using the lesson format below. Maintain a completed/pending checklist keyed to lesson IDs. Never silently skip a lesson. When the reply budget is reached, stop at a module boundary and provide a concise resume manifest listing completed IDs, pending IDs and the exact next batch.

**Stage 5 — Exercises, solutions, projects and exams.** Build practice materials with correct answers and explanations, then projects and a balanced final assessment. Ensure every exercise actually tests a taught skill and every project has a rubric and visible outcome.

**Stage 6 — Content QA and import packaging.** Run the validation checklist, produce the manifest and explain any unsupported or runner-dependent lesson. Provide machine-readable JSON that follows the schema below, plus the readable Markdown version. JSON must be valid JSON, with no comments or trailing commas.

### C. Curriculum architecture

Use the sequence that is natural for `[COURSE_NAME]`. Include relevant topics from these stages, omitting/renaming those that do not fit:

1. **Course overview:** definition, purpose, use cases, prerequisites, learning outcomes, setup, tools, version/standard assumptions and the roadmap.
2. **Foundations:** mental model, syntax, files/projects, first working example, environment, execution/interpretation and debugging.
3. **Core building blocks:** types/elements/constructs/syntax/commands/features of this technology; key concepts and their relationships.
4. **Control, composition and data:** logic, composition, APIs, data structures, schemas or other central constructs as appropriate.
5. **Practical patterns:** reusable patterns, architecture, integrations, common workflows, error handling and real use cases.
6. **Intermediate topics:** larger examples, project organization, best practices and trade-offs.
7. **Advanced topics:** performance, internals, optimization, concurrency, platform/browser/runtime features, advanced APIs or ecosystem-specific details.
8. **Security, privacy and accessibility:** include only the areas relevant to the technology; never imply a language alone provides complete system security.
9. **Testing, debugging and validation:** appropriate tooling, automated checks, reproducible cases and diagnostics.
10. **Tooling and professional workflow:** formatting, linting, version control, documentation, packaging/build/deployment as applicable.
11. **Ecosystem and integrations:** related tools and realistic interoperability. Clearly label concepts outside the technology itself.
12. **Projects and portfolio:** beginner, intermediate, advanced and one capstone when the scope supports it.
13. **References and final assessment:** summarized reference index, practical evaluation, improvement plan and next learning path.

Build at least one dependency table such as `Before learning → Learner should understand`, one course roadmap table, and one text-based flowchart. Provide a Mermaid flowchart where relationships/processes can be shown accurately. Keep optional/experimental/historical features out of the compulsory beginner path.

### D. Required lesson format

Each lesson must use this structure where relevant. If an element genuinely does not fit (e.g., code execution for a conceptual history lesson), say why rather than adding fake material.

1. **Lesson metadata:** stable lesson ID, title, slug, module, sequence, difficulty, estimated minutes, required prerequisites, core/optional label, keywords and previous/next lesson IDs.
2. **Why this matters:** one or two sentences tied to a practical task.
3. **Learning outcomes:** 2–4 observable statements using verbs like create, explain, compare, trace, debug or validate.
4. **Visual first:** at least one useful visual for concepts where relationships/steps help. Prefer CodeLeaf native dynamic diagram JSON rendered as responsive JSX cards/connectors, tables, timelines, state diagrams or side-by-side before/after. Do not use static images/SVGs for diagrams. Include a caption and describe what the learner should notice. Do not invent image URLs or claim an image exists when only a prompt is supplied.
5. **Concept explanation:** short chunks with meaningful headings; define jargon before using it; contrast similar ideas in a table.
6. **Minimal example:** correct and runnable code/config/query/command for the target. Explain important lines. Use the smallest example that genuinely demonstrates the concept.
7. **Run/observe:** specify editor/runtime, command or steps, expected output/result, and how to reset the state. If the platform will use an isolated runner, identify the runner mode and permissions it needs.
8. **Try it yourself:** one clear task with starter code/data, acceptance criteria and expected behavior. Do not show the full answer before the user attempts it unless the lesson explicitly requests a worked example.
9. **Hints:** progressive hints, from conceptual hint to exact pointer. Avoid leaking secret values or insecure shortcuts.
10. **Common mistakes:** a table containing mistake, why it happens, fix, and how to recognize it.
11. **Knowledge check:** 2–5 questions with answer and explanation kept in a separate solution block for the platform to reveal after an attempt.
12. **Recap:** 3–5 short points or a small summary diagram.
13. **Next step:** the next lesson/practice item, relevant reference and one real use case.
14. **QA notes:** official source links with the specific concept each supports, version/browser support caveat if relevant, and any item that requires human review.

Do not use filler such as “this is very important” without explaining why. Never state that HTML, CSS, JavaScript, Python or another single technology does something outside its actual capability. Use honest boundaries between the core technology, adjacent libraries, browser/runtime, operating system and backend.

### E. Visual learning rules

Aim for **visual explanation over verbose explanation**, but maintain accuracy and accessibility.

- For conceptual relationships: flowchart or labeled relationship diagram.
- For syntax/API differences: comparison table and small code snippets.
- For execution or lifecycle: sequence diagram or step timeline.
- For state/data: state diagram, memory/data table or before/after view.
- For algorithms: input → steps → output trace; add a flowchart and at least one worked trace when appropriate.
- For UI/web concepts: code pane + expected result description/mockup; include responsive behavior when relevant.
- For debugging: faulty example → observed error → diagnosis → corrected example.
- For APIs/commands: parameter table including type, purpose, default, return value/error behavior and safety notes when relevant.
- Use Mermaid syntax for flowcharts/sequence diagrams when supported. Otherwise provide a faithful text diagram. Keep contrast readable; color must not be the only signal.
- Each module should have a module overview visual. Do not force a diagram into a topic where it obscures a straightforward fact; explain the exception.

### F. Exercise and challenge design

Create a useful mixture of:
- Multiple-choice concept checks.
- Fill-in-the-blank or missing-token tasks.
- Predict-the-output traces.
- Debug/correct the code.
- Put steps/code blocks in order.
- Practical coding/query/config exercises with hidden tests where an execution runner exists.
- Small build tasks with a human-review checklist where automatic tests cannot evaluate quality.

Every exercise must include: stable ID; lesson/module ID; difficulty; prompt; target concept; input/starter material; expected output or acceptance criteria; hints; answer/solution; explanation; test cases or rubric; XP value (suggested only); retry policy. Never grade from client-submitted “correct” flags. Keep hidden tests out of public response payloads.

Progressive difficulty: warm-up → standard → transfer/application → challenge. Every major core concept needs at least one practice opportunity before the next concept assumes it.

### G. Project design

For each project, include:
- Project ID, name, tier, objective, real-world scenario and target skills.
- Prerequisite lesson IDs.
- Visual wireframe/architecture/process diagram or explicit diagram spec.
- Required features and optional stretch goals.
- Starter folder/file tree and starter code/data when useful.
- Milestones in the order they should be built.
- Expected final behavior/output and at least three test/use cases.
- Deliverables, accessibility/security/performance requirements when relevant.
- Rubric with measurable criteria and point weights totaling 100.
- Reference solution in a separate section, not mixed into learner instructions.

Project progression must reuse previous knowledge instead of suddenly requiring an unintroduced framework, service or API. Include at least three beginner projects, two intermediate, two advanced, and a capstone when appropriate for the technology; if that exact count would create artificial projects, justify the adjusted count.

### H. Final exam and certificate readiness

Generate a course exam blueprint before writing the full question set. Map question counts/points to learning outcomes and topic coverage. Include beginner/core/intermediate/advanced balance, practical problems where the runner can evaluate them, explanation per answer, and remediation links to lesson IDs. Provide a suggested pass score (default 70%, adjustable by platform policy), duration, attempts policy and allowed resources—but mark these as CodeLeaf platform policy choices, not facts about a certification authority. Never claim an industry-accredited credential unless the platform has actual authorization/accreditation. A platform certificate should have a verifiable unique ID and should only be issued after server-verified passing criteria.

### I. Research, correctness and copyright

- Use the latest stable/official documentation available at writing time and cite sources inline in a human-readable bibliography.
- Separate official specifications, vendor docs, community practice and your own recommendation.
- When version behavior matters, state the tested/assumed version and check support before release.
- Avoid obsolete or experimental APIs in the required core unless explicitly labeled historical/experimental.
- Do not copy long passages, diagrams, branded assets or examples from other publishers. Explain ideas in original words and create original examples.
- Code must be syntactically correct for the target and should be tested conceptually; never invent a passing test result.
- For security topics, recommend safe defaults and clearly identify what requires server-side enforcement or isolation.

### J. Output order

Return deliverables in this exact order:

1. **Course profile** — purpose, audience, prerequisites, outcomes, assumptions and version scope.
2. **Coverage map** — included areas and explicit out-of-scope areas.
3. **Visual roadmap** — Mermaid flowchart of the learning sequence.
4. **Full syllabus manifest** — modules and all lessons with sequence numbers, stable IDs, outcomes and dependencies; no placeholder such as “and more”.
5. **Dependency table** — prerequisite concepts by later module.
6. **Exercises map** — exercises per lesson/module and target skills.
7. **Project catalog** — beginner through capstone with milestone/rubric summaries.
8. **Final exam blueprint** — objective weights, formats and pass/retake policy suggestions.
9. **Content QA checklist** — coverage, duplicates, correctness, sources, accessibility, visuals and practice.
10. **Import-ready JSON manifest** following the schema in Section K.
11. **Detailed lesson batch** only after the complete manifest is delivered. In the first response, fully expand Module 1 unless the user requests syllabus-only. Then stop and provide the exact next batch to continue.
12. **References** — official first, supporting sources second, with direct URLs and a one-line relevance note.

If a response cannot fit all material, do not silently abbreviate the syllabus. Give the complete curriculum manifest first; defer lesson expansion to later batches and clearly label `NOT_YET_GENERATED` items.

### K. Import-ready manifest schema

Return a separate valid JSON block that follows this *shape* (add fields only when needed; maintain stable IDs):

```json
{
  "schema_version": "1.0",
  "course": {
    "slug": "course-slug",
    "title": "Course Title",
    "course_type": "language|framework|database|tool|concept",
    "category": "category",
    "level": "beginner-to-advanced",
    "version_scope": "version/standard assumption",
    "description": "Original concise description",
    "prerequisites": [],
    "learning_outcomes": [],
    "official_sources": [{"title": "Official docs", "url": "https://example.com", "supports": "What it verifies"}]
  },
  "stages": [{"id": "stage-01", "title": "Foundations", "sequence": 1}],
  "modules": [{
    "id": "course-module-01",
    "slug": "module-slug",
    "title": "Module title",
    "sequence": 1,
    "stage_id": "stage-01",
    "track": "core",
    "prerequisites": [],
    "learning_outcomes": [],
    "lesson_ids": []
  }],
  "lessons": [{
    "id": "course-lesson-001",
    "slug": "lesson-slug",
    "title": "Lesson title",
    "module_id": "course-module-01",
    "sequence": 1,
    "level": "beginner",
    "track": "core",
    "estimated_minutes": 10,
    "prerequisites": [],
    "keywords": [],
    "learning_outcomes": [],
    "visual_assets": [{"type": "mermaid|table|svg_spec|illustration_spec", "title": "Visual title", "source": "Complete source/description", "alt_text": "What it conveys"}],
    "content_blocks": [],
    "example_ids": [],
    "exercise_ids": [],
    "previous_lesson_id": null,
    "next_lesson_id": null,
    "sources": [{"url": "https://example.com", "supports": "Claim or API checked"}],
    "status": "draft"
  }],
  "exercises": [{"id": "course-exercise-001", "lesson_id": "course-lesson-001", "type": "mcq|fill_blank|predict_output|debug|ordering|coding|project_task", "difficulty": "easy", "prompt": "Task", "starter": "", "public_tests": [], "hidden_tests_reference": "server-only reference or null", "acceptance_criteria": [], "hints": [], "solution": "Separate solution", "explanation": "Why", "suggested_xp": 10}],
  "projects": [{"id": "course-project-01", "slug": "project-slug", "title": "Project title", "tier": "beginner", "objective": "Outcome", "prerequisite_lesson_ids": [], "milestones": [], "rubric": [{"criterion": "Criterion", "points": 25}], "solution_reference": "separate solution reference"}],
  "exam_blueprint": {"suggested_pass_percent": 70, "duration_minutes": 60, "topics": [{"module_id": "course-module-01", "weight_percent": 10}], "remediation_policy": "Review weak topics and retry under platform policy"},
  "qa": {"all_ids_unique": true, "dependencies_checked": true, "sources_to_reverify": [], "runner_requirements": [], "human_review_required": []}
}
```

The sample URLs/IDs above are illustrative; never ship them as source facts. Fill every module and lesson from the completed syllabus. JSON `content_blocks` must be structured data (e.g. `{"type":"paragraph","text":"..."}` or `{"type":"code","language":"python","code":"...","expected_output":"..."}`), not Markdown hidden inside invalid JSON. Mermaid source goes in a string with escaped newlines if needed.

### L. Definition of done

The curriculum is only “complete” when:
- Every required topic in the agreed scope maps to at least one lesson ID.
- Learning dependencies form a sensible order and have no unexplained cycle.
- Required core content is separate from optional advanced/specialized content.
- Every lesson has outcomes, at least one concrete example or justified exception, a practical check and real sources.
- Exercises have answer explanations and tests/rubrics; projects have milestones and 100-point rubrics.
- Examples and commands match the stated version and runtime.
- Diagram text/alt descriptions are supplied; lessons remain understandable to screen-reader and keyboard users.
- No obvious duplicate lessons or unsupported feature claims remain.
- The JSON parses; IDs/slugs are unique; all referenced module/lesson/exercise/project IDs exist.
- The output states which topics are yet to be expanded and what batch should be generated next.

**Start now with Stage 1 and Stage 2 for `[COURSE_NAME]`.** First check the supplied reference material, then deliver the whole course path and manifest. Do not start by writing only a few random lessons, and do not declare the complete platform or the full course implemented when you have only delivered the plan.

## MASTER PROMPT (copy ends here)

---

## How to use it well

1. Attach the subject's official documentation and, for the first course, the example `HTML(1).pdf`.
2. Replace `[COURSE_NAME]`, `[COURSE_TYPE]`, `[OFFICIAL_DOCS_URL]` and `[`TRUSTED_REFERENCE_URLS]`.
3. Ask for the full syllabus/manifest first; review it before generating all lesson text.
4. Then ask: **“Expand Module 1 in full using the agreed manifest IDs. Do not change other IDs. Include all visuals, examples, exercises and sources. Mark completion status.”** Repeat for each module.
5. Finally ask: **“Run the full course QA checklist, validate JSON and cross-reference all IDs. Return only corrections and the final import package.”**
6. Store each approved batch in version control. Do not rely on chat history alone for curriculum continuity.
