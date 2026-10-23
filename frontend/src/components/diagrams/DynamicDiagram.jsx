import { apiFetch } from "../../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  GitBranch,
  LoaderCircle,
  Sparkles,
} from "lucide-react";
import { API_BASE } from "../../lib/demoState.js";
import { recordAnalyticsEvent } from "../../lib/analytics.js";

function encodePath(path) {
  return String(path || "")
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

function toDynamicAssetPath(assetPath) {
  const path = String(assetPath || "").trim();
  if (!path) return "";
  if (/\.diagram\.json$/i.test(path)) return path;
  return path.replace(/\.svg$/i, ".diagram.json");
}

function CardLabel({ label }) {
  if (!label?.text) return null;
  if (label.role === "badge") return null;
  if (label.role === "title") {
    return <h3 className="dynamic-diagram-node-title">{label.text}</h3>;
  }
  return <p className="dynamic-diagram-node-detail">{label.text}</p>;
}

function DiagramNode({
  node,
  index,
  edges,
  nodesById,
  layout,
  linearFlow = false,
  onSelect,
  selected = false,
  stepActive = false,
  showEdgeLabels = false,
}) {
  const outgoing = edges.filter((edge) => edge.from === node.id);
  const badgeText = node.labels?.find((label) => label.role === "badge")?.text;
  const adjacentDirections = new Set();
  for (const edge of outgoing) {
    const target = nodesById.get(edge.to);
    if (!target) continue;
    if (
      target.renderRow === node.renderRow &&
      target.renderColumn === node.renderColumn + 1
    )
      adjacentDirections.add("right");
    if (
      target.renderRow === node.renderRow &&
      target.renderColumn === node.renderColumn - 1
    )
      adjacentDirections.add("left");
    if (
      target.renderColumn === node.renderColumn &&
      target.renderRow === node.renderRow + 1
    )
      adjacentDirections.add("down");
  }
  const directions = new Set(
    outgoing.map((edge) => {
      const target = nodesById.get(edge.to);
      if (!target) return edge.direction || "branch";
      if (
        target.renderRow === node.renderRow &&
        target.renderColumn === node.renderColumn + 1
      )
        return "right";
      if (
        target.renderRow === node.renderRow &&
        target.renderColumn === node.renderColumn - 1
      )
        return "left";
      if (
        target.renderColumn === node.renderColumn &&
        target.renderRow === node.renderRow + 1
      )
        return "down";
      return edge.direction || "branch";
    }),
  );
  return (
    <article
      className={`dynamic-diagram-node dynamic-diagram-tone-${index % 4}${selected ? " is-selected" : ""}${stepActive ? " is-active-step" : ""}`}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      aria-label={`Select ${node.title || `Concept ${index + 1}`} for details`}
      onClick={() => onSelect?.(node.id)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect?.(node.id);
        }
      }}
    >
      <div className="dynamic-diagram-node-topline">
        <span className="dynamic-diagram-step-label">
          {badgeText || `CONCEPT ${String(index + 1).padStart(2, "0")}`}
        </span>
        <span className="dynamic-diagram-node-icon" aria-hidden="true">
          {directions.has("down") ? (
            <ArrowDown size={18} />
          ) : directions.has("branch") ? (
            <GitBranch size={18} />
          ) : (
            <Sparkles size={17} />
          )}
        </span>
      </div>
      <div className="dynamic-diagram-node-content">
        {node.labels?.map((label) => (
          <CardLabel
            key={`${node.id}-source-${label.source_index ?? label.text ?? "label"}`}
            label={label}
          />
        ))}
      </div>
      {outgoing.length > 0 && (
        <div
          className="dynamic-diagram-node-links"
          aria-label="Outgoing connections"
        >
          {outgoing.map((edge) => {
            const target = nodesById.get(edge.to);
            if (!target) return null;
            return (
              <span
                key={`${edge.from}-${edge.to}`}
                className="dynamic-diagram-link-chip"
              >
                <ArrowRight size={12} aria-hidden="true" /> {target.title}
                {showEdgeLabels && edge.label && (
                  <small className="dynamic-diagram-edge-label">
                    {edge.label}
                  </small>
                )}
              </span>
            );
          })}
        </div>
      )}
      {adjacentDirections.has("right") && (
        <span
          className="dynamic-diagram-connector dynamic-diagram-connector-right"
          aria-hidden="true"
        >
          <ArrowRight size={17} />
        </span>
      )}
      {adjacentDirections.has("left") && (
        <span
          className="dynamic-diagram-connector dynamic-diagram-connector-left"
          aria-hidden="true"
        >
          <ArrowLeft size={17} />
        </span>
      )}
      {adjacentDirections.has("down") && (
        <span
          className="dynamic-diagram-connector dynamic-diagram-connector-down"
          aria-hidden="true"
        >
          <ArrowDown size={17} />
        </span>
      )}
      {linearFlow && outgoing.length > 0 && (
        <span
          className="dynamic-diagram-connector dynamic-diagram-connector-mobile"
          aria-hidden="true"
        >
          <ArrowDown size={16} />
        </span>
      )}
    </article>
  );
}

