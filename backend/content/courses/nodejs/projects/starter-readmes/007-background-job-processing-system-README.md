# Background Job Processing System

## Objective

Process long-running work outside request handlers with bounded concurrency and resilience.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] Queue and worker separation
- [ ] Bounded concurrency and cancellation
- [ ] Retry policy with backoff/jitter and a maximum attempt count
- [ ] Failed-job records and idempotency keys
- [ ] Metrics, logging, and graceful shutdown

## Stretch features

- [ ] Add a dead-letter queue and operator retry path
- [ ] Persist scheduling state across restarts
- [ ] Compare worker threads, child processes, and a separate queue service

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
