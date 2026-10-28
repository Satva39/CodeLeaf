"""Static readiness and course-specific coverage check for all practical exams.

Run from backend/: python scripts/test_all_practical_exam_readiness.py
No database or production service is accessed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "scripts"))
from audit_exam_readiness import audit_course  # noqa: E402


def main() -> None:
    root = BACKEND / "content" / "courses"
    rows = []
    for course_dir in sorted(root.iterdir()):
        manifest_path = course_dir / "course.json"
        if not course_dir.is_dir() or not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        info = manifest.get("course", manifest)
        if info.get("status") != "published":
            continue
        report = audit_course(course_dir)
        practical_path = course_dir / "exams" / "practical-exam.json"
        assert practical_path.is_file(), f"{course_dir.name}: practical assessment is missing"
        assert "exams/practical-exam.json" in manifest.get("assessment_files", []), (
            f"{course_dir.name}: practical assessment is not in the course manifest"
        )
        practical = json.loads(practical_path.read_text(encoding="utf-8"))
        assert practical.get("status") == "published", f"{course_dir.name}: practical is not published"
        assert practical.get("difficulty") == "intermediate", f"{course_dir.name}: difficulty must be intermediate"
        assert practical.get("execution_mode") == "structured_text_validation", (
            f"{course_dir.name}: assessment execution mode must be explicitly declared"
        )
        tasks = practical.get("tasks")
        assert isinstance(tasks, list) and len(tasks) >= 4, f"{course_dir.name}: at least four tasks required"
        task_ids = [task.get("id") for task in tasks]
        assert all(isinstance(task_id, str) and task_id for task_id in task_ids), f"{course_dir.name}: task ID missing"
        assert len(task_ids) == len(set(task_ids)), f"{course_dir.name}: duplicate task IDs"
        for task in tasks:
            grader = task.get("grader") or {}
            assert task.get("submission_type") == "text", f"{course_dir.name}/{task.get('id')}: unsupported type"
            assert grader.get("type") in {"exact_text", "contains_all", "json_equal"}, (
                f"{course_dir.name}/{task.get('id')}: unsupported grader"
            )
            if grader.get("type") == "contains_all":
                required = grader.get("required_strings")
                assert isinstance(required, list) and required and all(isinstance(x, str) and x for x in required), (
                    f"{course_dir.name}/{task.get('id')}: invalid required strings"
                )
        assert report["practical_exam_status"] == "ready", (
            f"{course_dir.name}: runtime readiness audit failed: {report['practical_exam_errors']}"
        )
        rows.append({"slug": course_dir.name, "title": info.get("title", course_dir.name),
                     "mcq_ready": report["mcq_ready"], "mcq_distinct_prompts": report["distinct_prompt_count"],
                     "practical_status": report["practical_exam_status"], "task_count": len(tasks)})

    assert len(rows) == 62, f"Expected 62 published course tracks; got {len(rows)}"
    assert all(row["practical_status"] == "ready" for row in rows)
    mcq_ready = sum(1 for row in rows if row["mcq_ready"])
    print(f"PASS practical assessments are published and connected for all {len(rows)} course tracks")
    print(f"PASS {sum(row['task_count'] for row in rows)} course-specific text-validated practical tasks across {len(rows)} tracks")
    print(f"INFO MCQ readiness remains {mcq_ready}/{len(rows)}; {len(rows) - mcq_ready} tracks remain blocked by the separate 80-question MCQ rule")
    print("NOTE These practical tasks use deterministic text/artifact checks; learner code is not executed by the API.")


if __name__ == "__main__":
    main()
