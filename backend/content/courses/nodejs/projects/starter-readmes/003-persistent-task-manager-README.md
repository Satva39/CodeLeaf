# Persistent Task Manager

## Objective

Build a CLI task manager that preserves validated data between sessions.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] Add, list, edit, complete, and delete tasks
- [ ] JSON persistence with safe updates
- [ ] Input validation and consistent error messages
- [ ] Reusable modules with clear responsibilities
- [ ] Unit tests for storage and task logic

## Stretch features

- [ ] Add CSV import/export
- [ ] Handle concurrent edits with an explicit file-lock strategy
- [ ] Introduce a storage adapter interface

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
