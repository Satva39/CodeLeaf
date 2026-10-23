# PDF Coverage and Technical Review Notes

## Coverage decision

The attached PDF's Section B is represented in order: all 21 module headings, all 162 numbered lesson titles, and the extracted subtopic lists. Section C's 28 practical exercises, Section D's 10 projects and capstone, and Section E's six optional specialist tracks are included. No syllabus topic was intentionally dropped. The original PDF is primarily text: a 47-page render review found no embedded raster image objects in `pdfimages -list`; original CodeLeaf SVG overview diagrams were created because the source PDF itself does not provide teaching diagrams to reuse.

## Normalization and corrections

- The requested label `[Github Actoin]` contains a spelling error; the course uses the official product name **GitHub Actions** and the stable slug `github-actions`.
- The PDF's optional Section E tracks are not given numbered lesson IDs. To fit CodeLeaf's required stable, consecutive sequence IDs without changing the core order, they are represented as lessons 163–168 with source IDs E1–E6 and live in a separate optional module.
- The PDF correctly phrases YAML anchors and aliases as “where supported.” This compatibility note is retained: validate against the target GitHub.com/GitHub Enterprise Server version and the current workflow syntax reference.
- GitHub documentation reviewed on 2026-10-20 recommends pinning actions to verified full commit SHAs as an immutable action reference when using that model. Tutorial snippets use major version tags for readability; the lesson content explicitly says to review/pin production dependencies according to repository policy.
- OIDC examples deliberately stop before provider-specific login because cloud issuer, audience, subject/environment claims, permissions, and provider actions must be configured for the actual target. Placeholder examples are labelled as design/static-validation material, not as tested cloud deployment code.
- A cache is described as a reusable store for dependencies/rebuildable inputs; an artifact is described as output/report storage and inter-job transfer. Neither should contain secrets.
- `pull_request_target`, privileged `workflow_run` patterns, action trust, untrusted event input, and self-hosted runner boundaries are treated as security-sensitive rather than beginner conveniences.
- Feature availability, action runtime support, ARC/runner scale-set capabilities, pricing, retention, and plan-level behavior can change. The course instructs learners to re-check current docs; it does not assert that every feature is available to every account or GitHub Enterprise Server version.
- GitHub Agentic Workflows are not added as a course lesson because they do not appear in the attached syllabus scope. They may be considered in a separately reviewed future update rather than silently changing this course blueprint.

## Source distinction

- **PDF-derived:** module and numbered lesson hierarchy, subtopics, practical exercises, projects, capstone requirements, and optional track names. These are preserved in `syllabus-map.json`.
- **Officially cross-checked:** links in `references/reference-index.json` and lesson-level source arrays point to GitHub or GitHub CLI documentation consulted on 2026-10-20.
- **CodeLeaf-authored:** explanations, examples, exercises, question distractors, SVG diagrams, review checklists, and recommended validation steps are original instructional content; they are not quotations from the PDF.

## Known execution boundaries

The content import path is tested independently of GitHub-hosted workflow execution. Workflow snippets in lessons vary in status: runnable minimal workflow, illustrative fragment, metadata outline, or design sketch. A static JSON/SVG validation does not mean a GitHub Actions run, cloud deployment, OIDC trust setup, custom action bundle, or self-hosted runner was executed.
