"""Audit published CodeLeaf MCQ banks and practical assessment definitions without DB access.

Run from backend/: python scripts/audit_exam_readiness.py
Optional output path: python scripts/audit_exam_readiness.py --output ../docs/exam-readiness-report.json
"""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSES = ROOT / "content" / "courses"
SUPPORTED_GRADERS = {"exact_text", "contains_all", "json_equal"}


def normalized(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)


def refs_for(blueprint: dict) -> list[str]:
    refs = blueprint.get("question_files")
    if isinstance(refs, list) and refs:
        return refs
    refs = blueprint.get("source_question_pool_files")
    return refs if isinstance(refs, list) else []


def question_rows(data: dict) -> list:
    rows = data.get("questions")
    if isinstance(rows, list):
        return rows
    if isinstance(data.get("options"), list) and (data.get("prompt") or data.get("question")):
        return [data]
    return []


def answer_is_valid(options: list[str], key: object) -> bool:
    if not isinstance(key, str):
        return False
    if key in options:
        return True
    letter = key.strip().upper()
    return len(letter) == 1 and "A" <= letter <= "Z" and ord(letter) - ord("A") < len(options)


def audit_course(course_dir: Path) -> dict:
    manifest, manifest_error = load_json(course_dir / "course.json")
    blueprint, blueprint_error = load_json(course_dir / "exams" / "exam-blueprint.json")
    metadata = (manifest or {}).get("course", manifest or {})
    title = str(metadata.get("title") or course_dir.name) if isinstance(metadata, dict) else course_dir.name
    status = metadata.get("status", (manifest or {}).get("status")) if isinstance(metadata, dict) else "unknown"
    blueprint_status = (blueprint or {}).get("status") if isinstance(blueprint, dict) else None
    row = {
        "slug": course_dir.name, "title": title,
        "published": status == "published" and blueprint_status == "published",
        "manifest_status": status or "unknown", "blueprint_status": blueprint_status or "missing",
        "question_file_ref_count": 0, "valid_question_count": 0,
        "distinct_valid_question_ids": 0, "distinct_prompt_count": 0,
        "required_minimum": 80, "selectable_count": 0,
        "missing_or_malformed_refs": [], "missing_answer_keys": 0,
        "invalid_option_mappings": 0, "malformed_questions": 0,
        "duplicate_question_ids": [], "duplicate_prompt_count": 0,
        "mcq_ready": False, "practical_exam_status": "missing",
        "practical_exam_errors": [], "overall_exam_ready": False,
    }
    for name, err in (("manifest", manifest_error), ("blueprint", blueprint_error)):
        if err:
            row["missing_or_malformed_refs"].append(f"{name}: {err}")
    if not isinstance(blueprint, dict):
        return row

    refs = refs_for(blueprint)
    row["question_file_ref_count"] = len(refs)
    ids: list[str] = []
    prompts: list[str] = []
    seen_paths = set()
    for ref in refs:
        if not isinstance(ref, str) or not ref.strip() or "\\" in ref:
            row["missing_or_malformed_refs"].append(str(ref))
            continue
        relative = ref if ref.startswith("exams/") else f"exams/{ref}"
        path = (course_dir / relative).resolve()
        if course_dir.resolve() not in path.parents or not path.is_file():
            row["missing_or_malformed_refs"].append(ref)
            continue
        # Multiple references to the same bank file should not inflate selectable counts.
        if path in seen_paths:
            continue
        seen_paths.add(path)
        data, err = load_json(path)
        if err or not isinstance(data, dict):
            row["missing_or_malformed_refs"].append(f"{ref}: {err or 'expected an object'}")
            continue
        if data.get("status") != "published":
            continue
        questions = question_rows(data)
        if not questions:
            row["missing_or_malformed_refs"].append(f"{ref}: missing question rows")
            continue
        for question in questions:
            if not isinstance(question, dict):
                row["malformed_questions"] += 1
                continue
            qid = question.get("id")
            prompt = question.get("prompt") or question.get("question")
            options = question.get("options")
            if not isinstance(qid, str) or not qid.strip() or not isinstance(prompt, str) or not prompt.strip():
                row["malformed_questions"] += 1
                continue
            if not isinstance(options, list) or len(options) != 4 or not all(isinstance(o, str) and o.strip() for o in options) or len({o.strip() for o in options}) != len(options):
                row["invalid_option_mappings"] += 1
                continue
            key = question.get("answer_key")
            if key is None or (isinstance(key, str) and not key.strip()):
                row["missing_answer_keys"] += 1
                continue
            if not answer_is_valid(options, key):
                row["invalid_option_mappings"] += 1
                continue
            ids.append(qid.strip())
            prompts.append(normalized(prompt))

    id_counts = Counter(ids)
    prompt_counts = Counter(prompts)
    row["valid_question_count"] = len(ids)
    row["distinct_valid_question_ids"] = len(id_counts)
    row["duplicate_question_ids"] = sorted(k for k, v in id_counts.items() if v > 1)
    row["distinct_prompt_count"] = len(prompt_counts)
    row["duplicate_prompt_count"] = sum(v - 1 for v in prompt_counts.values() if v > 1)
    # A valid bank needs enough distinct concepts, unique IDs, unbroken refs, and no malformed IDs.
    row["selectable_count"] = min(80, row["distinct_prompt_count"])
    row["mcq_ready"] = (
        row["published"] and row["distinct_prompt_count"] >= 80
        and len(row["duplicate_question_ids"]) == 0
        and not row["missing_or_malformed_refs"]
        and row["missing_answer_keys"] == 0 and row["invalid_option_mappings"] == 0
        and row["malformed_questions"] == 0
    )

    practical_path = course_dir / "exams" / "practical-exam.json"
    if not practical_path.is_file():
        row["practical_exam_status"] = "missing"
        row["practical_exam_errors"].append("exams/practical-exam.json does not exist")
    else:
        practical, practical_error = load_json(practical_path)
        manifest_data = manifest if isinstance(manifest, dict) else {}
        course_block = manifest_data.get("course") if isinstance(manifest_data.get("course"), dict) else {}
        authored = manifest_data.get("assessment_files") or course_block.get("assessment_files") or []
        if not isinstance(authored, list) or "exams/practical-exam.json" not in authored:
            row["practical_exam_errors"].append("practical file is not listed in manifest assessment_files")
        if practical_error or not isinstance(practical, dict):
            row["practical_exam_errors"].append(practical_error or "expected JSON object")
        else:
            tasks = practical.get("tasks")
            if practical.get("status") != "published":
                row["practical_exam_errors"].append("status is not published")
            if not isinstance(tasks, list) or not tasks:
                row["practical_exam_errors"].append("no tasks defined")
            else:
                task_ids = set()
                for i, task in enumerate(tasks):
                    if not isinstance(task, dict):
                        row["practical_exam_errors"].append(f"task {i + 1} is not an object")
                        continue
                    tid = task.get("id")
                    if not isinstance(tid, str) or not tid.strip() or tid in task_ids:
                        row["practical_exam_errors"].append(f"task {i + 1} has missing/duplicate id")
                    task_ids.add(tid)
                    grader = task.get("grader")
                    if task.get("submission_type", "text") != "text" or not isinstance(grader, dict) or grader.get("type") not in SUPPORTED_GRADERS:
                        row["practical_exam_errors"].append(f"task {tid or i + 1} has no supported deterministic text grader")
                if practical.get("status") == "published" and not row["practical_exam_errors"]:
                    row["practical_exam_status"] = "ready"
                else:
                    row["practical_exam_status"] = "invalid"
    row["overall_exam_ready"] = row["mcq_ready"] and row["practical_exam_status"] == "ready"
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT.parent / "docs" / "exam-readiness-report.json")
    args = parser.parse_args()
    rows = [audit_course(p) for p in sorted(COURSES.iterdir()) if p.is_dir() and (p / "course.json").exists()]
    published = [r for r in rows if r["published"]]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "backend/content/courses; static audit, no database access",
        "minimum_mcq_questions": 80,
        "published_course_count": len(published),
        "mcq_ready_published_course_count": sum(r["mcq_ready"] for r in published),
        "mcq_blocked_published_course_count": sum(not r["mcq_ready"] for r in published),
        "practical_ready_published_course_count": sum(r["practical_exam_status"] == "ready" for r in published),
        "overall_exam_ready_published_course_count": sum(r["overall_exam_ready"] for r in published),
        "courses": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "courses"}, indent=2))
    for r in published:
        if not r["overall_exam_ready"]:
            print(f"BLOCKED {r['slug']}: mcq={r['distinct_prompt_count']}/80 ({'ready' if r['mcq_ready'] else 'incomplete'}), practical={r['practical_exam_status']}")

if __name__ == "__main__":
    main()
