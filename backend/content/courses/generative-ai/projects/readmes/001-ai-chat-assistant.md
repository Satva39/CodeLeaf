# AI Chat Assistant

## Objective
Build a conversational UI and secure backend adapter for a hosted model API.

## Suggested architecture
Create a client interface that accepts a user message and returns a normalized response; isolate provider-specific payload parsing behind an adapter.

## Required features
- [ ] Conversation history with a documented reset behavior
- [ ] Streaming where the chosen provider supports it
- [ ] Loading, empty, cancellation, and provider-error states
- [ ] Server-side API credentials and bounded request controls
- [ ] Clear AI-use disclosure and feedback/correction controls

## Setup (local development)
1. Create and activate a Python virtual environment.
2. Install only the pinned dependencies needed for the chosen provider, parser, vector store, or UI.
3. Copy the example environment template to a local, ignored `.env` file and add credentials only to the server environment. Never commit real credentials.
4. Implement an adapter interface and start with mocked model/tool responses.
5. Add one provider integration after checking its current official documentation and terms.
6. Run the project's unit tests and review the acceptance criteria below.

Project-specific notes: Create a Python virtual environment, install a pinned HTTP client, define provider settings in a local backend environment, then run the local API and UI separately.

## Verification plan
Use `evaluation-cases.txt` as a starting checklist. Keep fixed test inputs, expected behaviors, test results, API/model versions, latency/cost observations, and failure cases. For model outputs, document the evaluator/rubric and retain human review where appropriate.

## Acceptance criteria
- [ ] Conversation history with a documented reset behavior
- [ ] Streaming where the chosen provider supports it
- [ ] Loading, empty, cancellation, and provider-error states
- [ ] Server-side API credentials and bounded request controls
- [ ] Clear AI-use disclosure and feedback/correction controls
- [ ] Input validation and invalid-input tests pass.
- [ ] At least one failure/retry or insufficient-evidence case is covered.
- [ ] Sensitive data, credentials, and action permissions are tested.
- [ ] README describes setup, limitations, and a reproducible test command.

## Limitations and security boundaries
This is a teaching project brief and starter scaffold, not a deployed application. Do not claim that model output is fully accurate or that the system is secure without a documented evaluation. Provider APIs, costs, content rules, supported models, and legal requirements can change. Prefer synthetic/public test data, least privilege, human approval for consequential actions, and explicit stop conditions.

## Test evidence
**Status: NOT RUN.** This course-generation environment created the brief and test cases only; it did not build or deploy the project implementation or contact any paid/production AI API. Record actual environment versions, test commands, pass/fail results, and remaining risks here before publication.
