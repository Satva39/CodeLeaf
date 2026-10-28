"""Focused contract tests for explicit exercise-solution reveal and path safety."""
from __future__ import annotations

import json
import tempfile
import unittest
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.main as main


class ExerciseSolutionEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "courses"
        self.course_root = self.root / "demo-course"
        self.module_root = self.course_root / "modules" / "demo-module"
        self.exercises_root = self.module_root / "exercises"
        self.solutions_root = self.module_root / "solutions"
        self.exercises_root.mkdir(parents=True)
        self.solutions_root.mkdir(parents=True)
        (self.exercises_root / "demo-exercise.json").write_text(json.dumps({
            "slug": "demo-exercise",
            "lesson_slug": "demo-lesson",
            "status": "draft",
            "solution_file": "../solutions/demo-solution.json",
        }), encoding="utf-8")
        (self.solutions_root / "demo-solution.json").write_text(json.dumps({
            "answer": "print('safe')",
            "explanation": "This is an explicitly requested worked solution.",
            "manual_validation_checklist": ["Check output."],
            "grading_config": {"correct_answer": "SECRET"},
            "reference_solution": "SHOULD NOT LEAK",
        }), encoding="utf-8")
        self.old_root = main.COURSE_CONTENT_ROOT
        main.COURSE_CONTENT_ROOT = self.root
        self.old_find = main.find_published_exercise
        main.find_published_exercise = lambda _db, _course, _lesson, _exercise: SimpleNamespace(
            slug="demo-exercise", title="Demo exercise", solution={}
        )
        main.app.dependency_overrides[main.get_db] = lambda: None
        self.client = TestClient(main.app)

    def tearDown(self) -> None:
        self.client.close()
        main.app.dependency_overrides.pop(main.get_db, None)
        main.COURSE_CONTENT_ROOT = self.old_root
        main.find_published_exercise = self.old_find
        self.temp.cleanup()

    def test_solution_is_revealed_only_through_explicit_endpoint_and_redacted(self) -> None:
        response = self.client.get("/api/courses/demo-course/lessons/demo-lesson/exercises/demo-exercise/solution")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["answer"], "print('safe')")
        self.assertEqual(payload["steps"], ["Check output."])
        serialized = json.dumps(payload)
        self.assertNotIn("grading_config", serialized)
        self.assertNotIn("correct_answer", serialized)
        self.assertNotIn("SHOULD NOT LEAK", serialized)

    def test_linked_reference_code_replaces_database_placeholder(self) -> None:
        (self.exercises_root / "demo-exercise.json").write_text(json.dumps({
            "slug": "demo-exercise",
            "lesson_slug": "demo-lesson",
            "solution_file": "../solutions/demo-solution.json",
        }), encoding="utf-8")
        (self.solutions_root / "demo-solution.json").write_text(json.dumps({
            "answer": "Implement the exercise and include the required evidence.",
            "example_code": "print('worked answer')",
            "explanation": "Run the example to verify the output.",
        }), encoding="utf-8")
        main.find_published_exercise = lambda _db, _course, _lesson, _exercise: SimpleNamespace(
            slug="demo-exercise", title="Demo exercise", solution={
                "explanation": "The protected reference solution is stored in a file; it is not exposed in learner-facing responses."
            }
        )
        response = self.client.get("/api/courses/demo-course/lessons/demo-lesson/exercises/demo-exercise/solution")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["answer"], "print('worked answer')")
        self.assertNotIn("protected reference solution is stored", response.json()["explanation"].lower())

    def test_inline_manifest_solution_returns_complete_answer_code(self) -> None:
        exercise_path = self.exercises_root / "demo-exercise.json"
        exercise_path.write_text(json.dumps({
            "slug": "demo-exercise",
            "lesson_slug": "demo-lesson",
            "solution": {
                "answer": "<!doctype html>\n<html lang=\"en\">\n<body><h1>About Me</h1><p>Hello.</p><p>I enjoy <em>learning</em>.</p></body>\n</html>",
                "explanation": "A complete worked HTML example.",
                "expected_result": "A document with a heading, paragraphs, and semantic emphasis.",
            },
        }), encoding="utf-8")
        main.find_published_exercise = lambda _db, _course, _lesson, _exercise: SimpleNamespace(
            slug="demo-exercise", title="Demo exercise", solution={
                "answer": None,
                "explanation": "Reference approach: Use an h1 and paragraphs; this is guidance, not the full code.",
            }
        )
        response = self.client.get("/api/courses/demo-course/lessons/demo-lesson/exercises/demo-exercise/solution")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertIn("<h1>About Me</h1>", payload["answer"])
        self.assertIn("<em>learning</em>", payload["answer"])
        self.assertEqual(payload["expected_result"], "A document with a heading, paragraphs, and semantic emphasis.")

    def test_course_level_solution_tree_is_supported(self) -> None:
        course_solutions = self.course_root / "solutions" / "exercises"
        course_solutions.mkdir(parents=True)
        (course_solutions / "demo-solution.json").write_text(json.dumps({
            "answer": "int main(void) { return 0; }",
            "explanation": "Course-level solution tree is supported.",
        }), encoding="utf-8")
        exercise_path = self.exercises_root / "demo-exercise.json"
        exercise_path.write_text(json.dumps({
            "slug": "demo-exercise",
            "lesson_slug": "demo-lesson",
            "solution_file": "../../../solutions/exercises/demo-solution.json",
        }), encoding="utf-8")
        response = self.client.get("/api/courses/demo-course/lessons/demo-lesson/exercises/demo-exercise/solution")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("Course-level solution tree", response.json()["explanation"])

    def test_manifest_path_cannot_escape_course_solution_roots(self) -> None:
        exercise_path = self.exercises_root / "demo-exercise.json"
        exercise_path.write_text(json.dumps({
            "slug": "demo-exercise",
            "lesson_slug": "demo-lesson",
            "solution_file": "../../../../../outside.json",
        }), encoding="utf-8")
        response = self.client.get("/api/courses/demo-course/lessons/demo-lesson/exercises/demo-exercise/solution")
        self.assertEqual(response.status_code, 404, response.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
