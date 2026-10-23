# Full-Scale Commerce Platform — starter brief

## Goal
Build a production-oriented multi-page commerce frontend and integrate with a backend API.

## Setup
1. Create a separate Vue 3 project with the official `create-vue` workflow.
2. Run `npm install` and `npm run dev`.
3. Keep source files in JavaScript and Vue Single-File Components. The CodeLeaf course patch does not provide or run a production backend.

## Suggested structure
- `src/components/` — reusable visual components
- `src/views/` — route-level pages when routing is needed
- `src/composables/` — reusable reactive logic
- `src/services/` — HTTP requests and response validation
- `src/stores/` — shared Pinia state when it helps

## Milestones

1. **Responsive home page, catalog, and product details**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

2. **Search, filters, sorting, and pagination**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

3. **Cart and checkout form with server-confirmed totals**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

4. **API service with loading/empty/error states**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

5. **Router-based navigation and lazy-loaded views**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

6. **Pinia for appropriate shared UI state**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

7. **Reusable components, slots, and composables**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

8. **Accessible navigation and validation messages**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

9. **Unit, component, and end-to-end tests**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

10. **Production build, deployment, configuration, and runbook**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

## Acceptance checklist
- [ ] All required features above are present.
- [ ] Forms and controls have labels, keyboard support, and clear errors.
- [ ] API/remote data has loading, empty, success, and error states.
- [ ] Sensitive prices, payments, inventory, authentication, and authorization are not trusted from client-side state.
- [ ] Tests or manual verification steps are reproducible.
- [ ] `npm run build` succeeds in the separate project.
- [ ] Setup, environment configuration, and known limitations are documented.

## Submission evidence
Attach the folder structure, key snippets, test output, screenshots where useful, and a note about what was not tested. Do not include credentials or `.env` secrets.
