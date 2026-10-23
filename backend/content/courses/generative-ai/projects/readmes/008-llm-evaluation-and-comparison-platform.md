# LLM Evaluation and Comparison Platform

## Objective
Compare models and prompt versions using a repeatable dataset, rubric, and resource metrics.

## Suggested architecture
Define stable case IDs, normalized model responses, evaluator interfaces, and report outputs for quality, cost, and latency.

## Required features
- [ ] Versioned evaluation dataset and prompt registry
- [ ] Configurable rubrics and human rating interface
- [ ] Blind side-by-side comparison where useful
- [ ] Latency and cost accounting
- [ ] Regression reports with known limitations

## Setup (local development)
1. Create and activate a Python virtual environment.
2. Install only the pinned dependencies needed for the chosen provider, parser, vector store, or UI.
3. Copy the example environment template to a local, ignored `.env` file and add credentials only to the server environment. Never commit real credentials.
4. Implement an adapter interface and start with mocked model/tool responses.
5. Add one provider integration after checking its current official documentation and terms.
6. Run the project's unit tests and review the acceptance criteria below.

Project-specific notes: Create a small fixed synthetic dataset and a mock model adapter before calling paid APIs.

## Verification plan
Use `evaluation-cases.txt` as a starting checklist. Keep fixed test inputs, expected behaviors, test results, API/model versions, latency/cost observations, and failure cases. For model outputs, document the evaluator/rubric and retain human review where appropriate.

## Acceptance criteria
- [ ] Versioned evaluation dataset and prompt registry
- [ ] Configurable rubrics and human rating interface
- [ ] Blind side-by-side comparison where useful
- [ ] Latency and cost accounting
- [ ] Regression reports with known limitations
- [ ] Input validation and invalid-input tests pass.
- [ ] At least one failure/retry or insufficient-evidence case is covered.
- [ ] Sensitive data, credentials, and action permissions are tested.
- [ ] README describes setup, limitations, and a reproducible test command.

## Limitations and security boundaries
This is a teaching project brief and starter scaffold, not a deployed application. Do not claim that model output is fully accurate or that the system is secure without a documented evaluation. Provider APIs, costs, content rules, supported models, and legal requirements can change. Prefer synthetic/public test data, least privilege, human approval for consequential actions, and explicit stop conditions.

## Test evidence
**Status: NOT RUN.** This course-generation environment created the brief and test cases only; it did not build or deploy the project implementation or contact any paid/production AI API. Record actual environment versions, test commands, pass/fail results, and remaining risks here before publication.
