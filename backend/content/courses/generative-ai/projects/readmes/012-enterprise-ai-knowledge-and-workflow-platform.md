# Enterprise AI Knowledge and Workflow Platform

## Objective
Build a role-aware knowledge assistant with grounded answers, validated extraction, and controlled workflows.

## Suggested architecture
Build from explicit interfaces for identity/access, ingestion, search, response generation, tool approvals, evaluations, and observability.

## Required features
- [ ] Role-based access and document-version management
- [ ] Semantic/hybrid search with optional reranking
- [ ] Citation-grounded answers and structured extraction
- [ ] Restricted tool workflows with human approval
- [ ] Regression tests, monitoring, privacy-aware logs, data deletion, and audit reports

## Setup (local development)
1. Create and activate a Python virtual environment.
2. Install only the pinned dependencies needed for the chosen provider, parser, vector store, or UI.
3. Copy the example environment template to a local, ignored `.env` file and add credentials only to the server environment. Never commit real credentials.
4. Implement an adapter interface and start with mocked model/tool responses.
5. Add one provider integration after checking its current official documentation and terms.
6. Run the project's unit tests and review the acceptance criteria below.

Project-specific notes: Use synthetic multi-tenant documents and local mocks; the capstone should have documented architecture, test evidence, a risk register, and a teardown procedure.

## Verification plan
Use `evaluation-cases.txt` as a starting checklist. Keep fixed test inputs, expected behaviors, test results, API/model versions, latency/cost observations, and failure cases. For model outputs, document the evaluator/rubric and retain human review where appropriate.

## Acceptance criteria
- [ ] Role-based access and document-version management
- [ ] Semantic/hybrid search with optional reranking
- [ ] Citation-grounded answers and structured extraction
- [ ] Restricted tool workflows with human approval
- [ ] Regression tests, monitoring, privacy-aware logs, data deletion, and audit reports
- [ ] Input validation and invalid-input tests pass.
- [ ] At least one failure/retry or insufficient-evidence case is covered.
- [ ] Sensitive data, credentials, and action permissions are tested.
- [ ] README describes setup, limitations, and a reproducible test command.

## Limitations and security boundaries
This is a teaching project brief and starter scaffold, not a deployed application. Do not claim that model output is fully accurate or that the system is secure without a documented evaluation. Provider APIs, costs, content rules, supported models, and legal requirements can change. Prefer synthetic/public test data, least privilege, human approval for consequential actions, and explicit stop conditions.

## Test evidence
**Status: NOT RUN.** This course-generation environment created the brief and test cases only; it did not build or deploy the project implementation or contact any paid/production AI API. Record actual environment versions, test commands, pass/fail results, and remaining risks here before publication.
