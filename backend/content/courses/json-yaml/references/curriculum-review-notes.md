# Curriculum review notes — JSON and YAML

## Source coverage

The 55-page PDF was inspected via text extraction and rendered page contact sheets. Section B contributes all 168 numbered lesson topics across 16 modules; Section C contributes 32 practical exercises; Section D contributes 10 projects plus the capstone. All lesson numbers are preserved in `source_syllabus_number`, and the lesson title/subtopic records were generated from those source ranges. The course contains no publication claims: every new item is `draft`.

## Technical clarifications made explicit

1. The PDF uses “six JSON value categories” as a useful taxonomy. In JSON's value model, strings, numbers, booleans, and null are primitive values; objects and arrays are structured values.
2. JSONPath's standard specification is RFC 9535. JSON Patch (RFC 6902) and JSON Merge Patch (RFC 7396) are different formats. In Merge Patch, a `null` value in an object patch removes the target member, so callers must account for that behavior.
3. JSON Lines / NDJSON conventionally places one JSON value on each line. RFC 7464 JSON text sequences instead use record-separator framing and are not the same protocol.
4. YAML 1.2.2 is a revision with clarifications/errata against YAML 1.2; it should not be described as an entirely new type system. Actual scalar resolution still depends on the parser/schema used. Quote ambiguous strings and test the target tool.
5. YAML's `<<` merge-key convention is supported by popular implementations but is not a portable core YAML 1.2.2 feature. Where compatibility matters, use explicit values or confirm the target parser's documented extension.
6. Safe parsing and schema/business-rule validation are separate steps. A safe loader mitigates unsafe object construction but does not by itself bound input size, validate the application contract, prevent resource exhaustion, or redact secrets.
7. JSON has no comment syntax and no dedicated date/time type. Conversion through a data model can preserve values while losing comments or original presentation. Document string/date/null conventions in a contract.
8. JSON Schema examples declare the 2020-12 dialect where relevant. A validator's dialect/format support should be configured and tested explicitly.
9. The repository's existing exercise grader supports only `choice`, `exact_text`, and `contains_all`. Practical exercises therefore use `contains_all` only as a transparent smoke check; complete technical work needs human review and tool-based evidence.

## Content completeness / publication gate

All 168 topics have a separate lesson file, each with three knowledge-check questions, a real SVG visual, an inspectable example, run instructions, expected output, troubleshooting guidance, a task, hints, recap, and official source links. Thirty-two exercise files and eleven projects include separate repository-only solution files. Content and assessments remain draft pending expert review.
