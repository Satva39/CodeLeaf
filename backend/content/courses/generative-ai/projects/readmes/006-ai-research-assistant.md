# AI Research Assistant

## Objective
Search a controlled source collection and produce traceable summaries with explicit claim support.

## Suggested architecture
Create a source record schema, retrieval baseline, citation object, and rubric for claim coverage and unsupported statements.

## Required features
- [ ] Search and source comparison
- [ ] Question answering over selected documents
- [ ] Notes and outline generation
- [ ] Citation tracking and unsupported-claim checks
- [ ] Document version and source provenance

## Setup (local development)
1. Create and activate a Python virtual environment.
2. Install only the pinned dependencies needed for the chosen provider, parser, vector store, or UI.
3. Copy the example environment template to a local, ignored `.env` file and add credentials only to the server environment. Never commit real credentials.
4. Implement an adapter interface and start with mocked model/tool responses.
5. Add one provider integration after checking its current official documentation and terms.
6. Run the project's unit tests and review the acceptance criteria below.

Project-specific notes: Use public or synthetic documents; retain the source collection and evaluation questions alongside the project.

## Verification plan
Use `evaluation-cases.txt` as a starting checklist. Keep fixed test inputs, expected behaviors, test results, API/model versions, latency/cost observations, and failure cases. For model outputs, document the evaluator/rubric and retain human review where appropriate.

## Acceptance criteria
- [ ] Search and source comparison
- [ ] Question answering over selected documents
- [ ] Notes and outline generation
- [ ] Citation tracking and unsupported-claim checks
- [ ] Document version and source provenance
- [ ] Input validation and invalid-input tests pass.
- [ ] At least one failure/retry or insufficient-evidence case is covered.
- [ ] Sensitive data, credentials, and action permissions are tested.
- [ ] README describes setup, limitations, and a reproducible test command.

## Limitations and security boundaries
This is a teaching project brief and starter scaffold, not a deployed application. Do not claim that model output is fully accurate or that the system is secure without a documented evaluation. Provider APIs, costs, content rules, supported models, and legal requirements can change. Prefer synthetic/public test data, least privilege, human approval for consequential actions, and explicit stop conditions.

## Test evidence
**Status: NOT RUN.** This course-generation environment created the brief and test cases only; it did not build or deploy the project implementation or contact any paid/production AI API. Record actual environment versions, test commands, pass/fail results, and remaining risks here before publication.
