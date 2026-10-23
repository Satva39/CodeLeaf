# Inventory Management Backend

## Objective

Build a relational database-backed inventory service with reliable stock changes.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] Product and stock schema with migrations
- [ ] Parameterized queries and managed connection pool
- [ ] Transaction-safe stock adjustments
- [ ] Authentication and role/resource authorization
- [ ] Audit-friendly logs and regression tests

## Stretch features

- [ ] Add idempotent stock reservation requests
- [ ] Add an outbox pattern for reliable events
- [ ] Profile queries with representative data

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
