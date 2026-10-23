# Generative AI curriculum review notes

## Source review

- **Source:** `Generative AI.pdf`, 62 pages, supplied with this run.
- **Review date:** 2026-10-17.
- **Scope:** sections A–G, all 25 module headings, all 227 numbered main topics, all 1,334 decimal-numbered subtopics, the 16 practical exercises, 12 projects, six optional specialization tracks, and the eight-stage roadmap.
- **Visual inspection:** page contact sheets were inspected across all 62 rendered pages. The prominent embedded raster imagery on pages 52–54 consists of illustrative product/project screenshots; it is not a complete technical architecture specification. None of that third-party imagery or its branding has been copied. The course instead contains original SVG diagrams for all modules and lessons.

## Coverage decisions

- All source lesson titles and their listed subtopics are preserved in `syllabus-map.json` and mirrored in individual lesson JSON files.
- The 16 exercises follow Section C, and the 12 project names/objectives/features follow Section D, including Project 12 — Enterprise AI Knowledge and Workflow Platform.
- Section E's six optional specializations and ecosystem tool categories, Section F's eight-stage path/dependency guidance, and Section G's quality checklist are represented in the roadmap, reference index, lessons, and project test templates.
- Topic tracks are labeled core foundations, core application development, advanced specialization, optional specialization, or professional practice. This avoids making advanced model-training material a prerequisite for building a modest pretrained-model/API application.
- All content remains `draft`; generated outlines, explanations, examples, tests, and answer banks require subject-matter and instructional review before publishing.

## Corrections and constraints

- No syllabus topics were intentionally removed or silently replaced.
- Provider APIs are taught with provider-neutral design rules and selected official examples. No production model ID, API key, live pricing value, quota, or provider payload is assumed to be universal. The cost examples explicitly label rates as invented arithmetic examples.
- Python examples are local inspectable examples. CodeLeaf's current playground is an HTML/CSS/JavaScript iframe preview, not a secure arbitrary Python/code execution service. Python, model APIs, training, and external tools must be run locally or through separately isolated infrastructure where needed.
- The PDF's current/live-documentation recommendations are supported by primary references in `reference-index.json`; APIs and model behavior should be rechecked at implementation time.
- The 16 practical exercises use a basic static keyword grader only as a preliminary scaffold check. Their practical acceptance criteria require human review; these are not presented as fully automated evaluation of project quality.
- Projects include README files, text starter materials, protected design-outline solutions, and test-case templates. The implementations themselves were not built or run in this generation environment; their actual test evidence is explicitly marked **NOT RUN**.
- No database migrations, backend route changes, package changes, hosting changes, or frontend changes were made. The existing importer and API use generic course manifests, module/lesson records, knowledge-check files, and project manifests.

## Technical source links checked on 2026-10-17

- Google Machine Learning Crash Course: https://developers.google.com/machine-learning/crash-course/
- Python Tutorial: https://docs.python.org/3/tutorial/
- Hugging Face LLM Course: https://huggingface.co/learn/llm-course/en/chapter1/1
- PyTorch Learn the Basics: https://docs.pytorch.org/tutorials/beginner/basics/intro
- OpenAI API text generation: https://developers.openai.com/api/docs/guides/text
- OpenAI Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- OpenAI function calling: https://developers.openai.com/api/docs/guides/function-calling
- OpenAI vector embeddings: https://developers.openai.com/api/docs/guides/embeddings
- Anthropic prompting guidance: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-templates-and-variables
- Microsoft RAG design/evaluation: https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/rag-solution-design-and-evaluation-guide
- Hugging Face Agents Course: https://huggingface.co/learn/agents-course/en/unit0/introduction
- Hugging Face PEFT methods: https://huggingface.co/docs/peft/en/methods/overview
- OWASP GenAI Security Project: https://genai.owasp.org/initiative/owasp-top-10-for-llm-and-genai/
- NIST AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- Model Context Protocol specification: https://modelcontextprotocol.io/specification/2026-07-28
