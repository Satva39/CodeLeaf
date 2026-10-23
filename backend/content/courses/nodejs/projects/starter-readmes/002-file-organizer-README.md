# File Organizer

## Objective

Create a utility that organizes files into folders safely and predictably.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] Extension-based folder mapping
- [ ] Configurable source and destination paths
- [ ] Duplicate-name conflict policy
- [ ] Preview/dry-run mode
- [ ] Filesystem errors and path traversal protection

## Stretch features

- [ ] Add resumable execution and a structured audit log
- [ ] Process large directories with bounded concurrency
- [ ] Provide an undo manifest

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
