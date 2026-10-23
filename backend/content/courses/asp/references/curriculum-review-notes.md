# Curriculum review notes — ASP (Classic Active Server Pages)

## Source inspected

- Source file: `ASP(1).pdf`, 35 pages.
- Inspection: all 35 pages rendered to images and reviewed as seven contact sheets; the text layer was also extracted and reconciled against the page images.
- Coverage: Section A (course overview); Section B (15 modules and topics 1–116); Section C (24 practical exercises); Section D (seven projects including capstone); Section E (eight optional specializations); Section F (six-stage learning path and dependency order); Section G (coverage and quality checks); and the official-reference list.
- The PDF says each numbered main topic can be developed as an individual lesson. This course therefore has 116 lesson files, preserving the PDF's numbering and subtopics.

## Coverage map

- Module 1: Introduction to ASP — lessons 1–8 (8 lesson files).
- Module 2: Web Fundamentals and the ASP Execution Environment — lessons 9–15 (7 lesson files).
- Module 3: VBScript Fundamentals for ASP — lessons 16–28 (13 lesson files).
- Module 4: Intermediate VBScript Programming — lessons 29–34 (6 lesson files).
- Module 5: HTML, Server-Side Scripting, and Page Composition — lessons 35–40 (6 lesson files).
- Module 6: Classic ASP Built-in Objects — lessons 41–47 (7 lesson files).
- Module 7: State, Cookies, and Application Events — lessons 48–53 (6 lesson files).
- Module 8: Forms, Input Handling, and Authentication — lessons 54–60 (7 lesson files).
- Module 9: Includes, Reuse, and Application Organization — lessons 61–64 (4 lesson files).
- Module 10: Databases and ADO — lessons 65–78 (14 lesson files).
- Module 11: Files, COM Components, and External Integrations — lessons 79–85 (7 lesson files).
- Module 12: Debugging, Testing, and Troubleshooting — lessons 86–91 (6 lesson files).
- Module 13: Security and Privacy — lessons 92–100 (9 lesson files).
- Module 14: Performance, Configuration, and Deployment — lessons 101–108 (8 lesson files).
- Module 15: Professional Maintenance and Migration — lessons 109–116 (8 lesson files).

## Corrections, clarifications, and scope notes

1. **Classic ASP is not ASP.NET.** The course follows the PDF's Classic ASP/VBScript/JScript + IIS + COM + ADO scope. ASP.NET and ASP.NET Core are not silently added as lessons.
2. **Support status is host-dependent.** Microsoft states that Classic ASP is supported on supported IIS versions, while the lifecycle follows the host Windows operating system. That is not a promise that every old server, provider, COM component, or third-party integration remains supported. Check the actual host lifecycle and dependency support before operational use.
3. **IIS setup guide age.** The Microsoft “Build a Classic ASP Website on IIS” guide includes setup steps for older operating systems. It is cited for core concepts, not treated as a current click-by-click guide for every present Windows release. Use the feature names and configuration available on the actual host.
4. **Parent-path default discrepancy in Microsoft pages.** The older step-by-step IIS page and configuration reference do not describe the default identically. The course therefore tells learners to inspect the effective setting, prefer application-rooted/virtual includes, and disable parent paths unless a reviewed legacy dependency requires otherwise.
5. **Password storage.** Classic ASP has no modern built-in identity/password-hashing framework. The course does not invent a new password hashing algorithm; it requires a reviewed server-side hashing/identity component and secure configuration.
6. **ADO parameter behavior.** Positional `?` placeholders, type constants, output parameters, cursor behavior, and connection strings vary by provider. Samples are labelled as inspectable and require verification against the real provider.
7. **File upload.** Classic ASP has no universal built-in multipart binary upload handler. The course teaches a secure workflow and calls for a vetted, compatible component where needed rather than pretending a generic snippet handles arbitrary file uploads.
8. **Security examples.** The course applies current OWASP defensive recommendations to the legacy context. Exercises use synthetic data and authorized local test environments; detailed diagnostics remain server-side.
9. **Execution limitations.** CodeLeaf's built-in browser playground previews HTML/CSS/JavaScript, not ASP/VBScript, IIS configuration, ADO, COM, PowerShell, or SQL. All Classic ASP samples are labelled `static-validation` and were not executed during generation.
10. **Excluded from core.** No numbered Section B topic or Section C/D exercise/project was intentionally excluded. The PDF's Section E specialist items (advanced IIS administration, COM administration, advanced ADO, enterprise integrations, security assessment, database modernization, application modernization, and legacy code maintenance) are carried into the course overview as optional tracks, with core concepts covered by the main modules.

## Learning roadmap preserved

1. Understand environment: Modules 1–2.
2. Learn VBScript and page composition: Modules 3–5.
3. Build objects/state/forms: Modules 6–9.
4. Work with ADO/data/integrations: Modules 10–11.
5. Prepare for production: Modules 12–14.
6. Maintain and modernize: Module 15 plus the capstone.

## Technical-source policy

Course-wide references were checked on 2026-10-15. The source index links Microsoft Learn support/IIS/ADO guidance and OWASP SQL-injection, XSS, CSRF, session, upload, and password-storage guidance. The specific version and provider of the learner's target environment remain an explicit verification item.
