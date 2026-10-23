"""Validate the structured dynamic diagram models for all CodeLeaf courses."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "content" / "courses"

def main() -> int:
    models = list(ROOT.glob("*/assets/diagrams/**/*.diagram.json"))
    errors=[]; node_total=edge_total=text_total=0
    if not models:
        print(f"No dynamic diagram JSON found under {ROOT}")
        return 2
    for path in models:
        try: d=json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path}: invalid JSON ({exc})"); continue
        if d.get("renderer") != "codeleaf-native-dynamic-diagram": errors.append(f"{path}: unsupported renderer")
        nodes=d.get("nodes"); source_text=d.get("source_text"); edges=d.get("edges")
        if not isinstance(nodes,list) or not isinstance(source_text,list) or not isinstance(edges,list):
            errors.append(f"{path}: nodes/source_text/edges must be arrays"); continue
        ids={n.get("id") for n in nodes if isinstance(n,dict)}
        for i,node in enumerate(nodes):
            if not isinstance(node,dict) or not node.get("id") or not isinstance(node.get("labels"),list): errors.append(f"{path}: invalid node at index {i}")
        for edge in edges:
            if edge.get("from") not in ids or edge.get("to") not in ids: errors.append(f"{path}: edge points to missing node")
        mapped=set()
        for node in nodes:
            mapped.update(node.get("sourceTextIndices",[]))
        mapped.update(x.get("source_index") for x in d.get("header_labels",[]))
        mapped.update(x.get("source_index") for x in d.get("annotations",[]))
        mapped.update(d.get("metadata_text_indices",[]))
        source_indices={x.get("index") for x in source_text}
        missing=source_indices-mapped
        if missing: errors.append(f"{path}: source text indices are not mapped: {sorted(missing)[:8]}")
        # Every source visible text string must either be present in the rendered nodes, header/notes, or bound to metadata.
        display_values={n.get("title") for n in nodes}
        display_values.update(l.get("text") for n in nodes for l in n.get("labels",[]))
        display_values.update(x.get("text") for x in d.get("header_labels",[]))
        display_values.update(x.get("text") for x in d.get("annotations",[]))
        display_values.update([d.get("title"),d.get("description")])
        missing_text=[x for x in source_text if x.get("text") not in display_values]
        if missing_text: errors.append(f"{path}: {len(missing_text)} source text string(s) not represented")
        if d.get("text_mapping_complete") is not True: errors.append(f"{path}: text_mapping_complete is not true")
        node_total+=len(nodes); edge_total+=len(edges); text_total+=len(source_text)
    print(f"Validated {len(models)} models; {node_total} nodes; {edge_total} relationships; {text_total} visible text records.")
    if errors:
        print(f"FAILED: {len(errors)} problem(s)")
        for e in errors[:100]: print(e)
        return 1
    print("PASS: JSON, node references, edge references, and text coverage checks.")
    return 0
if __name__ == "__main__": raise SystemExit(main())
