"""Regression check that the published AI course can serve its required practical exam.

Run from backend/: python scripts/test_ai_practical_exam_readiness.py
This is a static content check; it does not write to a database or production service.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
COURSE_DIR = BACKEND / "content" / "courses" / "ai"
sys.path.insert(0, str(BACKEND / "scripts"))
from audit_exam_readiness import audit_course  # noqa: E402


def main() -> None:
    report = audit_course(COURSE_DIR)
    assert report["published"], "AI course or MCQ blueprint must remain published"
    assert report["mcq_ready"], f"AI MCQ bank is not ready: {report['missing_or_malformed_refs']}"
    assert report["practical_exam_status"] == "ready", report["practical_exam_errors"]
    assert report["overall_exam_ready"], "AI certification should be available once learner prerequisites are complete"

    manifest = json.loads((COURSE_DIR / "course.json").read_text(encoding="utf-8"))
    assert "exams/practical-exam.json" in manifest.get("assessment_files", []), (
        "The practical assessment must be registered in the published course manifest"
    )
    practical = json.loads((COURSE_DIR / "exams" / "practical-exam.json").read_text(encoding="utf-8"))
    assert practical.get("status") == "published"
    assert practical.get("difficulty") == "intermediate"
    assert practical.get("execution_mode") == "structured_text_validation"
    tasks = practical.get("tasks")
    assert isinstance(tasks, list) and len(tasks) >= 3
    assert len({task.get("id") for task in tasks}) == len(tasks)
    for task in tasks:
        grader = task.get("grader", {})
        assert task.get("submission_type", "text") == "text"
        assert grader.get("type") in {"exact_text", "contains_all", "json_equal"}
    # Verify the main numerical task against the supplied confusion matrix.
    tp, fp, fn, tn = 45, 15, 5, 35
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    expected = {
        "accuracy": round((tp + tn) / (tp + fp + fn + tn), 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(2 * precision * recall / (precision + recall), 4),
    }
    assert tasks[0]["grader"].get("expected") == expected, (
        f"Metrics grader mismatch: expected {expected}, got {tasks[0]['grader'].get('expected')}"
    )
    print("PASS AI course MCQ bank and published practical assessment are ready")
    print(f"PASS {len(tasks)} intermediate-level tasks with supported server-side graders")
    print("PASS classification metric answer key")


if __name__ == "__main__":
    main()
