# XML Data Reporting System

## Objective
Extract information from multiple XML documents and produce a repeatable report.

## Suggested workflow
1. Inspect the included sample XML and identify its root, namespace, repeated records, and assumptions.
2. Define expected behavior and at least one invalid/edge case before running a processor.
3. Add validation/query/transformation checks appropriate to the project.
4. Keep untrusted resource resolution disabled unless a reviewed, allowlisted need exists.
5. Record the processor and version, test evidence, limitations, and a reset/cleanup plan.

## Submission
Submit source artifacts, sample input/output, schema/stylesheet where applicable, a test report, and a concise explanation of design choices.

## Safety and scope
All example data is synthetic. The CodeLeaf playground is not an XML/XSD/XPath/XSLT/XQuery runtime. Run specialist examples only in a compatible local processor. Do not process untrusted XML without hardened parser/resolver settings and resource limits.
