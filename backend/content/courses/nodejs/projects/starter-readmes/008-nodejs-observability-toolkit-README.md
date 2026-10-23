# Node.js Observability Toolkit

## Objective

Create a reusable toolkit that helps developers inspect behavior and performance safely.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] Structured logging with sensitive-value redaction
- [ ] Request/correlation identifiers using async context
- [ ] Runtime and request timing measurements
- [ ] Diagnostic report and error categorization helpers
- [ ] Reproducible benchmark command and README

## Stretch features

- [ ] Expose metrics in a pull-based format
- [ ] Add a minimal pluggable output API
- [ ] Add tests for data redaction and context isolation

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
