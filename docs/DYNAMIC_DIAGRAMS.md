# CodeLeaf native dynamic diagrams

All existing course diagram SVG assets now have companion `*.diagram.json` structured models. LessonPage replaces the `.svg` suffix with `.diagram.json`, fetches the model from the safe course asset endpoint, then renders the diagram as React/HTML cards and connections. The lesson page does not use `<img>` or `<object>` to show diagrams. Existing SVG files remain in the repository as source material/backward-compatible assets; they are not the active lesson renderer.

## Model structure

- `title` / `description`: visual heading and explanation.
- `layout.kind`, `columns`, `rows`: per-diagram layout inferred from source geometry.
- `nodes`: each individually positioned card with its own ordered label text and role (badge/title/detail).
- `edges`: links detected from source connector geometry. Single-row step flows may infer adjacent sequence edges if source files omit explicit connectors.
- `header_labels` / `annotations`: all visible SVG text not attached to a node.
- `source_text`: original visible text strings for audit. Every original visible text index is mapped to a node, header, annotation, or the same metadata title/description, so conversion does not silently drop labels.
- `source_view_box`: source geometry dimensions.

## Rebuild / audit

The current patch includes pre-generated models for all 9,994 course diagram SVGs. When adding future lessons, author `*.diagram.json` directly and do not create static SVG diagrams. Legacy assets can be converted with the maintenance converter in a developer workspace; inspect edge relationships and long labels before publication. Do not expose arbitrary JSON through the asset endpoint—only `.diagram.json` files are permitted.

## Validation report

The patch-level converter checks that every source text item index is accounted for by a node or annotation and stores all source text in each model for auditing. This is a structural conversion; no automated parser can always infer semantic grouping perfectly from arbitrary SVGs. Review high-complexity diagrams or those flagged by `backend/scripts/validate_dynamic_diagrams.py` before publication. The front end displays all converted text and detected relationships from the structured model rather than displaying the original image.
