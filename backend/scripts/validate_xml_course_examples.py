"""Validate XML course examples and starter artifacts without a database connection.

Run from backend/: python scripts/validate_xml_course_examples.py
If lxml is installed, also compile starter XSDs, validate samples, validate the local DTD,
and execute safe sample XSLT transformations. Otherwise the standard library still verifies
XML well-formedness and the script reports which semantic checks were skipped.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

BACKEND = Path(__file__).resolve().parents[1]
COURSE = BACKEND / "content" / "courses" / "xml"

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")

def main() -> int:
    metadata = json.loads((COURSE / "course.json").read_text(encoding="utf-8"))
    course = metadata["course"]
    require(course["slug"] == "xml", "course slug is xml")
    lessons = []
    for module_rel in metadata["module_files"]:
        module_path = COURSE / module_rel
        module = json.loads(module_path.read_text(encoding="utf-8"))
        for lesson_rel in module["lesson_files"]:
            lesson = json.loads((module_path.parent / lesson_rel).read_text(encoding="utf-8"))
            lessons.append(lesson)
    require(len(lessons) == 176, "all 176 PDF lesson topics are linked")

    parsed_examples = 0
    for lesson in lessons:
        for block in lesson.get("content", {}).get("content_blocks", []):
            if block.get("type") == "code" and block.get("language") in {"xml", "xsd", "xslt", "svg"}:
                ET.fromstring(block["code"])
                parsed_examples += 1
    require(parsed_examples > 0, f"{parsed_examples} XML/XSD/XSLT/SVG teaching snippets are well-formed XML")

    xml_artifacts = []
    for path in (COURSE / "projects" / "starter-files").rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".xml", ".xsd", ".xsl", ".xslt"}:
            continue
        ET.parse(path)
        xml_artifacts.append(path)
    require(len(xml_artifacts) >= 10, f"{len(xml_artifacts)} XML/XSD/XSLT project starter files are well-formed")

    try:
        from lxml import etree
    except ImportError:
        print("SKIP lxml semantic checks (lxml is not installed); XML syntax checks passed.")
        return 0

    # Check the DTD-based catalog sample declared in project 2.
    dtd_path = COURSE / "projects/starter-files/002-product-catalog-xml/catalog.dtd"
    xml_path = COURSE / "projects/starter-files/002-product-catalog-xml/catalog.xml"
    with dtd_path.open("rb") as source:
        dtd = etree.DTD(source)
    dtd_doc = etree.parse(str(xml_path))
    require(dtd.validate(dtd_doc), "Product Catalog DTD accepts its sample XML")

    # Compile and validate schema/instance pairs.
    schema_pairs = [
        ("projects/starter-files/005-xml-validation-service/product.xsd", "projects/starter-files/005-xml-validation-service/sample.xml"),
        ("projects/starter-files/007-xml-enterprise-integration-pipeline/order.xsd", "projects/starter-files/007-xml-enterprise-integration-pipeline/order.xml"),
        ("projects/starter-files/009-xml-document-management-and-transformation-platform/catalog.xsd", "projects/starter-files/009-xml-document-management-and-transformation-platform/sample-catalog.xml"),
    ]
    for schema_rel, xml_rel in schema_pairs:
        schema_doc = etree.parse(str(COURSE / schema_rel))
        schema = etree.XMLSchema(schema_doc)
        instance = etree.parse(str(COURSE / xml_rel))
        require(schema.validate(instance), f"XSD validates sample: {Path(xml_rel).name}")

    xslt_pairs = [
        ("projects/starter-files/004-xml-to-html-catalog-generator/catalog.xsl", "projects/starter-files/004-xml-to-html-catalog-generator/catalog.xml", "Notebook"),
        ("projects/starter-files/009-xml-document-management-and-transformation-platform/catalog-to-html.xsl", "projects/starter-files/009-xml-document-management-and-transformation-platform/sample-catalog.xml", "Notebook"),
    ]
    for xslt_rel, xml_rel, expected in xslt_pairs:
        stylesheet = etree.XSLT(etree.parse(str(COURSE / xslt_rel)))
        result = str(stylesheet(etree.parse(str(COURSE / xml_rel))))
        require(expected in result, f"XSLT transformation includes {expected} from {Path(xml_rel).name}")

    print("XML course example validation completed.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, ET.ParseError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
