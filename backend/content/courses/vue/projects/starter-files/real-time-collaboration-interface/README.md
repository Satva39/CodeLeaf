# Real-Time Collaboration Interface — starter brief

## Goal
Build a collaborative frontend connected to a backend service.

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

1. **Real-time event updates and connection status**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

2. **User presence and message history**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

3. **Shared state and stale-event handling**
   - Implement and test the behavior.
   - Record a normal case and a boundary/failure case.

4. **Automated tests for connection lifecycle**
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
