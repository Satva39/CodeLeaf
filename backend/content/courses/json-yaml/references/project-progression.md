# Project progression

Each project has a separate JSON file and repository-only reference-solution file. Rubrics are 100 points in aggregate and require human review. The reference files describe an approach and expected artifact types rather than claiming a runtime implementation has been executed.

| # | Project | Focus | Reference solution |
|---:|---|---|---|
| 1 | Student Records Dataset | Build a small, well-documented collection of student records in JSON and YAML. | `projects/solutions/001-student-records-dataset-reference-solution.json` |
| 2 | Personal Reading List | Create a reading-list data model with stable identifiers, statuses, dates, and validation fixtures. | `projects/solutions/002-personal-reading-list-reference-solution.json` |
| 3 | Application Settings File | Design readable YAML settings with explicit scalar types and environment-safe placeholders. | `projects/solutions/003-application-settings-file-reference-solution.json` |
| 4 | Product Catalog and Validation System | Create a JSON product collection and validate it with a reusable JSON Schema. | `projects/solutions/004-product-catalog-and-validation-system-reference-solution.json` |
| 5 | API Response Explorer | Inspect success, pagination, and error payloads and document a stable response contract. | `projects/solutions/005-api-response-explorer-reference-solution.json` |
| 6 | Configuration Converter | Convert a synthetic configuration between YAML and JSON and report round-trip differences. | `projects/solutions/006-configuration-converter-reference-solution.json` |
| 7 | API Contract Validation Toolkit | Create reusable schemas, positive/negative fixtures, and contract test instructions. | `projects/solutions/007-api-contract-validation-toolkit-reference-solution.json` |
| 8 | Multi-Environment Configuration Manager | Structure development/test/production settings without committing secret values. | `projects/solutions/008-multi-environment-configuration-manager-reference-solution.json` |
| 9 | Structured Data Quality Auditor | Inspect JSON/YAML fixtures for syntax, duplicate keys, type inconsistencies, and unsafe patterns. | `projects/solutions/009-structured-data-quality-auditor-reference-solution.json` |
| 10 | Versioned Event Data Processor | Process versioned synthetic events and explain streaming, compatibility, and data-quality policies. | `projects/solutions/010-versioned-event-data-processor-reference-solution.json` |
| 11 | JSON and YAML Configuration and Data Management Platform | Capstone: validate, compare, convert, and report structured data using a repeatable, security-aware workflow. | `projects/solutions/011-json-and-yaml-configuration-and-data-management-platform-reference-solution.json` |

## Progression rationale

1. **Projects 1–3:** practise core data modelling, repeated records, configuration, and scalar semantics.
2. **Projects 4–6:** combine schema constraints, API shapes, and round-trip conversion/interoperability.
3. **Projects 7–9:** introduce reusable validation contracts, multi-environment settings, and data-quality/security audits.
4. **Project 10:** apply versioned event modelling and stream-processing considerations.
5. **Project 11 — Capstone:** combine JSON/YAML input, parser selection, validation, comparison/conversion, reports, test fixtures, and security/compatibility documentation.

The exam blueprint in `exams/exam-blueprint.json` proposes a 90-minute assessment and a 75% suggested pass score. These are draft blueprint values, not platform-enforced attempts or a certificate issuance mechanism; the current importer does not persist the question pools or offer an exam submission flow, so these files are reference material until that integration is built and tested.
