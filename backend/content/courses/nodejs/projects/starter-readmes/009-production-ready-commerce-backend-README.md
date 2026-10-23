# Production-Ready Commerce Backend

## Objective

Design, test, secure, deploy, and maintain an online-marketplace backend with explicit operational controls.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] User registration, authentication, profiles, and role/resource authorization
- [ ] Product catalog, search, pagination, and inventory management
- [ ] Cart and order APIs with database transactions and server-side business rules
- [ ] Payment-provider integration in test mode with verified callbacks/webhooks and idempotency
- [ ] Background notification/retry jobs
- [ ] Documented API, validation, centralized errors, and automated tests
- [ ] Structured logging, health checks, environment config, and graceful shutdown
- [ ] Dependency auditing, deployment automation, security review, and performance tests

## Stretch features

- [ ] Add an outbox/reconciliation strategy for payment state
- [ ] Define backup/restore, incident, and rollback runbooks
- [ ] Run a threat-model and failure-mode review

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
