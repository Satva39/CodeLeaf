"""Focused regression tests for the authenticated Playground format tools.

Run from backend/: python scripts/test_playground_tools.py
"""
from __future__ import annotations

import unittest
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth_security import require_user
from app.playground_tools import router, run_structured_tool
from app.onlinecompiler_client import compiler_for_language


class StructuredToolTests(unittest.TestCase):
    def test_xml_validation_format_and_xpath(self):
        source = (
            '<catalog><product sku="P-101"><name>Notebook</name>'
            '<price>4.50</price></product></catalog>'
        )
        result = run_structured_tool("xml", source, ".//product[@sku='P-101']")
        self.assertTrue(result["success"], result["stderr"])
        self.assertIn("XML validation: PASSED", result["stdout"])
        self.assertIn("Root element: <catalog>", result["stdout"])
        self.assertIn("Matches: 1", result["stdout"])
        self.assertIn("FORMATTED XML", result["stdout"])

    def test_xml_invalid_reports_location(self):
        result = run_structured_tool("xml", "<catalog>\n  <product>\n</catalog>")
        self.assertFalse(result["success"])
        self.assertIn("line", result["stderr"].lower())

    def test_xml_rejects_doctype_and_entities(self):
        result = run_structured_tool("xml", '<!DOCTYPE x [<!ENTITY test "bad">]><x>&test;</x>')
        self.assertFalse(result["success"])
        self.assertIn("disabled", result["stderr"].lower())

    def test_xml_rejects_unsupported_xpath(self):
        result = run_structured_tool("xml", "<root><item/></root>", "document('https://example.invalid')")
        self.assertFalse(result["success"])
        self.assertIn("XPath", result["stderr"])

    def test_json_valid_and_nonstandard_constants(self):
        valid = run_structured_tool("json", '{"name":"CodeLeaf","ready":true}')
        self.assertTrue(valid["success"])
        self.assertIn('"name": "CodeLeaf"', valid["stdout"])
        invalid = run_structured_tool("json", '{"value": NaN}')
        self.assertFalse(invalid["success"])
        self.assertIn("not valid standard JSON", invalid["stderr"])

    def test_yaml_safe_load_and_format(self):
        valid = run_structured_tool("yaml", "name: CodeLeaf\nitems:\n  - one\n  - two\n")
        self.assertTrue(valid["success"])
        self.assertIn("FORMATTED YAML", valid["stdout"])
        unsafe = run_structured_tool("yaml", "value: !!python/object/apply:os.system ['echo unsafe']")
        self.assertFalse(unsafe["success"])

    def test_csv_consistency_and_preview(self):
        valid = run_structured_tool("excel", "name,score\nA,10\nB,20\n")
        self.assertTrue(valid["success"])
        self.assertIn("TABLE PREVIEW", valid["stdout"])
        invalid = run_structured_tool("excel", "a,b\n1\n")
        self.assertFalse(invalid["success"])
        self.assertIn("inconsistent", invalid["stderr"])

    def test_dockerfile_is_static_lint_only(self):
        valid = run_structured_tool("docker", "FROM python:3.13\nWORKDIR /app\n")
        self.assertTrue(valid["success"])
        self.assertIn("does not build images", valid["stdout"])
        invalid = run_structured_tool("docker", "RUN echo missing-base")
        self.assertFalse(invalid["success"])
        self.assertIn("FROM", invalid["stderr"])

    def test_cloudformation_and_github_workflow_validation(self):
        aws = run_structured_tool("aws", "AWSTemplateFormatVersion: '2010-09-09'\nResources: {}\n")
        self.assertTrue(aws["success"])
        workflow = run_structured_tool(
            "githubactions",
            "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps: []\n",
        )
        self.assertTrue(workflow["success"], workflow["stderr"])
        invalid = run_structured_tool("githubactions", "name: CI\nsteps: []\n")
        self.assertFalse(invalid["success"])

    def test_toml_markdown_plain_and_size_limit(self):
        self.assertTrue(run_structured_tool("toml", '[app]\nname = "CodeLeaf"')["success"])
        self.assertFalse(run_structured_tool("toml", '[app\nname = "broken"')["success"])
        markdown = run_structured_tool("markdown", "# Intro\n\nText")
        self.assertTrue(markdown["success"])
        self.assertIn("1. Intro", markdown["stdout"])
        self.assertEqual(run_structured_tool("plain", "hello")["stdout"], "hello")
        too_large = run_structured_tool("json", " " + (" " * 65_536))
        self.assertFalse(too_large["success"])

    def test_authenticated_api_contract(self):
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[require_user] = lambda: {"id": "test-user"}
        client = TestClient(app)
        response = client.post(
            "/api/playground/tools/run",
            json={"language": "xml", "source": "<root><item/></root>", "query": ".//item"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()["result"]
        self.assertEqual(payload["provider"], "CodeLeaf Format Tools")
        self.assertTrue(payload["success"])
        self.assertIn("Matches: 1", payload["stdout"])
        self.assertNotIn("api_key", response.text.lower())

    def test_redis_command_simulator(self):
        source = (
            'SET greeting "Hello, CodeLeaf!"\n'
            'GET greeting\n'
            'INCR page:views\n'
            'HSET user:1 name Satva level beginner\n'
            'HGET user:1 name\n'
            'LPUSH queue first second\n'
            'LRANGE queue 0 -1\n'
            'SADD tags python xml\n'
            'SMEMBERS tags'
        )
        result = run_structured_tool("redis", source)
        self.assertTrue(result["success"], result["stderr"])
        self.assertEqual(result["provider"], "CodeLeaf Redis Simulator (ephemeral)")
        self.assertIn("Hello, CodeLeaf!", result["stdout"])
        self.assertIn('["second", "first"]', result["stdout"])
        self.assertIn('["python", "xml"]', result["stdout"])

    def test_redis_is_ephemeral_and_rejects_unsafe_or_unknown_commands(self):
        first = run_structured_tool("redis", 'SET transient value')
        second = run_structured_tool("redis", 'GET transient')
        self.assertTrue(first["success"])
        self.assertTrue(second["success"])
        self.assertIn("(nil)", second["stdout"])
        denied = run_structured_tool("redis", 'CONFIG GET *')
        self.assertFalse(denied["success"])
        self.assertIn("unsupported command", denied["stderr"].lower())

    def test_onlinecompiler_python_data_packages_are_routable(self):
        self.assertEqual(compiler_for_language("numpy"), "python-3.14")
        self.assertEqual(compiler_for_language("scipy"), "python-3.14")
        self.assertEqual(compiler_for_language("scikit-learn"), "python-3.14")
        self.assertEqual(compiler_for_language("pandas"), "python-3.14-pandas2")
        self.assertIsNone(compiler_for_language("pytorch"))
        self.assertIsNone(compiler_for_language("django"))

    def test_invalid_language_is_rejected(self):
        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[require_user] = lambda: {"id": "test-user"}
        response = TestClient(app).post(
            "/api/playground/tools/run",
            json={"language": "python", "source": "print(1)"},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
