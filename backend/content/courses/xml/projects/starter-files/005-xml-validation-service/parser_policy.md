# Parser policy checklist
- Cap request size before parsing.
- Disable DTD and external entity processing unless a documented reviewed requirement demands otherwise.
- Independently restrict schema and stylesheet imports/resolution.
- Do not allow arbitrary file or network access.
- Apply timeouts, nesting/entity limits, and useful non-sensitive error messages.
- Fail closed if required security controls cannot be applied.
