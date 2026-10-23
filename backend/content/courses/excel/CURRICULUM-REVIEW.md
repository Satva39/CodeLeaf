# Excel curriculum review and technical notes

**Source syllabus:** attached `Excel.pdf`, 53 pages, Sections A–G.
**Checked:** 2026-10-12
**Status:** Draft.

## Coverage preserved

The section-B parser identified **27 modules and 262 sequential numbered topics**. All numbered topics and listed subtopics were transferred into the corresponding lesson records. Section C’s 24 practical exercise titles and objectives are separate exercise files, with synthetic CSV input data and protected reference-answer files. Section D’s 12 project briefs, including the integrated capstone, are represented separately. Section E specializations, Section F stages and Section G review requirements are recorded in course metadata/references and project acceptance criteria.

## Technical notes and corrections/clarifications

1. **Function availability is version-dependent.** Modern dynamic-array functions are labeled as requiring availability checks. Microsoft currently documents `REGEXEXTRACT` for Microsoft 365 on Windows and Mac; it must not be assumed to exist in older perpetual versions.
2. **Power Query, Power Pivot, the Data Model and DAX remain separate related concepts.** The syllabus’s combined analysis workflow is retained, but each feature is described with edition/platform/license prerequisites. A Power Query transformation is not a DAX measure, and neither is a worksheet formula.
3. **VBA, Office Scripts/Power Automate and Office Add-ins are separate automation paths.** They are not mandatory prerequisites for one another. VBA macros do not run in Excel for the web; Office Scripts require a supported Microsoft 365 environment/tenant. Office Add-ins use the Office JavaScript API.
4. **CSV is a flat-text exchange format, not a full workbook replacement.** Format, formulas, styling, sheets and other workbook objects may not survive CSV export; leading zeros, encoding, delimiter and dates need explicit validation.
5. **Worksheet/workbook protection is not a complete security boundary.** It prevents some accidental changes but does not replace access control or secure storage. This clarifies workbook security topics without removing them.
6. **The PDF does not prescribe threshold values for sample business policies.** The commission practice uses explicitly labeled illustrative thresholds (5%, 7%, 10%) only so learners can test below/at/above boundaries; replace them with the policy required by the task. The PDF’s listed subject coverage remains unchanged.
7. **Office Scripts use Microsoft’s documented Excel Script API.** The example is stored as lesson content only; no `.ts`/`.tsx` project source was introduced, in keeping with the CodeLeaf frontend constraint.
8. **No PDF topic was excluded.** The minor wordings and technical notes above are compatibility/quality clarifications, not syllabus removal.

## Execution limitations

No desktop Excel engine is bundled with this course generator, so workbook formulas/macros/scripts were not executed in Excel. SVG/XML, JSON/file relationships, course contract, text grader configuration and import dry-run can be checked locally; final worksheet rendering and the human-reviewed workbook projects still need a compatible Excel installation and editorial review.