export default function DynamicDiagram({
  courseSlug,
  assetPath,
  title = "Visual explanation",
  description = "Explore the concepts and how they relate.",
  caption = "",
  alt = "",
}) {
  const [model, setModel] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(Boolean(assetPath));
  const [selectedNodeId, setSelectedNodeId] = useState("");
  const [showEdgeLabels, setShowEdgeLabels] = useState(false);
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const dataPath = useMemo(() => toDynamicAssetPath(assetPath), [assetPath]);
  const requestUrl = useMemo(() => {
    if (!courseSlug || !dataPath) return "";
    return `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/assets/${encodePath(dataPath)}`;
  }, [courseSlug, dataPath]);

  useEffect(() => {
    setSelectedNodeId("");
    setShowEdgeLabels(false);
    setActiveStepIndex(0);
    if (!requestUrl) {
      setLoading(false);
      setModel(null);
      setLoadError(
        "No dynamic diagram data file is associated with this lesson yet.",
      );
      return undefined;
    }
    const controller = new AbortController();
    setLoading(true);
    setLoadError("");
    apiFetch(requestUrl, { credentials: "include", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok)
          throw new Error(`Diagram data request failed (${response.status}).`);
        const data = await response.json();
        if (
          data?.renderer !== "codeleaf-native-dynamic-diagram" ||
          !Array.isArray(data.nodes)
        ) {
          throw new Error(
            "The diagram file does not use the supported dynamic model format.",
          );
        }
        setModel(data);
      })
      .catch((error) => {
        if (error.name !== "AbortError") {
          setModel(null);
          void recordAnalyticsEvent({
            event_type: "broken_asset",
            course_slug: courseSlug,
            item_key: dataPath.split("/").pop(),
            outcome: "missing",
          });
          setLoadError(
            error.message || "The dynamic diagram could not be loaded.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [requestUrl]);

  if (loading) {
    return (
      <div className="dynamic-diagram-state" role="status">
        <LoaderCircle className="dynamic-diagram-spinner" size={19} /> Loading
        the lesson diagram…
      </div>
    );
  }
  if (!model) {
    return (
      <div
        className="dynamic-diagram-state dynamic-diagram-state-error"
        role="status"
      >
        <strong>Diagram unavailable</strong>
        <span>
          {loadError ||
            "The structured diagram has not been generated for this asset."}
        </span>
      </div>
    );
  }

  const sourceNodes = [...model.nodes].sort(
    (a, b) =>
      (a.row ?? 0) - (b.row ?? 0) ||
      (a.column ?? 0) - (b.column ?? 0) ||
      (a.order ?? 0) - (b.order ?? 0),
  );
  const edges = model.edges || [];
  const sourceIndexById = new Map(
    sourceNodes.map((node, index) => [node.id, index]),
  );
  // Simple linear flows use a serpentine path: across the first row, down at
  // the edge, then back across the next row. Branched/architectural diagrams
  // retain their own node coordinates and relationships.
  const linearFlow =
    model.layout?.kind === "flow" &&
    sourceNodes.length >= 3 &&
    sourceNodes.length <= 8 &&
    edges.length === sourceNodes.length - 1 &&
    edges.every((edge) => {
      const fromIndex = sourceIndexById.get(edge.from);
      const toIndex = sourceIndexById.get(edge.to);
      return Number.isInteger(fromIndex) && toIndex === fromIndex + 1;
    });
  const sourceColumnCount = Math.max(
    1,
    ...sourceNodes.map((node) =>
      Number.isInteger(node.column) && node.column >= 0 ? node.column + 1 : 0,
    ),
  );
  // Linear flows get two roomy columns in a serpentine sequence. Other large
  // diagrams reflow into up to four columns, preserving each source node/edge.
  const columnCount = linearFlow ? 2 : Math.min(sourceColumnCount, 4);
  const hasCompleteCoordinates = sourceNodes.every(
    (node) =>
      Number.isInteger(node.row) &&
      node.row >= 0 &&
      Number.isInteger(node.column) &&
      node.column >= 0,
  );
  const reflow =
    !linearFlow && (!hasCompleteCoordinates || sourceColumnCount > columnCount);
  const nodes = sourceNodes.map((node, index) => {
    const row = Math.floor(index / columnCount);
    const rowOffset = index % columnCount;
    const column =
      linearFlow && row % 2 === 1 ? columnCount - 1 - rowOffset : rowOffset;
    return {
      ...node,
      renderRow: linearFlow || reflow ? row : (node.row ?? row),
      renderColumn: linearFlow || reflow ? column : (node.column ?? column),
    };
  });
  const nodesById = new Map(nodes.map((node) => [node.id, node]));
  const rowCount = Math.max(1, ...nodes.map((node) => node.renderRow + 1));
  const headerLabels = model.header_labels || [];
  const annotations = model.annotations || [];
  const sourceTexts = model.source_text || [];
  const layoutKind = String(model.layout?.kind || "grid").toLowerCase();
  const stepMode =
    linearFlow ||
    layoutKind.includes("algorithm") ||
    layoutKind.includes("trace") ||
    layoutKind === "sequence" ||
    layoutKind === "state";
  const safeStepIndex = Math.min(
    Math.max(0, activeStepIndex),
    Math.max(0, nodes.length - 1),
  );
  const selectedNode =
    nodes.find((node) => node.id === selectedNodeId) ||
    (stepMode ? nodes[safeStepIndex] : null);
  const selectedNodeIndex = selectedNode
    ? nodes.findIndex((node) => node.id === selectedNode.id)
    : -1;
  const selectedOutgoing = selectedNode
    ? edges.filter((edge) => edge.from === selectedNode.id)
    : [];
  const layoutLabel =
    {
      flow: "CONCEPT FLOW",
      sequence: "SEQUENCE",
      branching: "DECISION FLOW",
      architecture: "ARCHITECTURE",
      "concept-map": "CONCEPT MAP",
      timeline: "TIMELINE",
      comparison: "COMPARISON",
      table: "COMPARISON TABLE",
      state: "STATE DIAGRAM",
      "algorithm-trace": "ALGORITHM TRACE",
    }[layoutKind] || layoutKind.replace(/[-_]/g, " ").toUpperCase();

  return (
    <figure
      className={`dynamic-diagram dynamic-diagram-layout-${layoutKind.replace(/[^a-z0-9_-]/g, "") || "grid"}${linearFlow ? " dynamic-diagram-linear-flow" : ""}`}
      aria-label={alt || model.title || title}
    >
      <header className="dynamic-diagram-header">
        <div className="dynamic-diagram-header-topline">
          <span className="dynamic-diagram-eyebrow">
            <Sparkles size={14} aria-hidden="true" /> VISUAL EXPLANATION
          </span>
          <div className="dynamic-diagram-tools">
            <span className="dynamic-diagram-type">{layoutLabel}</span>
            {edges.some((edge) => edge.label) && (
              <button
                type="button"
                className="dynamic-diagram-control"
                aria-pressed={showEdgeLabels}
                onClick={() => setShowEdgeLabels((visible) => !visible)}
              >
                {showEdgeLabels ? "Hide edge labels" : "Show edge labels"}
              </button>
            )}
          </div>
        </div>
        {headerLabels.length > 0 && (
          <div className="dynamic-diagram-header-labels">
            {headerLabels.map((item) => (
              <span key={`head-${item.source_index}`}>{item.text}</span>
            ))}
          </div>
        )}
        <h3>{model.title || title}</h3>
        {(model.description || description) && (
          <p>{model.description || description}</p>
        )}
      </header>
      <div
        className="dynamic-diagram-board"
        role="list"
        aria-label={`Diagram concepts: ${model.title || title}`}
        style={{ "--diagram-columns": columnCount, "--diagram-rows": rowCount }}
      >
        {nodes.map((node, index) => (
          <div
            className="dynamic-diagram-node-wrap"
            key={node.id}
            role="listitem"
            style={{
              "--node-column": node.renderColumn + 1,
              "--node-row": node.renderRow + 1,
            }}
          >
            <DiagramNode
              node={node}
              index={index}
              edges={edges}
              nodesById={nodesById}
              layout={model.layout}
              linearFlow={linearFlow}
              onSelect={(nodeId) => {
                setSelectedNodeId(nodeId);
                const nextIndex = nodes.findIndex(
                  (candidate) => candidate.id === nodeId,
                );
                if (nextIndex >= 0) setActiveStepIndex(nextIndex);
              }}
              selected={selectedNode?.id === node.id}
              stepActive={stepMode && safeStepIndex === index}
              showEdgeLabels={showEdgeLabels}
            />
          </div>
        ))}
      </div>
      {stepMode && nodes.length > 1 && (
        <div
          className="dynamic-diagram-stepper"
          aria-label="Step through this diagram"
        >
          <span>
            Step {safeStepIndex + 1} of {nodes.length}
          </span>
          <div>
            <button
              type="button"
              className="dynamic-diagram-control"
              disabled={safeStepIndex <= 0}
              onClick={() => {
                const next = Math.max(0, safeStepIndex - 1);
                setActiveStepIndex(next);
                setSelectedNodeId(nodes[next].id);
              }}
            >
              Previous step
            </button>
            <button
              type="button"
              className="dynamic-diagram-control"
              disabled={safeStepIndex >= nodes.length - 1}
              onClick={() => {
                const next = Math.min(nodes.length - 1, safeStepIndex + 1);
                setActiveStepIndex(next);
                setSelectedNodeId(nodes[next].id);
              }}
            >
              Next step
            </button>
          </div>
        </div>
      )}
      {selectedNode && (
        <section
          className="dynamic-diagram-detail"
          aria-live="polite"
          aria-label={`Details for ${selectedNode.title || "selected concept"}`}
        >
          <div className="dynamic-diagram-detail-heading">
            <span className="dynamic-diagram-eyebrow">
              {stepMode ? `STEP ${selectedNodeIndex + 1}` : "SELECTED CONCEPT"}
            </span>
            <h4>{selectedNode.title || `Concept ${selectedNodeIndex + 1}`}</h4>
          </div>
          {(selectedNode.explanation || selectedNode.description) && (
            <p>{selectedNode.explanation || selectedNode.description}</p>
          )}
          {selectedNode.example && (
            <p>
              <strong>Example:</strong> {selectedNode.example}
            </p>
          )}
          {selectedNode.code && (
            <pre tabIndex={0}>
              <code>{selectedNode.code}</code>
            </pre>
          )}
          {!(
            selectedNode.explanation ||
            selectedNode.description ||
            selectedNode.example ||
            selectedNode.code
          ) && (
            <p>
              {(selectedNode.labels || [])
                .filter((label) => label.role !== "badge")
                .map((label) => label.text)
                .filter(Boolean)
                .join(" · ") ||
                "This node has no additional author-provided explanation."}
            </p>
          )}
          {selectedOutgoing.length > 0 && (
            <div className="dynamic-diagram-detail-links">
              <strong>Connects to</strong>
              {selectedOutgoing.map((edge) => (
                <span key={`${edge.from}-${edge.to}`}>
                  {nodesById.get(edge.to)?.title || edge.to}
                  {edge.label ? ` — ${edge.label}` : ""}
                </span>
              ))}
            </div>
          )}
        </section>
      )}
      {edges.some(
        (edge) =>
          edge.direction === "branch" ||
          edge.direction === "up" ||
          edge.direction === "left",
      ) && (
        <div
          className="dynamic-diagram-relationships"
          aria-label="Additional relationships"
        >
          <span className="dynamic-diagram-relationships-title">
            Relationships
          </span>
          {edges
            .filter(
              (edge) =>
                edge.direction === "branch" ||
                edge.direction === "up" ||
                edge.direction === "left",
            )
            .map((edge) => (
              <div
                className="dynamic-diagram-relationship"
                key={`relationship-${edge.from}-${edge.to}`}
              >
                <span>{nodesById.get(edge.from)?.title || edge.from}</span>
                <ArrowRight size={14} aria-hidden="true" />
                <span>{nodesById.get(edge.to)?.title || edge.to}</span>
              </div>
            ))}
        </div>
      )}
      {annotations.length > 0 && (
        <div className="dynamic-diagram-annotations" aria-label="Diagram notes">
          {annotations.map((item) => (
            <p key={`annotation-${item.source_index}`}>{item.text}</p>
          ))}
        </div>
      )}
      {caption && (
        <figcaption className="dynamic-diagram-caption">
          <span aria-hidden="true" />
          {caption}
        </figcaption>
      )}
      <span className="sr-only">
        This interactive layout was generated from {sourceTexts.length} original
        diagram text labels.
      </span>
    </figure>
  );
}
