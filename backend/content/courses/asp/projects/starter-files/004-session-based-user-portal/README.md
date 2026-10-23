# Session-Based User Portal

**Objective:** Create a basic authenticated portal that separates public and protected pages.

## Required features
- [ ] Login workflow
- [ ] Session state
- [ ] Logout
- [ ] Server-side authorization checks
- [ ] Profile page
- [ ] Safe error handling

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
