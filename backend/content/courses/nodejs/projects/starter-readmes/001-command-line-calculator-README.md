# Command-Line Calculator

## Objective

Build a terminal calculator with argument validation, clear usage/error messages, and appropriate exit codes.

## Suggested setup

1. Create a new folder and initialize a Node.js project.
2. Select a supported Node.js LTS release and document it.
3. Split runtime code, tests, configuration, and documentation by responsibility.
4. Do not commit `.env` files, service credentials, private keys, or real user data.

## Required features

- [ ] Arithmetic operations for supported operators
- [ ] Argument parsing and finite-number validation
- [ ] Help and usage output
- [ ] Readable errors and meaningful process exit codes
- [ ] Automated checks for valid and invalid input

## Stretch features

- [ ] Support a safe expression grammar without eval()
- [ ] Add localized number formatting
- [ ] Publish a private test package before a public release

## Validation checklist

- [ ] Write down the expected outcome before running each test.
- [ ] Cover normal and failure/boundary behavior.
- [ ] Run automated tests with `node --test` or the documented project test command.
- [ ] Record Node.js and dependency versions.
- [ ] Document known limits and operational/security assumptions.
