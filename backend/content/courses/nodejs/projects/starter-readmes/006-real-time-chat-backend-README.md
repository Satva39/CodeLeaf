# Real-Time Chat Backend

## Objective

Deliver authorized messages between connected users and preserve important conversation history.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] Authenticated connections and resource-level authorization
- [ ] Private conversation membership checks
- [ ] Message persistence and deterministic ordering
- [ ] Online presence with disconnect cleanup
- [ ] Reconnect handling and tests for duplicate delivery

## Stretch features

- [ ] Add horizontal-scale adapter or event broker design
- [ ] Add per-room rate limits and retention rules
- [ ] Measure load and reconnect behavior

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
