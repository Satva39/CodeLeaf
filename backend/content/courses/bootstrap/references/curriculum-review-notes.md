# Bootstrap curriculum review notes

## Source coverage

- Source: `Bootstrap.pdf`, all 37 pages visually reviewed, including the 161 numbered core topics, exercise tables, project descriptions, optional specializations, suggested learning path, and final quality-check section.
- The course preserves the full ordered topic sequence across 12 modules. Individual source syllabus numbers are recorded in each lesson and in `complete-syllabus.json`.
- All 23 source exercises are represented as separate drafts: B01–B07, I01–I08, and A01–A08.
- All nine named projects plus the production-ready commerce capstone are represented as separate draft briefs, each with a repository-only reference plan and a 100-point rubric.
- The source PDF calls the stable baseline Bootstrap 5.3.8 and discusses Bootstrap 6 alpha as future material. This course follows that version assumption; re-check official releases at publication.

## Corrections and clarification notes

1. **Subresource Integrity:** CDN version pinning and SRI are related but different. The example uses a version-pinned URL; production SRI hashes must be copied from the official documentation for the exact URL/file. No hash is guessed here.
2. **Optional CSS Grid:** Bootstrap 5.3 grid utility classes are opt-in and need the relevant Sass configuration and a rebuild. The lesson does not imply they are enabled in the default compiled CSS.
3. **Form validation:** Bootstrap's custom client-side validation styling/tooltips have documented accessibility limitations. Lessons emphasize native browser constraints, clear feedback, and server-side validation.
4. **Tooltips and popovers:** These require Bootstrap JavaScript initialization and Popper positioning. Use the bundle or configure Popper correctly; do not load duplicate builds.
5. **Framework integrations:** Bootstrap's DOM-manipulating plugins can conflict with React/Vue/Angular ownership if both systems mutate the same subtree. Choose framework-aware components or a clear ownership boundary.
6. **Bootstrap Icons:** Bootstrap Icons is a separate icon library, not automatically included with Bootstrap CSS.
7. **RTL:** Treat RTL as a specialist compatibility check and test the appropriate build, text direction, layout flow, controls, and iconography; `dir="rtl"` alone is not proof that every component is correctly mirrored.
8. **Bootstrap 4 migration and Bootstrap 6 alpha:** These are marked optional. Migration needs the official guide and testing; an alpha release is not used as the production baseline.
9. **Scope:** The capstone evaluates a frontend. Real authentication, payment capture, inventory, order processing, and secure file handling require application/backend services and are not provided by Bootstrap itself.

## Content boundaries and test assumptions

- This is a generated draft course. Every course/module/lesson/exercise/project is marked `draft` and needs technical, pedagogical, browser, accessibility, and editorial review before publication.
- Visuals are original locally generated SVG diagrams with meaningful titles, captions, and alt text.
- Knowledge-check answer keys and exercise/project reference materials are stored in separate protected repository files, relying on CodeLeaf's existing learner-safe API behavior. Verify that behavior again during deployment review.
- XP is not authored in content. Existing platform rules own XP and duplicate-reward behavior.
- No application source, database migrations, dependency manifests, or deployment configuration were changed. Integration uses the existing filesystem importer/API/catalog.
