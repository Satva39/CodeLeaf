"""Offline unit tests for deterministic compressed course content bundles."""
from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.storage.course_content import (
    BUNDLE_SCHEMA_VERSION,
    build_course_bundle,
    decode_course_bundle,
    lesson_metadata_only,
)


class CourseBundleTests(unittest.TestCase):
    def setUp(self):
        self.lessons = {
            "lesson-1": {
                "id": "lesson-1",
                "_codeleaf_course_slug": "python",
                "title": "Intro",
                "content": {"sections": [{"heading": "Hello", "body": "Python"}]},
                "keywords": ["python"],
            },
            "lesson-2": {
                "id": "lesson-2",
                "_codeleaf_course_slug": "python",
                "title": "Variables",
                "content": {"sections": [{"heading": "Variables", "body": "Values"}]},
            },
        }

    def test_bundle_is_deterministic_and_round_trips(self):
        first = build_course_bundle("course-id", "python", self.lessons)
        second = build_course_bundle("course-id", "python", self.lessons)
        self.assertEqual(first, second)
        payload, raw_size, digest, key = first
        self.assertEqual(hashlib.sha256(payload).hexdigest(), digest)
        self.assertTrue(key.endswith(f"{digest}.json.gz"))
        self.assertGreater(raw_size, len(payload))
        decoded = decode_course_bundle(
            payload, expected_course_id="course-id", expected_checksum=digest
        )
        self.assertEqual(decoded["schema_version"], BUNDLE_SCHEMA_VERSION)
        self.assertEqual(decoded["lessons"], self.lessons)

    def test_checksum_mismatch_is_rejected(self):
        payload, _raw_size, _digest, _key = build_course_bundle("course-id", "python", self.lessons)
        with self.assertRaises(Exception):
            decode_course_bundle(payload, expected_checksum="0" * 64)

    def test_course_id_mismatch_is_rejected(self):
        payload, _raw_size, digest, _key = build_course_bundle("course-id", "python", self.lessons)
        with self.assertRaises(Exception):
            decode_course_bundle(payload, expected_course_id="other-course", expected_checksum=digest)

    def test_metadata_keeps_import_and_outline_fields(self):
        document = self.lessons["lesson-1"]
        metadata = lesson_metadata_only(document)
        self.assertNotIn("content", metadata)
        self.assertEqual(metadata["id"], "lesson-1")
        self.assertEqual(metadata["_codeleaf_course_slug"], "python")
        self.assertTrue(metadata["_lesson_content_externalized"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
