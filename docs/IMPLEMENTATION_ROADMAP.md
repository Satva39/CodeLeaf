# CodeLeaf implementation roadmap

This roadmap is intentionally incremental. Each phase should be applied, tested, and reviewed before the next phase is merged. Do not deploy unverified bulk changes to production.

## Phase 1 — Learning core and navigation (current patch)
- Add lesson-aware live examples near the explanation/code section.
- Use sandboxed browser previews only for browser-native HTML, CSS, and JavaScript examples.
- Use explicitly labelled interactive simulations for concepts whose native execution environment is not available; never imply that Python, native binaries, SQL, shell commands, or framework templates actually ran when they did not.
- Restore single-open course-module navigation. The active lesson's module is expanded by default; selecting another module closes the previous one; navigating to a lesson moves the expansion to that lesson's module.
- Add accessible `aria-expanded`/`aria-controls` state to module headings.
- Acceptance: model tests, sandbox policy tests, navigation contract checks, full frontend build, and manual smoke tests for HTML, CSS transforms, JavaScript, and one simulated language.

## Phase 2 — Course and content consistency
- Preserve existing shared style imports while finishing the tutorial-only course overview design.
- Ensure references, project guides, and practice pages use their own page-specific layouts rather than tutorial-only details.
- Use a shared reference-detail renderer with full-width outer panel, grounded source/topic metadata, suitable practical guidance, and accurately labelled related lesson links.
- Audit course manifests, imported content, route links, empty states, assets, and publication flags.
- Acceptance: all 62 published course catalogs load; reference/course links resolve; draft content stays hidden; all pages pass responsive checks.

## Phase 3 — Practice and progress
- Audit lesson completion, exercise attempts, bookmarks, notes, course progress, XP, streaks, and revision state.
- Preserve learner progress across content updates and ensure progress and rewards are server-authoritative and idempotent.
- Add revision queues and useful feedback for incorrect answers.
- Acceptance: API integration tests for anonymous, guest, and signed-in flows; duplicate submissions do not duplicate rewards; progress persists across sessions.

## Phase 4 — Authentication, email, and subscriptions
- Verify registration, email verification, password reset, existing-user login, expiry, and recovery flows.
- Validate transactional email sender requirements, SMTP authorization, delivery errors, and retries using the configured provider.
- Validate Razorpay checkout, webhook signatures, subscription lifecycle, cancellation, renewal, and entitlement checks.
- Acceptance: tests in payment test mode, email-delivery smoke test, and negative authorization tests. Never expose secrets in the frontend or repository.

## Phase 5 — Projects and coding playground
- Add structured starter projects, milestones, tests, hints, troubleshooting, and honest solution boundaries.
- Expand the playground with saved snippets, multi-file projects where appropriate, and language-specific execution environments.
- Run untrusted server-side code only in an isolated execution service with strict CPU, memory, time, filesystem, and network limits.
- Acceptance: starter archives validate, project files exist, test results are truthful, and unsafe execution paths are blocked.

## Phase 6 — Accessibility, performance, security, and operations
- Run responsive and keyboard-accessibility checks, accessible labels/focus states, reduced-motion checks, and contrast reviews.
- Measure Core Web Vitals, remove redundant requests, and tune caching/pagination only from measured bottlenecks.
- Review security headers, backend authorization, validation, rate limits, logs, and dependency hygiene.
- Add deployment smoke tests, health monitoring, and rollback instructions.
- Acceptance: successful build and tests, production smoke checks, and no secrets in tracked files.

## Phase 7 — Personalization, AI, and growth
- Start with transparent rule-based recommendations and a course-aware tutor grounded in published CodeLeaf material.
- Clearly label generated suggestions, protect learner privacy, and add provider quotas/fallbacks.
- Expand discovery/search, learning paths, portfolio presentation, and opt-in notification preferences.
- Acceptance: recommendations have explainable reasons, AI answers link to course sources where possible, and unavailable external services degrade gracefully.
