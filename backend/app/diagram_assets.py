"""Shared, path-safe contract for CodeLeaf native dynamic diagram assets.

Manifest `asset_path` values are relative to a course's `assets/` directory.
Legacy logical paths ending in `.svg` resolve to the paired `.diagram.json` model;
the physical SVG is not required for a dynamic diagram. This module is used by
manifest validation, publishing preflight, course-content validation, and the API.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

DIAGRAM_MODEL_SUFFIX = ".diagram.json"
DIAGRAMS_DIRECTORY = "diagrams"
DIAGRAM_RENDERER = "codeleaf-native-dynamic-diagram"
_ALLOWED_MODEL_KEYS = {
    "renderer", "schema_version", "title", "description", "layout", "nodes", "edges",
    "source_text", "source_text_count", "text_mapping_complete", "metadata_text_indices",
    "header_labels", "annotations", "source_asset", "source_view_box",
}
_ALLOWED_NODE_KEYS = {"id", "order", "row", "column", "box", "title", "sourceTextIndices", "labels", "description", "explanation", "code", "example"}
_ALLOWED_EDGE_KEYS = {"id", "from", "to", "direction", "kind", "label"}
_ALLOWED_TEXT_LABEL_KEYS = {"source_index", "text", "role", "x", "y"}
_ALLOWED_LAYOUT_KEYS = {"kind", "columns", "rows"}
_ALLOWED_BOX_KEYS = {"x", "y", "width", "height"}
_ALLOWED_SOURCE_TEXT_KEYS = {"index", "text"}


def resolve_dynamic_diagram(course_dir: Path, relative_asset: Any, label: str = "diagram") -> Path:
    """Return an existing native model for a safe legacy-SVG or direct-model path."""
    if not isinstance(relative_asset, str) or not relative_asset.strip():
        raise ValueError(f"{label}: expected a non-empty relative diagram path")

    value = relative_asset.strip()
    windows_path = PureWindowsPath(value)
    posix_path = PurePosixPath(value)
    raw_parts = value.split("/")
    if (
        "\x00" in value
        or "\\" in value
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or any(part in {"", ".", ".."} for part in raw_parts)
        or not posix_path.parts
        or posix_path.parts[0].lower() != DIAGRAMS_DIRECTORY
    ):
        raise ValueError(f"{label}: unsafe diagram asset path {relative_asset!r}")

    lowered = value.lower()
    if lowered.endswith(DIAGRAM_MODEL_SUFFIX):
        model_relative = posix_path
    elif lowered.endswith(".svg"):
        model_relative = posix_path.with_suffix(DIAGRAM_MODEL_SUFFIX)
    else:
        raise ValueError(
            f"{label}: expected a legacy .svg logical path or a .diagram.json model path"
        )

    assets_root = (Path(course_dir).resolve() / "assets").resolve()
    candidate = (assets_root.joinpath(*model_relative.parts)).resolve(strict=False)
    if assets_root not in candidate.parents:
        raise ValueError(f"{label}: diagram model escapes the course assets directory")
    try:
        candidate = candidate.resolve(strict=True)
    except (FileNotFoundError, RuntimeError, OSError) as exc:
        expected = model_relative.as_posix()
        raise ValueError(f"{label}: missing native diagram model; expected assets/{expected}") from exc
    if assets_root not in candidate.parents or not candidate.is_file():
        raise ValueError(f"{label}: missing or unsafe native diagram model {model_relative.as_posix()!r}")
    if not candidate.name.lower().endswith(DIAGRAM_MODEL_SUFFIX):
        raise ValueError(f"{label}: resolved file is not a .diagram.json model")
    return candidate


def validate_dynamic_diagram_model(model_path: Path, label: str = "diagram") -> dict[str, Any]:
    """Parse and validate a native diagram model, including complete source-text mapping."""
    path = Path(model_path)
    if not path.name.lower().endswith(DIAGRAM_MODEL_SUFFIX):
        raise ValueError(f"{label}: native diagram model must end in {DIAGRAM_MODEL_SUFFIX}")
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label}: malformed or unreadable native diagram JSON: {path}") from exc
    if not isinstance(model, dict):
        raise ValueError(f"{label}: native diagram JSON must be an object")
    if model.get("renderer") != DIAGRAM_RENDERER:
        raise ValueError(f"{label}: unsupported dynamic diagram renderer")
    if set(model) - _ALLOWED_MODEL_KEYS:
        raise ValueError(f"{label}: native diagram contains unsupported/protected fields")

    for text_field in ("title", "description"):
        if text_field in model and not isinstance(model[text_field], str):
            raise ValueError(f"{label}: {text_field} must be a string")
    schema_version = model.get("schema_version")
    if schema_version is not None and (isinstance(schema_version, bool) or not isinstance(schema_version, int)):
        raise ValueError(f"{label}: schema_version must be an integer")

    layout = model.get("layout")
    if (
        not isinstance(layout, dict)
        or set(layout) - _ALLOWED_LAYOUT_KEYS
        or not isinstance(layout.get("kind"), str)
        or any(
            key in layout and (isinstance(layout[key], bool) or not isinstance(layout[key], int))
            for key in ("columns", "rows")
        )
    ):
        raise ValueError(f"{label}: diagram layout is invalid or contains unsupported fields")
    source_asset = model.get("source_asset")
    if source_asset is not None and not isinstance(source_asset, str):
        raise ValueError(f"{label}: source_asset must be a string")
    source_view_box = model.get("source_view_box")
    if source_view_box is not None and (
        not isinstance(source_view_box, list)
        or len(source_view_box) != 4
        or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in source_view_box)
    ):
        raise ValueError(f"{label}: source_view_box must be a four-number array")

    nodes = model.get("nodes")
    edges = model.get("edges", [])
    source_text = model.get("source_text")
    if not isinstance(nodes, list) or not nodes:
        raise ValueError(f"{label}: nodes must be a non-empty array")
    if not isinstance(edges, list):
        raise ValueError(f"{label}: edges must be an array")
    if not isinstance(source_text, list) or model.get("text_mapping_complete") is not True:
        raise ValueError(f"{label}: original diagram text mapping is incomplete")

    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError(f"{label}: every node must be an object")
        if set(node) - _ALLOWED_NODE_KEYS:
            raise ValueError(f"{label}: diagram node contains unsupported fields")
        box = node.get("box")
        if box is not None and (
            not isinstance(box, dict)
            or set(box) - _ALLOWED_BOX_KEYS
            or any(
                key in box and (isinstance(box[key], bool) or not isinstance(box[key], (int, float)))
                for key in _ALLOWED_BOX_KEYS
            )
        ):
            raise ValueError(f"{label}: diagram node box is invalid or contains unsupported fields")
        if "title" in node and not isinstance(node["title"], str):
            raise ValueError(f"{label}: diagram node title must be a string")
        for text_key in ("description", "explanation", "code", "example"):
            if text_key in node and (not isinstance(node[text_key], str) or len(node[text_key]) > 8000):
                raise ValueError(f"{label}: diagram node {text_key} must be a string of at most 8000 characters")
        for key in ("order", "row", "column"):
            if key in node and (isinstance(node[key], bool) or not isinstance(node[key], int)):
                raise ValueError(f"{label}: diagram node {key} must be an integer")
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip() or node_id in node_ids:
            raise ValueError(f"{label}: node IDs are missing, invalid, or duplicated")
        node_ids.add(node_id)

    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError(f"{label}: every edge must be an object")
        if set(edge) - _ALLOWED_EDGE_KEYS:
            raise ValueError(f"{label}: diagram edge contains unsupported fields")
        if any(key in edge and not isinstance(edge[key], str) for key in ("id", "direction", "kind", "label")):
            raise ValueError(f"{label}: edge labels and metadata must be strings")
        if (
            not isinstance(edge.get("from"), str)
            or not isinstance(edge.get("to"), str)
            or edge.get("from") not in node_ids
            or edge.get("to") not in node_ids
        ):
            raise ValueError(f"{label}: edge references a missing node")

    source_indices: set[int] = set()
    for record in source_text:
        if not isinstance(record, dict):
            raise ValueError(f"{label}: every source_text entry must be an object")
        if set(record) - _ALLOWED_SOURCE_TEXT_KEYS:
            raise ValueError(f"{label}: source_text contains unsupported fields")
        index = record.get("index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index in source_indices:
            raise ValueError(f"{label}: source_text indices are missing, invalid, or duplicated")
        if not isinstance(record.get("text"), str):
            raise ValueError(f"{label}: source_text entries must preserve original text strings")
        source_indices.add(index)

    mapped_indices: set[int] = set()
    for node in nodes:
        indices = node.get("sourceTextIndices", [])
        if not isinstance(indices, list):
            raise ValueError(f"{label}: node sourceTextIndices must be an array")
        for index in indices:
            if isinstance(index, bool) or not isinstance(index, int):
                raise ValueError(f"{label}: node source-text mappings must use integer indices")
            mapped_indices.add(index)
        # Keep compatibility with model versions that map text through visible labels.
        labels = node.get("labels", [])
        if not isinstance(labels, list):
            raise ValueError(f"{label}: node labels must be an array")
        for label_item in labels:
            if not isinstance(label_item, dict):
                raise ValueError(f"{label}: node labels must contain objects")
            if set(label_item) - _ALLOWED_TEXT_LABEL_KEYS:
                raise ValueError(f"{label}: node label contains unsupported fields")
            if any(key in label_item and not isinstance(label_item[key], str) for key in ("text", "role")):
                raise ValueError(f"{label}: node label text and role must be strings")
            if any(
                key in label_item and (isinstance(label_item[key], bool) or not isinstance(label_item[key], (int, float)))
                for key in ("x", "y")
            ):
                raise ValueError(f"{label}: node label coordinates must be numbers")
            index = label_item.get("source_index")
            if index is not None:
                if isinstance(index, bool) or not isinstance(index, int):
                    raise ValueError(f"{label}: label source_index must be an integer")
                mapped_indices.add(index)

    for group_name in ("header_labels", "annotations"):
        group = model.get(group_name, [])
        if not isinstance(group, list):
            raise ValueError(f"{label}: {group_name} must be an array")
        for item in group:
            if not isinstance(item, dict):
                raise ValueError(f"{label}: {group_name} entries must be objects")
            if set(item) - _ALLOWED_TEXT_LABEL_KEYS:
                raise ValueError(f"{label}: {group_name} entry contains unsupported fields")
            if any(key in item and not isinstance(item[key], str) for key in ("text", "role")):
                raise ValueError(f"{label}: {group_name} text and role must be strings")
            if any(
                key in item and (isinstance(item[key], bool) or not isinstance(item[key], (int, float)))
                for key in ("x", "y")
            ):
                raise ValueError(f"{label}: {group_name} coordinates must be numbers")
            index = item.get("source_index")
            if index is not None:
                if isinstance(index, bool) or not isinstance(index, int):
                    raise ValueError(f"{label}: {group_name} source_index must be an integer")
                mapped_indices.add(index)

    metadata_indices = model.get("metadata_text_indices", [])
    if not isinstance(metadata_indices, list):
        raise ValueError(f"{label}: metadata_text_indices must be an array")
    for index in metadata_indices:
        if isinstance(index, bool) or not isinstance(index, int):
            raise ValueError(f"{label}: metadata text mappings must use integer indices")
        mapped_indices.add(index)

    if mapped_indices - source_indices:
        raise ValueError(f"{label}: diagram references source-text indices that do not exist")
    if source_indices - mapped_indices:
        raise ValueError(f"{label}: original source-text records are not fully mapped")
    declared_count = model.get("source_text_count")
    if declared_count is not None and (
        isinstance(declared_count, bool)
        or not isinstance(declared_count, int)
        or declared_count != len(source_indices)
    ):
        raise ValueError(f"{label}: source_text_count does not match source_text records")
    return model
