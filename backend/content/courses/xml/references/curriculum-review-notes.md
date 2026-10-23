# XML curriculum review notes

## Source inspection

- Source: `XML.pdf`, 38 pages. All pages were rendered at 60 DPI and visually reviewed in contact sheets (pages 1–10, 11–20, 21–30, and 31–38); the PDF text layer was also extracted and parsed. The page images contain a consistent dark-background curriculum layout, with the final pages containing exercise/project cards and the staged learning roadmap.
- Captured course overview: XML is a structured-data markup language, no prior programming is required, and the PDF estimates 35–60 hours for core content. This course uses a planning estimate of about 50 hours, with additional project/specialization time.
- Coverage: all 176 numbered lesson topics and their visible subtopics; all 18 practical exercises; eight named projects plus the capstone; advanced/specialized topics; recommended dependencies; and the quality checklist.

## Correction / normalization

- The PDF's page 11 labels Module 8 (DTD) above lessons 57–65 and its page 13 explicitly begins Module 9 (XML Schema Definition/XSD) at lesson 66. The contents are therefore split into a nine-lesson DTD module and a fourteen-lesson XSD module. The syllabus topics are preserved; only the confusing heading placement is normalized.
- The document recommends keeping XQuery, advanced XSLT, XML Signature, XPointer, XLink, and specialized publishing as optional extensions. They are covered but labeled optional/specialist within this course rather than forced as prerequisites for basic XML use.
- XML 1.0, XML Namespaces, XSD 1.1, XPath 3.1, XSLT 3.0 and XQuery 3.1 are treated as specification families. Processor/version support is called out rather than implied universal.

## Security and execution boundaries

- The existing CodeLeaf playground previews HTML/CSS/JavaScript; it is not an XML/XSD/XPath/XSLT/XQuery/Python/SQL runner. Those examples are labeled `static-validation`, `query-simulation`, or `server-runner` as appropriate.
- Defensive XML examples do not include a reusable XXE attack payload. They teach disabling unnecessary external-resource resolution, hardened parsers, separate stylesheet/schema resolvers, resource limits, and failing closed.
- All modules, lessons, exercises, projects, knowledge checks and exam pools are marked `draft`; they need technical review against chosen processors before publication.

## Official references checked on 2026-10-12

See `reference-index.json`. W3C XML/Namespaces/XSD/XPath/XSLT/XQuery/Infoset specifications, MDN browser XML API guides, and OWASP XML External Entity Prevention guidance were checked for exact source URLs and core technical framing.
