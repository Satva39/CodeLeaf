# Inventory and Order Management Platform

## Goal
Build a production-oriented application managing products, stock, customers, and orders through a complete release lifecycle.

## Requirements
- [ ] product management
- [ ] validated stock updates
- [ ] order state transitions
- [ ] database transactions
- [ ] relational persistence and migrations
- [ ] CLI or web API
- [ ] reliability and idempotency
- [ ] security and authorization
- [ ] automated tests
- [ ] operational quality and release readiness

## How to work
1. Write an input/output contract and list expected failures.
2. Build the smallest useful vertical slice.
3. Add tests for behavior and boundary cases.
4. Run locally with the Ruby version declared by your project.
5. Document setup, configuration, data reset, and known limitations.

## Security and quality
Use synthetic data. Do not commit credentials. Use parameterized SQL, bounded network timeouts, safe file operations, and an explicit dry-run for destructive filesystem actions. CodeLeaf does not execute Ruby project code in its web process; use a local test environment or a separately isolated runner.
