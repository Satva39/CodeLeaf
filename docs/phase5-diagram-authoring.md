# CodeLeaf native dynamic diagram authoring guide

Native models live in `backend/content/courses/<course>/assets/diagrams/*.diagram.json`. The lesson may reference a legacy logical `.svg` path; the resolver maps this to the sibling `.diagram.json`, so the physical SVG is not required. Do not replace unique diagram data with a generic illustration.

## Required data contract

Use `renderer: "codeleaf-native-dynamic-diagram"`, integer `schema_version`, a `layout.kind`, at least one unique node ID, optional edges whose `from`/`to` values reference existing IDs, `source_text` records with stable unique integer indices, and `text_mapping_complete: true`. Every `source_text` index must be referenced by a node's `sourceTextIndices`, a label/annotation's `source_index`, or `metadata_text_indices`. Set `source_text_count` to the full number of source records where available. This ensures original instructional text remains recoverable even if a visual rendering cannot fit it.

Supported layout families include `flow`, `sequence`, `branching`, `architecture`, `concept-map`, `timeline`, `comparison`, `table`, `state`, and `algorithm-trace`. The renderer may use row/column hints to help preserve author order; labels and descriptions must come from the model, not generated defaults. Nodes may use `description`, `explanation`, `code`, or `example` as text-backed details to reveal on selection. Edges may include a `label` to reveal in the UI.

## Accessible interaction guidance

Keep labels short, place explanatory text in node details when available, and make relationships clear without relying on color or hover. Ensure row/column placement reflects the teaching sequence and test narrow/mobile widths. Interactions should be keyboard reachable, preserve focus visibility, and respect reduced-motion preferences. Connectors should use reserved gaps rather than draw through node text.

## Validation commands

From `backend/`:

```powershell
python scripts/test_phase5_diagrams.py
python scripts/test_dynamic_diagram_compatibility.py
python scripts/validate_dynamic_diagrams.py
```

The included `tests/fixtures/diagrams/` directory has branching, architecture, and multi-row-flow examples. Add fixtures when supporting a new renderer behavior, and assert malformed edges and incomplete text mapping fail validation.
