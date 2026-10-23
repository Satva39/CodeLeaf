# Database-Backed Inventory Service

## Goal
Create a maintainable application for managing products and stock.

## Requirements
- [ ] database persistence
- [ ] transaction handling
- [ ] validated updates
- [ ] audit history
- [ ] automated tests
- [ ] structured logging
- [ ] API or CLI

## How to work
1. Write an input/output contract and list expected failures.
2. Build the smallest useful vertical slice.
3. Add tests for behavior and boundary cases.
4. Run locally with the Ruby version declared by your project.
5. Document setup, configuration, data reset, and known limitations.

## Security and quality
Use synthetic data. Do not commit credentials. Use parameterized SQL, bounded network timeouts, safe file operations, and an explicit dry-run for destructive filesystem actions. CodeLeaf does not execute Ruby project code in its web process; use a local test environment or a separately isolated runner.
