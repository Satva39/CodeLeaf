# Student Performance Explorer

**Status:** Draft starter brief.

## Scenario
Explore attendance, study time, and academic outcomes in synthetic data.

## Suggested files
- `data/raw/` — synthetic or explicitly licensed source files
- `notebooks/` — exploratory analysis and rationale
- `src/` — reusable cleaning/modeling logic
- `tests/` — assertions and quality checks
- `reports/` — generated visualizations and final report

## Milestones
1. Define the question, unit of analysis, target user, and success metric.
2. Record dataset provenance, permissions, fields, missingness, and any privacy risk.
3. Build a small, repeatable baseline before adding complexity.
4. Evaluate on data not used to fit choices; use time/group-aware splitting when appropriate.
5. Document findings, uncertainty, failures, operational constraints, and the next experiment.

## Acceptance criteria
- Missing-data handling
- Descriptive statistics
- Distribution plots
- Group comparisons
- Limitations discussion
- Include setup instructions and record relevant software/data versions.
- Do not commit credentials, personal data, unlicensed datasets, or trained artifacts containing sensitive information.
