# HTML Flagship Curriculum — Completeness and Review Report

**Audit status: draft / internal review required.** This report records checks against the structured CodeLeaf course files in this project archive. It is not a claim that the course is production-ready or that every authored explanation and answer has received expert review.

## Structured inventory

- **26 modules** and **141 lessons** are linked from the HTML course manifest.
- **30 exercise definitions** are linked from lessons. Their graders use the existing server-supported `choice`, `exact_text`, and `contains_all` modes; each exercise remains a separate JSON file.
- **141 knowledge-check question-set files** contain **423 questions** in total (three per file). Answer keys and explanations remain in the private authored files. The question sets and final exam blueprint remain `draft`.
- **10 project guide files** are present. All remain `draft`. The project guide API labels automatically generated starter scaffolds rather than representing them as full reference solutions; solution files remain excluded from starter-kit ZIP generation.
- **6 reference entries** now live in separate JSON files. Each has an official HTTP(S) source, a plain-language explanation, a practical usage example, and related lesson slugs.
- **141 lesson diagram models are unique across the 141 lessons.** The legacy logical `.svg` pointers resolve to lesson-specific `.diagram.json` models. Validation checks node IDs, edge endpoints, source text mapping, alt text, and manifest references.
- The required instructional fields (`learning_outcomes`, task/acceptance criteria, hints, expected output, troubleshooting, common mistakes, summary and HTTP(S) sources) are present across the authored lesson set.

## Coverage visible in the lesson titles and authored structure

The structured curriculum includes foundations and syntax; document structure, text, links and lists; images and responsive images; audio/video; tables and forms; semantics and metadata; embedded resources and browser interactions; accessibility and keyboard access; validation and debugging; responsive and cross-browser behavior; localization; security and privacy; performance; professional workflows, version control and legacy migration. The current lesson content-block pattern includes diagrams, two explanatory paragraph blocks, a list of key ideas, a code example with expected output, and a callout. The reader has been updated to preserve their titles and instructional metadata and to render additional supported structured block types using plain React text—not raw HTML.

## Required caveats and gaps

1. **The curriculum PDF was not included in the received files.** The project metadata references `HTML(2).pdf`, but no matching PDF was available in the ZIP or as an attachment to this task. Its pages, figures, tables, exercises, and project outlines therefore could not be inspected, and PDF-to-file traceability cannot yet be certified. Re-run this review with the exact curriculum PDF before claiming that every source topic has been reconciled.
2. **Course publication remains disabled.** The course manifest, blueprint, all 141 question sets, and all 10 projects remain draft. The API hides draft content except when local preview is explicitly enabled. Nothing in this patch publishes it.
3. **The HTML certificate flow intentionally remains pending for capstone review.** The blueprint says the capstone is human-reviewed. A backend workflow for submitting/reviewing capstones is not implemented, so a passing exam alone does not issue an HTML completion certificate. The UI reports this state honestly.
4. **Content is structurally present but not fully editorially reviewed.** The source currently has only 22 distinct code snippets across 141 lesson code blocks (119 code blocks repeat snippets used elsewhere), and one example recurs 21 times. The completeness validator reports that reuse rather than treating structural field presence as proof of instruction quality. A reviewer needs to replace overly repeated examples with topic-specific examples and verify explanations, hints, common errors, exercise intent/solutions, question fairness and difficulty, accessibility, and browser behavior.
5. **Project scaffolds are not completed project solutions.** Generated starter file bodies are explicitly labelled as scaffolds. A human course reviewer still needs to verify each project's file-by-file implementation before the projects are published.
6. Browser-based execution of arbitrary learner code remains out of scope; snippets are displayed/previewed according to the existing run mode. No production deployment or live database was used by the local checks.

## Validation

Run from `backend/`:

```powershell
python scripts/validate_course_manifests.py --course html
python scripts/validate_html_flagship_completeness.py
python -m py_compile app/main.py app/project_guide_service.py scripts/validate_html_flagship_completeness.py scripts/test_phase2_exam_api.py scripts/test_phase2_content_routes.py
python scripts/test_phase2_exam_api.py
python scripts/test_phase2_content_routes.py
python scripts/test_knowledge_check_api.py
python scripts/test_dynamic_diagram_compatibility.py
```

These scripts are read-only or use a temporary SQLite database. A successful validation run confirms file integrity and declared invariants; it does not replace the missing PDF review or human content review.
