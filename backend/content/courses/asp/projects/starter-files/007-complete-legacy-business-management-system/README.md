# Complete Legacy Business Management System

**Objective:** Deliver a maintainable Classic ASP application representing a realistic legacy business system.

## Required features
- [ ] User login and role-based authorization
- [ ] Database-backed customer/inventory records
- [ ] CRUD with parameterized ADO commands
- [ ] Search/filter/detail pages
- [ ] Shared navigation and reusable logic
- [ ] Validation, output encoding, and safe sessions
- [ ] Transactional workflows
- [ ] Centralized diagnostic logging
- [ ] IIS deployment and dependency documentation
- [ ] Security audit and future-migration plan

## Setup notes
- This is a Classic ASP starter, not ASP.NET.
- Use a Windows test machine with IIS and the Classic ASP feature enabled.
- The `.txt` ASP source in this starter is downloadable through CodeLeaf; save/rename it to `.asp` in your local test site.
- Do not place secrets in source control. Any database or external-service settings must be configured securely for the local test environment.
- CodeLeaf does not execute Classic ASP in its browser playground.

## Verification
- Write expected results before running tests.
- Test missing/malformed values and a controlled dependency failure.
- Record IIS/Windows/provider versions and cleanup/rollback behavior.
