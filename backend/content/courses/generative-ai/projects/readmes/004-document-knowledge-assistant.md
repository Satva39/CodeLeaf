# Document Knowledge Assistant

## Objective
Answer questions from an authorized document collection with traceable evidence.

## Suggested architecture
Build separate ingestion, chunking, retrieval, context assembly, answer validation, and citation formatting modules.

## Required features
- [ ] Document ingestion and chunking
- [ ] Embedding or hybrid retrieval
- [ ] Grounded answers with source identifiers
- [ ] Insufficient-evidence responses
- [ ] Tenant/user access filters before retrieval

## Setup (local development)
1. Create and activate a Python virtual environment.
2. Install only the pinned dependencies needed for the chosen provider, parser, vector store, or UI.
3. Copy the example environment template to a local, ignored `.env` file and add credentials only to the server environment. Never commit real credentials.
4. Implement an adapter interface and start with mocked model/tool responses.
5. Add one provider integration after checking its current official documentation and terms.
6. Run the project's unit tests and review the acceptance criteria below.

Project-specific notes: Begin with five synthetic documents and fixed questions; implement an index interface so embedding/vector-store providers can be changed.

## Verification plan
Use `evaluation-cases.txt` as a starting checklist. Keep fixed test inputs, expected behaviors, test results, API/model versions, latency/cost observations, and failure cases. For model outputs, document the evaluator/rubric and retain human review where appropriate.

## Acceptance criteria
- [ ] Document ingestion and chunking
- [ ] Embedding or hybrid retrieval
- [ ] Grounded answers with source identifiers
- [ ] Insufficient-evidence responses
- [ ] Tenant/user access filters before retrieval
- [ ] Input validation and invalid-input tests pass.
- [ ] At least one failure/retry or insufficient-evidence case is covered.
- [ ] Sensitive data, credentials, and action permissions are tested.
- [ ] README describes setup, limitations, and a reproducible test command.

## Limitations and security boundaries
This is a teaching project brief and starter scaffold, not a deployed application. Do not claim that model output is fully accurate or that the system is secure without a documented evaluation. Provider APIs, costs, content rules, supported models, and legal requirements can change. Prefer synthetic/public test data, least privilege, human approval for consequential actions, and explicit stop conditions.

## Test evidence
**Status: NOT RUN.** This course-generation environment created the brief and test cases only; it did not build or deploy the project implementation or contact any paid/production AI API. Record actual environment versions, test commands, pass/fail results, and remaining risks here before publication.
