"""Run native Phase 5 diagram fixtures: python scripts/test_phase5_diagrams.py"""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
from app.diagram_assets import validate_dynamic_diagram_model

FIXTURES = BACKEND_ROOT / "tests" / "fixtures" / "diagrams"
EXPECTED = {"branching.diagram.json", "architecture.diagram.json", "multi-row-flow.diagram.json"}

def main() -> int:
    found = {path.name for path in FIXTURES.glob("*.diagram.json")}
    missing = EXPECTED - found
    if missing:
        raise AssertionError(f"Missing diagram fixtures: {sorted(missing)}")
    for name in sorted(EXPECTED):
        path = FIXTURES / name
        model = validate_dynamic_diagram_model(path, name)
        ids = {node["id"] for node in model["nodes"]}
        for edge in model.get("edges", []):
            assert edge["from"] in ids and edge["to"] in ids
        assert model.get("text_mapping_complete") is True
        source_indices = {row["index"] for row in model["source_text"]}
        mapped = set(model.get("metadata_text_indices", []))
        for node in model["nodes"]:
            mapped.update(node.get("sourceTextIndices", []))
            mapped.update(label["source_index"] for label in node.get("labels", []) if "source_index" in label)
        mapped.update(label["source_index"] for group in ("header_labels", "annotations") for label in model.get(group, []) if "source_index" in label)
        assert source_indices == mapped, f"Source-text coverage mismatch in {name}"
        assert any("row" in node for node in model["nodes"]), f"Missing explicit row layout in {name}"
        print(f"PASS {name}: {len(model['nodes'])} nodes, {len(model.get('edges', []))} edges, complete text mapping")
    # A malformed reference must fail closed.
    with tempfile.TemporaryDirectory() as temp:
        bad = json.loads((FIXTURES / "branching.diagram.json").read_text(encoding="utf-8"))
        bad["edges"][0]["to"] = "missing-node"
        path = Path(temp) / "bad.diagram.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        try:
            validate_dynamic_diagram_model(path, "negative edge test")
        except ValueError:
            print("PASS malformed edge is rejected")
        else:
            raise AssertionError("Malformed edge endpoint was accepted")
    print("All Phase 5 diagram fixture checks passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
