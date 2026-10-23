#!/usr/bin/env python3
"""MySQL-specific coverage and static example checks for CodeLeaf course content.
Run from backend/: python scripts/validate_mysql_course_examples.py
This validates structure and presence, not SQL-engine execution.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / "content" / "courses" / "mysql"
def read(path):
    return json.loads(path.read_text(encoding="utf-8"))
def main():
    doc = read(ROOT / "course.json")
    course = doc["course"]
    modules = []
    lessons = []
    failures = []
    visual_count = 0
    for module_rel in doc["module_files"]:
        mp = ROOT / module_rel
        md = read(mp); modules.append(md)
        if md.get("status") != "draft": failures.append(f"Module not draft: {mp}")
        for lesson_rel in md["lesson_files"]:
            lp = mp.parent / lesson_rel
            ld = read(lp); lessons.append(ld)
            if ld.get("source_syllabus_number") != len(lessons):
                failures.append(f"Source syllabus numbering is not contiguous at {lp}")
            blocks = ld.get("content", {}).get("content_blocks", [])
            diagram = next((b for b in blocks if b.get("type") == "diagram"), None)
            code = next((b for b in blocks if b.get("type") == "code"), None)
            if not diagram or not code:
                failures.append(f"Missing diagram/code block: {lp}")
            elif not (ROOT / "assets" / diagram.get("asset_path", "")).is_file():
                failures.append(f"Missing lesson visual: {lp}")
            elif not code.get("code") or not code.get("expected_output"):
                failures.append(f"Missing static code or expected output: {lp}")
            elif ld.get("content", {}).get("run_mode") != "static-validation":
                failures.append(f"Unsafe/unexpected run mode: {lp}")
            qref = ld.get("content", {}).get("knowledge_check_file")
            if not qref or not (ROOT / qref).is_file(): failures.append(f"Missing knowledge check: {lp}")
            elif len(read(ROOT / qref).get("questions", [])) < 3: failures.append(f"Too few questions: {qref}")
            if ld.get("status") != "draft": failures.append(f"Lesson not draft: {lp}")
            if not ld.get("sources"): failures.append(f"No sources: {lp}")
            for exp_rel in ld.get("exercise_files", []):
                ep = lp.parent / exp_rel
                if not ep.is_file(): failures.append(f"Missing exercise: {ep}")
                else:
                    ex = read(ep)
                    if not ex.get("solution_file"): failures.append(f"Exercise without protected solution ref: {ep}")
                    else:
                        solp=ep.parent/ex["solution_file"]
                        if not solp.is_file(): failures.append(f"Missing protected solution: {solp}")
                        elif read(solp).get("visibility") != "protected_content_repository_only": failures.append(f"Unprotected solution marker: {solp}")
    numbers = [l.get("source_syllabus_number") for l in lessons]
    if len(modules) != 37: failures.append(f"Expected 37 modules, found {len(modules)}")
    if len(lessons) != 435: failures.append(f"Expected 435 lessons, found {len(lessons)}")
    if numbers != list(range(1,436)): failures.append("Source topic numbers must be exactly 1..435")
    if course.get("lesson_count") != len(lessons): failures.append("course.lesson_count does not match linked lessons")
    for p in ROOT.rglob("*.json"):
        value=read(p)
        txt=json.dumps(value, ensure_ascii=False).lower()
        for forbidden in ('"xp_reward"','"xp_points"','"xp_override"','"lesson_xp"','"exercise_xp"'):
            if forbidden in txt: failures.append(f"Forbidden XP override key {forbidden} in {p}")
    manifest=read(ROOT/"assets/asset-manifest.json")
    for asset in manifest.get("assets",[]):
        ap=ROOT/asset["path"]
        if not ap.is_file(): failures.append(f"Manifest visual missing: {asset['path']}")
    visual_count=len(manifest.get("assets",[]))
    if visual_count != 472: failures.append(f"Expected 472 visual files in manifest, found {visual_count}")
    if failures:
        print("MySQL-specific checks FAILED:")
        for f in failures[:100]: print(" -",f)
        if len(failures)>100: print(f" - plus {len(failures)-100} more findings")
        raise SystemExit(1)
    print(json.dumps({"status":"passed","course_slug":"mysql","modules":len(modules),"lessons":len(lessons),"exercises":sum(len(x.get('exercise_files',[])) for x in lessons),"knowledge_check_sets":len(lessons),"visual_assets":visual_count,"project_files":len(doc.get('project_files',[])),"note":"Static structure/path/metadata validation only; SQL examples were not executed against a MySQL server."},indent=2))
if __name__ == "__main__": main()
