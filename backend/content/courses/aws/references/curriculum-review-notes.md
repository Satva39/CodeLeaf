# AWS curriculum review notes

## Source inspected

- Input: `AWS.pdf`, 57 pages. The document was rendered page-by-page and a contact sheet was inspected; the pages are primarily curriculum text/tables, with selected embedded UI and architecture imagery (including the capstone e-commerce architecture on PDF page 51). Extracted text was checked across the full 57-page PDF.
- Source sections represented: Overview; 24-module syllabus; 22 practical exercises; 10 projects including capstone; specialization paths; suggested progression/prerequisites; curriculum quality and maintenance checklist.
- Source truth for topics: the explicit numbered topics in Section B, not guesses from the cover summary.

## Coverage and discrepancy

- The PDF explicitly states in Section B that the course has 24 modules and 287 numbered lessons, and its final validation section again mentions 287 stable identifiers.
- However, the enumerated topic list itself is a consecutive sequence **1–285** and contains 285 named lessons. This package preserves every visible numbered topic from 1 to 285, including the source numbers as stable `aws-lesson-NNN` IDs, and does not invent lesson 286 or 287. Resolve this discrepancy by correcting the source PDF or providing the two missing lesson definitions before increasing the count.
- All 22 Section C practical exercise briefs and all 10 Section D projects (including the production-ready capstone) have a corresponding structured brief.
- All 24 module headings and their listed main lessons/subtopics are represented. Learning path and module prerequisite metadata follow Section F.

## Technical corrections and maintenance notes

1. **AWS Data Pipeline is legacy, not the default for new ingestion.** AWS announced closure of new-customer access effective July 25, 2024. The PDF's lesson 229 title is retained to preserve syllabus coverage, but this course frames it as a legacy-service/migration topic and recommends evaluating AWS Glue, AWS Step Functions or Amazon MWAA for new workflows. Reference: https://docs.aws.amazon.com/datapipeline/latest/DeveloperGuide/migration.html
2. **Amazon Quick terminology.** PDF lesson 234 says “Business Intelligence with Amazon Quick”. The current official docs describe Amazon Quick as the broader AI-powered workspace, including Amazon Quick Sight for dashboards/BI. The title is preserved as the syllabus says; the example clarifies the hierarchy and asks learners to re-check availability/edition details. Reference: https://docs.aws.amazon.com/quick/latest/userguide/
3. **Budget alerts are not a spending cap.** The source explicitly calls this out in lessons 19 and 219; the course preserves the warning. Always inspect actual costs and resource inventories.
4. **Prices, quotas, Regions and certification details change.** No static price table, availability guarantee, quota number, or certification pass guarantee is embedded. Verify exact workload values and current service docs before publication.
5. **Public/private subnet terminology is route-based.** A subnet is not public solely because of its name: routing and addressing plus security controls determine reachability. The module emphasizes end-to-end path validation.
6. **CodeLeaf runner limitation.** The existing playground is a browser preview for HTML/CSS/JavaScript. AWS CLI/API operations, SQL, Python SDK snippets, YAML/JSON and cloud deployments are marked as static/human-reviewed examples; this package does not introduce a cloud runner or execute arbitrary commands in FastAPI.
7. **Course publication status.** All new course files remain draft. A valid file/package is not a certification, security review, live deployment, billing test or proof that every service-specific example has been independently run in every Region.

## Official source verification

The reference index includes official AWS documentation for core account/IAM, CLI, VPC, EC2, S3, RDS encryption, Lambda roles/events/retries, CloudWatch, CloudTrail, CloudFormation drift, CDK, pricing, Bedrock knowledge bases/guardrails, Amazon Quick and migration from AWS Data Pipeline. Selected key concepts and the two identified product/legacy corrections were checked against current AWS documentation on 2026-10-11. The full 285-lesson set is **not** represented as having received an individual live service deployment/test or page-by-page audit of every linked service operation; a publication review is still required.
