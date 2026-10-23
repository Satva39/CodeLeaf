# Experiment Analysis Report

**Status:** Draft starter brief.

## Scenario
Assess a hypothetical product change using experiment design and uncertainty.

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
- Outcome definition
- Randomized design
- Confidence intervals
- Hypothesis testing
- Recommendation
- Include setup instructions and record relevant software/data versions.
- Do not commit credentials, personal data, unlicensed datasets, or trained artifacts containing sensitive information.
