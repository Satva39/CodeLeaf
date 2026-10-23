# REST API Service

## Objective

Build a backend API exposing CRUD endpoints and a documented request/response contract.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] Routes, path parameters, query validation, and pagination
- [ ] Input schemas and centralized error handling
- [ ] Consistent status codes and response shape
- [ ] API documentation and health endpoint
- [ ] Unit and HTTP-level integration tests

## Stretch features

- [ ] Add request IDs and structured logs
- [ ] Implement versioned endpoints with compatibility tests
- [ ] Add rate limiting and an authorization boundary

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
