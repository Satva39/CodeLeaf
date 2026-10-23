# Multimodal Content Studio

## Objective
Create a managed workflow that combines text and compatible image/audio outputs.

## Suggested architecture
Design an asset manifest and status transitions; separate model calls from media storage and review steps.

## Required features
- [ ] Brief-to-media workflow with supported formats
- [ ] Asset metadata and provenance records
- [ ] Preview, regenerate, and delete controls
- [ ] Moderation/quality checks appropriate to each modality
- [ ] License/consent review and evaluation records

## Setup (local development)
1. Create and activate a Python virtual environment.
2. Install only the pinned dependencies needed for the chosen provider, parser, vector store, or UI.
3. Copy the example environment template to a local, ignored `.env` file and add credentials only to the server environment. Never commit real credentials.
4. Implement an adapter interface and start with mocked model/tool responses.
5. Add one provider integration after checking its current official documentation and terms.
6. Run the project's unit tests and review the acceptance criteria below.

Project-specific notes: Start with a provider sandbox or offline metadata mocks; review each provider's format, content, and retention rules before upload.

## Verification plan
Use `evaluation-cases.txt` as a starting checklist. Keep fixed test inputs, expected behaviors, test results, API/model versions, latency/cost observations, and failure cases. For model outputs, document the evaluator/rubric and retain human review where appropriate.

## Acceptance criteria
- [ ] Brief-to-media workflow with supported formats
- [ ] Asset metadata and provenance records
- [ ] Preview, regenerate, and delete controls
- [ ] Moderation/quality checks appropriate to each modality
- [ ] License/consent review and evaluation records
- [ ] Input validation and invalid-input tests pass.
- [ ] At least one failure/retry or insufficient-evidence case is covered.
- [ ] Sensitive data, credentials, and action permissions are tested.
- [ ] README describes setup, limitations, and a reproducible test command.

## Limitations and security boundaries
This is a teaching project brief and starter scaffold, not a deployed application. Do not claim that model output is fully accurate or that the system is secure without a documented evaluation. Provider APIs, costs, content rules, supported models, and legal requirements can change. Prefer synthetic/public test data, least privilege, human approval for consequential actions, and explicit stop conditions.

## Test evidence
**Status: NOT RUN.** This course-generation environment created the brief and test cases only; it did not build or deploy the project implementation or contact any paid/production AI API. Record actual environment versions, test commands, pass/fail results, and remaining risks here before publication.
