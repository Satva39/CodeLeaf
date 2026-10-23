# AI Curriculum Review Notes

## Source inspection

- Source file: `AI.pdf` (45 pages). The PDF text layer was extracted for all pages, checked against a visual contact sheet of all 45 rendered pages, and used to preserve the numbered lesson titles and subtopic lists.
- Section B includes 18 modules and 158 numbered lessons. Section C contains 24 practical exercises. Section D contains 10 projects, including the capstone “AI Learning and Knowledge Platform”. Sections E–G supply optional tracks, the staged learning path, and the quality audit.
- This patch carries the source's module order, lesson numbering, subtopics, exercise names and objectives, project names/objectives/features, learning stages, prerequisite relationships, and specialist tracks into separate files. All generated content remains `draft`.

## Editorial and technical decisions

1. **No syllabus items intentionally omitted.** All 18 modules, 158 numbered lesson records and listed lesson subtopics are preserved. All 24 exercises and all 10 projects are represented.
2. **Capability labels are qualified.** Artificial general intelligence is described as a research concept and artificial superintelligence as hypothetical; the course does not imply either is an established deployed capability.
3. **Evaluation is explicit.** The course repeatedly distinguishes training from inference, validation from final testing, correlation from causation, and fluent output from verified fact. Toy examples and a demo are not presented as evidence of production reliability.
4. **Vendor neutrality is preserved.** Tool names in the source's optional ecosystem are retained as examples in `specialist-tracks.json`, not as mandatory dependencies. Provider-specific interfaces, model names, APIs, legal requirements, and benchmarks need a current official-doc check before use.
5. **Source link cleanup.** The PDF includes abbreviated source callouts (for example, “Google for … +2”, “AIRC +1”, and a project screenshot attribution string). These are not treated as valid bibliographic records. The reference index uses direct official sources and records the check date; the screenshot is not copied.
6. **Current source caveats.** The NIST AI RMF official resource indicates that AI RMF 1.0 is being updated, so version-specific governance should be checked on NIST's live page. OWASP's GenAI security guidance is also updated over time; consult its live project page before a security review.
7. **Implementation boundary.** Existing CodeLeaf routes/importer support directory-based course content, lesson knowledge checks, SVG assets, and project files. No schema or application code change is needed for this content-only patch. Static Python snippets are examples for local inspection; they do not execute in the browser or call a model API. Do not run arbitrary learner code inside the FastAPI production service.
8. **Assessment protection.** Per-lesson question sets and reference solutions remain in the backend content repository. The final exam file is a blueprint; it does not claim a live timed exam engine, issuance of certificates, or persisted exam attempts.
9. **Review status.** Every course, module, lesson, exercise, project, solution outline, question set, and diagram is draft and should receive subject-matter and assessment review before publication. The lightweight graders are only submission gates, not proof of technical correctness.

## Official references checked on 2026-10-15

- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course/) — ML, neural networks, embeddings and evaluation.
- [UNESCO AI competency framework for students](https://www.unesco.org/en/articles/ai-competency-framework-students?hub=84624) — human-centred and ethical AI competencies.
- [NIST AI Risk Management Framework resources](https://airc.nist.gov/airmf-resources/airmf/) — risk and trustworthiness; check the live update status.
- [scikit-learn Getting Started](https://scikit-learn.org/stable/getting_started) — fitting, splits and model evaluation.
- [PyTorch Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html) — tensors and training workflow.
- [Microsoft Learn AI concepts](https://learn.microsoft.com/en-us/training/paths/ai-concepts) and [generative AI and agents](https://learn.microsoft.com/en-us/training/modules/fundamentals-generative-ai/) — optional tool-specific learning paths.
- [OWASP GenAI Security Project](https://genai.owasp.org/initiative/owasp-top-10-for-llm-and-genai/) — current LLM/GenAI application security guidance.
