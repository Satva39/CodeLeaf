# Django course status

- **Status:** draft; not publish-ready.
- **Source inspected:** attached 61-page Django curriculum PDF and the current CodeLeaf project ZIP.
- **Generated coverage:** 24 modules, 275 lessons, 15 practical exercises with protected solutions, 10 project briefs with starter notes/reference outlines, 275 knowledge-check sets (825 questions), and one draft final assessment blueprint with 40 repository-side draft questions.
- **Visual assets:** original local SVGs listed in `assets/asset-manifest.json`; all manifest paths are included and locally validated as XML/SVG.
- **Integration:** uses the existing file-based content schema and course importer. No frontend, backend route, model, migration, dependency, or hosting configuration change is included in this patch.
- **Not claimed:** Django code execution, live app tests, external payment/webhook/email delivery, exam UI integration, certificate issuance, production deployment, or database import against a live CodeLeaf database.
- **Before publication:** run the file validator and importer dry-run, connect/import to a disposable staging database, test the learner-facing API and hiding of answer keys, review lesson snippets with the supported Django patch release, have a Django specialist review technical accuracy and a teacher review the 275 lessons, validate accessibility, test project briefs, and integrate a real isolated runner/exam workflow only if those features are planned.
