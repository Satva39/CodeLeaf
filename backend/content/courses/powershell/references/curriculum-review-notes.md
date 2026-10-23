# Curriculum source review — PowerShell (draft)

Reviewed source: `PowerShell.pdf`, 55 pages, Sections A–G. The PDF presents a 26-module curriculum and 286 numbered lessons. The full numbered title sequence and subtopic bullets have been retained in the lesson JSON files; practical exercises and the project roadmap have separate repository files.

## Source fidelity
- No numbered lesson from 1 through 286 was intentionally omitted. The 20 exercises in Section C are represented as individual exercise files. Section D's 12 projects plus the PowerShell Automation and Operations Toolkit capstone are represented as 13 individual project files.
- The PDF describes 80–140 hours; this package uses 110 hours as a planning midpoint, not a measured completion time.
- All generated course items are marked `draft`. Code examples are static references and have not been executed by a PowerShell runtime in this environment.

## Corrections and clarifications before publication
1. **PowerShell release baseline:** the PDF names PowerShell 7.6 LTS. Microsoft's lifecycle page was checked on 2026-10-20; it lists PowerShell 7.6 LTS support through 15 November 2028. Recheck release status as part of each course review.
2. **Execution policy:** describe it as a safety/consistency feature, not a security boundary. It is not a replacement for least privilege, trusted sources, code review, or application control.
3. **DSC generations:** clearly distinguish Windows PowerShell DSC 1.1 (legacy), the DSC 2.0 module generation, and standalone/cross-platform DSC 3.0; do not imply they share identical runtime and resource support.
4. **SSH remoting:** cover supported cross-platform scenarios but explain feature and endpoint differences from WinRM. Verify setup on the target OS rather than presenting transports as interchangeable.
5. **PowerShell workflows:** keep Windows PowerShell Workflow material in a legacy-maintenance context rather than recommending it for new modern PowerShell automation.
6. **Module/resource management:** distinguish PSResourceGet from older PowerShellGet/PackageManagement workflows. Microsoft's utility-module overview reviewed on 2026-10-20 flags SecretManagement and SecretStore retirement in June 2026; verify current service/support status and migration guidance before relying on legacy secret-management material.
7. **Static examples:** CodeLeaf's current non-browser course preview does not run PowerShell. Code blocks are `static-validation` and must not be presented as online execution results. Use local `pwsh`, Pester, PSScriptAnalyzer and human review.

## Not excluded
No numbered syllabus topic was excluded. Platform-dependent Windows, Active Directory, registry, service, remoting, identity/cloud and legacy features are explicitly constrained by prerequisites, permissions, module availability and OS/runtime notes. Enterprise sections use synthetic examples and review-oriented briefs; real tenant access is not needed for the core course.

## Technical references
See `reference-index.json` for source names, URLs, publisher, topics covered and the check date. These are external official sources and should be checked again immediately before publication.
