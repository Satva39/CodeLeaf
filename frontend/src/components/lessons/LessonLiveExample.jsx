import { useMemo, useState } from "react";
import { Activity, ArrowRight, Braces, CheckCircle2, Code2, Database, GitBranch, Lightbulb, RotateCcw, ShieldCheck, Sparkles } from "lucide-react";
import { buildSandboxDocument, getLessonLiveExampleMode } from "../../lib/lessonLiveExampleModel.js";
import "../../styles/lesson-live-example.css";

const DEMO_ROWS = [
  { id: 101, name: "Asha", team: "Design", active: true, score: 88 },
  { id: 102, name: "Noah", team: "Engineering", active: true, score: 94 },
  { id: 103, name: "Mina", team: "Design", active: false, score: 76 },
  { id: 104, name: "Leo", team: "Engineering", active: true, score: 91 },
];
const INITIAL_ITEMS = ["HTML", "CSS", "JavaScript"];
const MODE_TITLES = {
  "browser-html": "Live HTML example",
  "browser-css": "Live CSS example",
  "browser-javascript": "Live JavaScript example",
  ui: "Interactive interface example",
  loops: "Explore a loop, one step at a time",
  conditions: "Try a condition with different inputs",
  collections: "Explore a collection interactively",
  functions: "Change an input and inspect the result",
  variables: "Explore a variable and its value",
  types: "Explore types and values",
  algorithm: "Watch an algorithm work",
  database: "Explore a small data query",
  spreadsheet: "Try a live formula",
  api: "Explore a request and response",
  git: "Explore a version history",
  containers: "Explore container state",
  cache: "See a cache hit and miss",
  security: "Test an access decision",
  data: "Explore a simple model decision",
  regex: "Test a regular expression",
  config: "Edit a configuration value",
  filesystem: "Explore a simulated file system",
  oop: "Inspect an object",
  "error-flow": "Explore the success and error paths",
  network: "Follow a request through the network",
  state: "Explore state transitions",
  math: "Change the value and see the calculation",
  concept: "Explore this lesson's idea",
};

function BrowserPreview({ mode, code, lessonTitle }) {
  const srcDoc = useMemo(() => buildSandboxDocument(mode, code, lessonTitle), [mode, code, lessonTitle]);
  return (
    <div className="lesson-live-browser">
      <div className="lesson-live-browser-toolbar">
        <span className="lesson-live-browser-dots" aria-hidden="true"><i /><i /><i /></span>
        <span className="lesson-live-browser-url"><span /> lesson-preview.local</span>
        <span className="lesson-live-browser-label">Sandboxed preview</span>
      </div>
      <iframe
        className="lesson-live-iframe"
        title="Live browser example for this lesson"
        sandbox="allow-scripts"
        referrerPolicy="no-referrer"
        srcDoc={srcDoc}
      />
      <p className="lesson-live-footnote">Preview updates from the lesson code editor. The isolated frame cannot access the CodeLeaf page or its cookies; outbound connections are blocked.</p>
    </div>
  );
}

function DemoDescription({ children }) {
  return <p className="lesson-live-description">{children}</p>;
}

function Simulator({ mode, lessonTitle, codeLanguage, intro }) {
  const [loopCount, setLoopCount] = useState(4);
  const [loopStep, setLoopStep] = useState(0);
  const [conditionValue, setConditionValue] = useState(12);
  const [threshold, setThreshold] = useState(10);
  const [items, setItems] = useState(INITIAL_ITEMS);
  const [newItem, setNewItem] = useState("React");
  const [functionValue, setFunctionValue] = useState(5);
  const [operation, setOperation] = useState("square");
  const [variableName, setVariableName] = useState("message");
  const [variableValue, setVariableValue] = useState("CodeLeaf");
  const [variableType, setVariableType] = useState("string");
  const [isSorted, setIsSorted] = useState(false);
  const [target, setTarget] = useState(5);
  const [team, setTeam] = useState("All teams");
  const [method, setMethod] = useState("GET");
  const [endpoint, setEndpoint] = useState("/api/lessons");
  const [commits, setCommits] = useState(3);
  const [branch, setBranch] = useState("main");
  const [running, setRunning] = useState(true);
  const [replicas, setReplicas] = useState(2);
  const [cacheLoaded, setCacheLoaded] = useState(false);
  const [cacheReads, setCacheReads] = useState(0);
  const [authenticated, setAuthenticated] = useState(true);
  const [authorized, setAuthorized] = useState(false);
  const [confidence, setConfidence] = useState(72);
  const [decisionThreshold, setDecisionThreshold] = useState(60);
  const [regexPattern, setRegexPattern] = useState("code\\w+");
  const [regexText, setRegexText] = useState("CodeLeaf makes code clear");
  const [configKey, setConfigKey] = useState("theme");
  const [configValue, setConfigValue] = useState("dark");
  const [fileName, setFileName] = useState("notes.txt");
  const [fileAction, setFileAction] = useState("read");
  const [objectName, setObjectName] = useState("Asha");
  const [objectRole, setObjectRole] = useState("Learner");
  const [throwError, setThrowError] = useState(false);
  const [networkStage, setNetworkStage] = useState(2);
  const [stateOn, setStateOn] = useState(false);
  const [mathValue, setMathValue] = useState(6);
  const [activeTab, setActiveTab] = useState("Overview");
  const [clicks, setClicks] = useState(0);
  const [conceptCase, setConceptCase] = useState("typical");
  const modeName = MODE_TITLES[mode] || MODE_TITLES.concept;
  const titleSnippet = String(lessonTitle || "this concept").replace(/[<>]/g, "");

  if (mode === "loops") return <>
    <DemoDescription>Increase the number of iterations and move through the loop. The highlighted row is the current step.</DemoDescription>
    <div className="lesson-live-controls"><label>Iterations <strong>{loopCount}</strong><input type="range" min="1" max="8" value={loopCount} onChange={(e) => { const v = Number(e.target.value); setLoopCount(v); setLoopStep((s) => Math.min(s, v - 1)); }} /></label><label>Current step <strong>{loopStep + 1}</strong><input type="range" min="0" max={Math.max(0, loopCount - 1)} value={loopStep} onChange={(e) => setLoopStep(Number(e.target.value))} /></label></div>
    <div className="lesson-live-loop-list">{Array.from({ length: loopCount }, (_, i) => <div key={i} className={i === loopStep ? "is-current" : ""}><code>i = {i}</code><span>{i === loopStep ? "Current iteration" : i < loopStep ? "Completed" : "Waiting"}</span></div>)}</div>
    <div className="lesson-live-result"><CheckCircle2 size={16} /> The loop body runs <strong>{loopCount}</strong> times, with indices from 0 to {loopCount - 1}.</div>
  </>;

  if (mode === "conditions") return <>
    <DemoDescription>Change the value or threshold and observe how a comparison changes the branch that would run.</DemoDescription>
    <div className="lesson-live-controls two"><label>Input value <strong>{conditionValue}</strong><input type="range" min="0" max="20" value={conditionValue} onChange={(e) => setConditionValue(Number(e.target.value))} /></label><label>Threshold <strong>{threshold}</strong><input type="range" min="0" max="20" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} /></label></div>
    <div className={`lesson-live-decision ${conditionValue >= threshold ? "is-true" : "is-false"}`}><span className="lesson-live-decision-label">condition result</span><code>{conditionValue} &gt;= {threshold}</code><strong>{conditionValue >= threshold ? "TRUE · first branch" : "FALSE · alternative branch"}</strong></div>
  </>;

  if (mode === "collections") return <>
    <DemoDescription>Add and remove values, then see how the collection changes. This models collection operations; it does not execute the source-language snippet.</DemoDescription>
    <form className="lesson-live-inline-form" onSubmit={(e) => { e.preventDefault(); const value = newItem.trim(); if (value && items.length < 10) setItems((old) => [...old, value]); setNewItem(""); }}><label className="sr-only" htmlFor="live-collection-item">New item</label><input id="live-collection-item" value={newItem} onChange={(e) => setNewItem(e.target.value)} placeholder="Add a value" /><button type="submit" disabled={!newItem.trim() || items.length >= 10}>Add item</button><button type="button" className="is-secondary" onClick={() => setItems(INITIAL_ITEMS)}><RotateCcw size={14} /> Reset</button></form>
    <div className="lesson-live-chips">{items.map((item, index) => <button type="button" key={`${index}-${item}`} title={`Remove ${item}`} onClick={() => setItems((old) => old.filter((_, i) => i !== index))}><span>{index}</span>{item}<b aria-hidden="true">×</b></button>)}</div>
    <div className="lesson-live-result">Length: <strong>{items.length}</strong> · Last index: <strong>{items.length - 1}</strong></div>
  </>;

  if (mode === "functions") {
    const result = operation === "double" ? functionValue * 2 : operation === "add10" ? functionValue + 10 : functionValue * functionValue;
    return <>
      <DemoDescription>Choose an input and a simple operation to see the relationship between an argument and a returned value.</DemoDescription>
      <div className="lesson-live-controls"><label>Input x <strong>{functionValue}</strong><input type="range" min="-10" max="10" value={functionValue} onChange={(e) => setFunctionValue(Number(e.target.value))} /></label><label>Example operation<select value={operation} onChange={(e) => setOperation(e.target.value)}><option value="square">x × x</option><option value="double">x × 2</option><option value="add10">x + 10</option></select></label></div>
      <div className="lesson-live-function-flow"><code>input: {functionValue}</code><ArrowRight size={18} /><code>function</code><ArrowRight size={18} /><strong>return: {result}</strong></div>
    </>;
  }

  if (mode === "variables" || mode === "types") {
    const safeName = (variableName || "value").replace(/[^a-zA-Z0-9_$]/g, "_").replace(/^[^a-zA-Z_$]+/, "value");
    let previewValue = variableValue;
    let displayedType = "string";
    let typedDeclaration = `const ${safeName} = ${JSON.stringify(variableValue)};`;
    if (variableType === "number") {
      previewValue = variableValue.trim() === "" || !Number.isFinite(Number(variableValue)) ? "NaN" : Number(variableValue);
      displayedType = "number";
      typedDeclaration = mode === "types" ? `const ${safeName}: number = ${previewValue};` : `const ${safeName} = ${previewValue};`;
    } else if (variableType === "boolean") {
      previewValue = variableValue === "true";
      displayedType = "boolean";
      typedDeclaration = mode === "types" ? `const ${safeName}: boolean = ${previewValue};` : `const ${safeName} = ${previewValue};`;
    } else if (variableType === "array") {
      try { const parsed = JSON.parse(variableValue); previewValue = Array.isArray(parsed) ? parsed : [variableValue]; } catch { previewValue = variableValue.split(",").map((part) => part.trim()).filter(Boolean); }
      displayedType = "array";
      typedDeclaration = `const ${safeName}${mode === "types" ? ": string[]" : ""} = ${JSON.stringify(previewValue)};`;
    } else if (variableType === "object") {
      try { const parsed = JSON.parse(variableValue); previewValue = parsed && typeof parsed === "object" ? parsed : { value: variableValue }; } catch { previewValue = { value: variableValue, active: true }; }
      displayedType = "object";
      typedDeclaration = `const ${safeName}${mode === "types" ? ": object" : ""} = ${JSON.stringify(previewValue)};`;
    } else if (variableType === "null") {
      previewValue = null;
      displayedType = "object (null)";
      typedDeclaration = `const ${safeName} = null;`;
    } else {
      displayedType = "string";
      typedDeclaration = `const ${safeName}${mode === "types" ? ": string" : ""} = ${JSON.stringify(variableValue)};`;
    }
    return <>
      <DemoDescription>{mode === "types" ? "Choose a type and value to see a simple declaration update. This is a type/value visualizer, not a TypeScript compiler." : "Edit a variable's name and value. The preview shows the stored value and a simplified type label."}</DemoDescription>
      <div className="lesson-live-controls two"><label>Variable name<input value={variableName} onChange={(e) => setVariableName(e.target.value)} /></label><label>Type<select value={variableType} onChange={(e) => setVariableType(e.target.value)}><option value="string">string</option><option value="number">number</option><option value="boolean">boolean</option><option value="array">array</option><option value="object">object</option><option value="null">null</option></select></label><label>Value<input value={variableValue} onChange={(e) => setVariableValue(e.target.value)} placeholder="Enter a value" /></label></div>
      <pre className="lesson-live-code-output">{typedDeclaration}</pre>
      <div className="lesson-live-object"><span>LIVE VALUE INSPECTOR</span><strong>{safeName}</strong><dl><dt>Type</dt><dd>{displayedType}</dd><dt>Value</dt><dd>{JSON.stringify(previewValue)}</dd></dl></div>
    </>;
  }

  if (mode === "algorithm") {
    const values = isSorted ? [1, 3, 5, 6, 8] : [8, 3, 5, 1, 6];
    const found = values.includes(Number(target));
    return <>
      <DemoDescription>Use a small sample to see how sorting changes order and how a target lookup checks values. This visual trace is illustrative, not a native-code execution.</DemoDescription>
      <div className="lesson-live-array-bars">{values.map((value, i) => <div className={Number(target) === value ? "is-target" : ""} key={`${i}-${value}`}><span style={{ height: `${18 + value * 8}px` }} /><code>{value}</code><small>{i}</small></div>)}</div>
      <div className="lesson-live-controls two"><label>Find target <input type="number" min="0" max="9" value={target} onChange={(e) => setTarget(e.target.value)} /></label><div className="lesson-live-button-group"><button type="button" onClick={() => setIsSorted((s) => !s)}>{isSorted ? "Restore original order" : "Sort values"}</button></div></div>
      <div className="lesson-live-result"><CheckCircle2 size={16} /> {found ? `Target ${target} appears at index ${values.indexOf(Number(target))}.` : `Target ${target} is not in this sample.`}</div>
    </>;
  }

  if (mode === "database") {
    const rows = DEMO_ROWS.filter((row) => team === "All teams" || row.team === team);
    return <>
      <DemoDescription>Change the filter to see how a query narrows a table. This local demonstration does not send a database request.</DemoDescription>
      <div className="lesson-live-controls"><label>WHERE team = <select value={team} onChange={(e) => setTeam(e.target.value)}><option>All teams</option><option>Design</option><option>Engineering</option></select></label><span className="lesson-live-count">{rows.length} row{rows.length === 1 ? "" : "s"}</span></div>
      <div className="lesson-live-table-wrap"><table className="lesson-live-table"><thead><tr><th>id</th><th>name</th><th>team</th><th>active</th><th>score</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id}><td>{row.id}</td><td>{row.name}</td><td>{row.team}</td><td>{String(row.active)}</td><td>{row.score}</td></tr>)}</tbody></table></div>
      <div className="lesson-live-result"><Database size={16} /> Conceptual equivalent: <code>SELECT * FROM learners{team === "All teams" ? ";" : ` WHERE team = '${team}';`}</code></div>
    </>;
  }

  if (mode === "spreadsheet") return <>
    <DemoDescription>Adjust the unit price or quantity. The total cell recalculates immediately, as a spreadsheet formula would.</DemoDescription>
    <div className="lesson-live-sheet"><div className="sheet-cell sheet-head">A</div><div className="sheet-cell sheet-head">B</div><div className="sheet-cell sheet-head">C</div><div className="sheet-cell sheet-label">Unit price</div><div className="sheet-cell"><input aria-label="Unit price" type="number" min="0" value={functionValue} onChange={(e) => setFunctionValue(Number(e.target.value))} /></div><div className="sheet-cell sheet-label">Quantity</div><div className="sheet-cell"><input aria-label="Quantity" type="number" min="0" value={loopCount} onChange={(e) => setLoopCount(Number(e.target.value))} /></div><div className="sheet-cell sheet-label">Total</div><div className="sheet-cell sheet-total">={functionValue} × {loopCount} = {functionValue * loopCount}</div></div>
    <div className="lesson-live-result">Formula idea: <code>=B2*B3</code></div>
  </>;

  if (mode === "api") return <>
    <DemoDescription>Change the method and path to inspect a simulated HTTP request and response. No network request is sent.</DemoDescription>
    <div className="lesson-live-controls"><label>Method<select value={method} onChange={(e) => setMethod(e.target.value)}><option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option><option>DELETE</option></select></label><label>Path<input value={endpoint} onChange={(e) => setEndpoint(e.target.value)} /></label></div>
    <div className="lesson-live-request"><div><span>REQUEST</span><code>{method} {endpoint || "/"} HTTP/1.1</code><small>Accept: application/json</small></div><ArrowRight size={20} /><div><span>SIMULATED RESPONSE</span><strong>{method === "POST" ? "201 Created" : method === "DELETE" ? "204 No Content" : "200 OK"}</strong><pre>{method === "DELETE" ? "// response body is empty" : JSON.stringify({ ok: true, method, path: endpoint || "/", demo: true }, null, 2)}</pre></div></div>
  </>;

  if (mode === "git") return <>
    <DemoDescription>Create a commit or switch branches to see a simple version-history model update.</DemoDescription>
    <div className="lesson-live-controls"><label>Current branch<select value={branch} onChange={(e) => setBranch(e.target.value)}><option>main</option><option>feature/demo</option><option>fix/example</option></select></label><div className="lesson-live-button-group"><button type="button" onClick={() => setCommits((n) => Math.min(7, n + 1))} disabled={commits >= 7}>Add commit</button><button type="button" className="is-secondary" onClick={() => { setCommits(3); setBranch("main"); }}><RotateCcw size={14} /> Reset</button></div></div>
    <div className="lesson-live-commit-line">{Array.from({ length: commits }, (_, i) => <div key={i} className={i === commits - 1 ? "is-latest" : ""}><span /><code>{i === 0 ? "init" : `c${String(i).padStart(2, "0")}`}</code>{i === commits - 1 && <small>HEAD → {branch}</small>}</div>)}</div>
    <div className="lesson-live-result"><GitBranch size={16} /> {commits} commits on the selected branch model.</div>
  </>;

  if (mode === "containers") return <>
    <DemoDescription>Toggle the simulated service and scale the number of replicas to see how deployment state changes.</DemoDescription>
    <div className="lesson-live-controls"><label>Replicas <strong>{replicas}</strong><input type="range" min="1" max="5" value={replicas} onChange={(e) => setReplicas(Number(e.target.value))} /></label><button type="button" className={running ? "is-secondary" : ""} onClick={() => setRunning((v) => !v)}>{running ? "Stop containers" : "Start containers"}</button></div>
    <div className="lesson-live-container-grid">{Array.from({ length: replicas }, (_, i) => <div key={i} className={running ? "is-running" : "is-stopped"}><span className="container-light" /><strong>web-{i + 1}</strong><small>{running ? "running" : "stopped"}</small></div>)}</div>
    <div className="lesson-live-result">Service: <strong>{running ? "available" : "unavailable"}</strong> · Ready replicas: <strong>{running ? replicas : 0}/{replicas}</strong></div>
  </>;

  if (mode === "cache") return <>
    <DemoDescription>Read the same value more than once. The first read fills the cache; subsequent reads can be served from it.</DemoDescription>
    <div className="lesson-live-cache"><div className={`cache-node ${cacheLoaded ? "is-warm" : ""}`}><Activity size={20} /><strong>Cache</strong><span>{cacheLoaded ? "value: 42" : "empty"}</span></div><ArrowRight /><div className="cache-node"><Database size={20} /><strong>Primary store</strong><span>value: 42</span></div></div>
    <div className="lesson-live-button-group"><button type="button" onClick={() => { setCacheReads((n) => n + 1); setCacheLoaded(true); }}>Read value</button><button className="is-secondary" type="button" onClick={() => { setCacheLoaded(false); setCacheReads(0); }}><RotateCcw size={14} /> Clear cache</button><span className="lesson-live-count">Reads: {cacheReads} · {cacheLoaded && cacheReads > 1 ? `${cacheReads - 1} cache hit(s)` : cacheLoaded ? "1 cache miss" : "not read yet"}</span></div>
  </>;

  if (mode === "security") {
    const status = !authenticated ? 401 : !authorized ? 403 : 200;
    return <>
      <DemoDescription>Toggle authentication and permission separately to see why identity checks and access-control checks solve different problems. This is a defensive, local simulation.</DemoDescription>
      <div className="lesson-live-toggle-list"><label><input type="checkbox" checked={authenticated} onChange={(e) => setAuthenticated(e.target.checked)} /> User is authenticated</label><label><input type="checkbox" checked={authorized} onChange={(e) => setAuthorized(e.target.checked)} /> User has the required permission</label></div>
      <div className={`lesson-live-security-result status-${status}`}><ShieldCheck size={22} /><div><span>REQUEST DECISION</span><strong>{status} · {status === 200 ? "Allowed" : status === 401 ? "Authentication required" : "Permission denied"}</strong><p>{status === 200 ? "Both identity and permission checks passed." : status === 401 ? "Establish who the user is before checking access." : "The user is known, but the requested action is not permitted."}</p></div></div>
    </>;
  }

  if (mode === "data") {
    const label = confidence >= decisionThreshold ? "Positive" : "Negative";
    return <>
      <DemoDescription>Adjust a model confidence score and the decision threshold. This illustrates thresholding only; it is not a trained machine-learning model.</DemoDescription>
      <div className="lesson-live-controls two"><label>Illustrative confidence <strong>{confidence}%</strong><input type="range" min="0" max="100" value={confidence} onChange={(e) => setConfidence(Number(e.target.value))} /></label><label>Decision threshold <strong>{decisionThreshold}%</strong><input type="range" min="0" max="100" value={decisionThreshold} onChange={(e) => setDecisionThreshold(Number(e.target.value))} /></label></div>
      <div className="lesson-live-score"><div className="score-meter"><span style={{ width: `${confidence}%` }} /></div><div className="score-threshold" style={{ left: `${decisionThreshold}%` }} /><div className={`lesson-live-result ${label === "Positive" ? "result-positive" : "result-negative"}`}>Illustrative prediction: <strong>{label}</strong> <span>({confidence}% {confidence >= decisionThreshold ? "meets" : "does not meet"} the {decisionThreshold}% threshold)</span></div></div>
    </>;
  }

  if (mode === "regex") {
    let matchText = "Enter a pattern that matches some of the sample text.";
    let hasMatch = false;
    try { const found = new RegExp(regexPattern); const match = regexText.match(found); hasMatch = Boolean(match); matchText = match ? `Matched: ${match[0]}` : "No match found."; } catch (error) { matchText = `Pattern error: ${error.message}`; }
    return <><DemoDescription>Change the pattern and input text to test matching. This uses the browser's JavaScript regular-expression engine.</DemoDescription><div className="lesson-live-controls"><label>Pattern<input value={regexPattern} onChange={(e) => setRegexPattern(e.target.value)} spellCheck="false" /></label><label>Input text<input value={regexText} onChange={(e) => setRegexText(e.target.value)} /></label></div><div className={`lesson-live-result ${hasMatch ? "result-positive" : "result-negative"}`}><Braces size={16} /> {matchText}</div></>;
  }

  if (mode === "config") {
    const isYaml = ["yaml", "yml"].includes(normalized(codeLanguage));
    const isXml = normalized(codeLanguage) === "xml";
    const xmlKey = (configKey || "key").replace(/[^a-zA-Z0-9_.-]/g, "_");
    const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
    const configText = isYaml
      ? `${configKey}: ${JSON.stringify(configValue)}\nenabled: true\nlesson: ${JSON.stringify(titleSnippet)}`
      : isXml
        ? `<settings>\n  <${xmlKey}>${xmlEscape(configValue)}</${xmlKey}>\n  <enabled>true</enabled>\n  <lesson>${xmlEscape(titleSnippet)}</lesson>\n</settings>`
        : JSON.stringify({ [configKey || "key"]: configValue, enabled: true, lesson: titleSnippet }, null, 2);
    return <><DemoDescription>Edit a value and inspect a valid configuration shape. This illustrates the selected format; it is not a full configuration-file parser.</DemoDescription><div className="lesson-live-controls two"><label>Key<input value={configKey} onChange={(e) => setConfigKey(e.target.value)} /></label><label>Value<input value={configValue} onChange={(e) => setConfigValue(e.target.value)} /></label></div><pre className="lesson-live-code-output">{configText}</pre></>;
  }

  if (mode === "filesystem") return <>
    <DemoDescription>Choose a harmless illustrative file operation. No real file, shell command, or operating-system process is accessed.</DemoDescription>
    <div className="lesson-live-controls two"><label>Operation<select value={fileAction} onChange={(e) => setFileAction(e.target.value)}><option value="read">Read file</option><option value="write">Write file</option><option value="list">List directory</option><option value="check">Check exists</option></select></label><label>Path<input value={fileName} onChange={(e) => setFileName(e.target.value)} /></label></div>
    <div className="lesson-live-terminal"><div><i /><i /><i /><span>simulated terminal</span></div><code>$ {fileAction === "read" ? `cat ${fileName}` : fileAction === "write" ? `printf 'hello' > ${fileName}` : fileAction === "list" ? `ls ${fileName || "."}` : `test -e ${fileName} && echo exists`}</code><p>{fileAction === "read" ? `Preview: content from ${fileName || "the selected file"} would be displayed here.` : fileAction === "write" ? `A simulated write would create or replace ${fileName || "the selected file"}.` : fileAction === "list" ? `A simulated directory listing for ${fileName || "."}.` : `Illustrative result: ${fileName ? "exists" : "path is required"}.`}</p></div>
  </>;

  if (mode === "oop") return <><DemoDescription>Update an object's properties to see how its data changes. This is an object model, not execution of the course language.</DemoDescription><div className="lesson-live-controls two"><label>Name<input value={objectName} onChange={(e) => setObjectName(e.target.value)} /></label><label>Role<input value={objectRole} onChange={(e) => setObjectRole(e.target.value)} /></label></div><div className="lesson-live-object"><span>OBJECT INSTANCE</span><strong>{objectName || "Unnamed"}</strong><dl><dt>name</dt><dd>{JSON.stringify(objectName)}</dd><dt>role</dt><dd>{JSON.stringify(objectRole)}</dd></dl></div></>;

  if (mode === "error-flow") return <><DemoDescription>Toggle an error to trace the normal and recovery paths. The simulation is local and doesn't run the source code.</DemoDescription><label className="lesson-live-checkbox"><input type="checkbox" checked={throwError} onChange={(e) => setThrowError(e.target.checked)} /> Simulate an operation failure</label><div className="lesson-live-flow"><div className={!throwError ? "is-current" : ""}><span>1</span><strong>Try</strong><small>Run the operation</small></div><ArrowRight /><div className={throwError ? "is-current is-error" : ""}><span>2</span><strong>{throwError ? "Catch / recover" : "Success"}</strong><small>{throwError ? "Handle the failure" : "Continue normally"}</small></div><ArrowRight /><div className="is-complete"><span>3</span><strong>Finish</strong><small>Keep the app responsive</small></div></div></>;

  if (mode === "network") return <><DemoDescription>Move the request through a simplified network path. This is a conceptual visualization, not a real packet capture.</DemoDescription><label className="lesson-live-controls">Request progress <strong>{networkStage}/4</strong><input type="range" min="0" max="4" value={networkStage} onChange={(e) => setNetworkStage(Number(e.target.value))} /></label><div className="lesson-live-network">{["Client", "DNS lookup", "Network", "Server", "Response"].map((label, i) => <div key={label} className={i <= networkStage ? "is-reached" : ""}><span>{i + 1}</span><strong>{label}</strong>{i < 4 && <ArrowRight size={15} />}</div>)}</div><div className="lesson-live-result">{networkStage === 4 ? "Response reached the client." : `Request is at: ${["Client", "DNS lookup", "Network", "Server", "Response"][networkStage]}.`}</div></>;

  if (mode === "state") return <><DemoDescription>Trigger a state change and inspect the current state and transition that caused it.</DemoDescription><div className={`lesson-live-state-card ${stateOn ? "is-on" : ""}`}><span>current state</span><strong>{stateOn ? "ACTIVE" : "IDLE"}</strong><p>{stateOn ? "The event handler changed state to active." : "Waiting for an event to change state."}</p><button type="button" onClick={() => setStateOn((v) => !v)}>{stateOn ? "Send reset event" : "Send start event"}</button></div><div className="lesson-live-result">Transition: <code>{stateOn ? "IDLE → ACTIVE" : "ACTIVE → IDLE"}</code></div></>;

  if (mode === "math") return <><DemoDescription>Move the value to see a calculation update immediately; use this to check how input size influences the result.</DemoDescription><label className="lesson-live-controls">Value x <strong>{mathValue}</strong><input type="range" min="0" max="20" value={mathValue} onChange={(e) => setMathValue(Number(e.target.value))} /></label><div className="lesson-live-math-results"><div><span>x</span><strong>{mathValue}</strong></div><div><span>x²</span><strong>{mathValue * mathValue}</strong></div><div><span>2x + 1</span><strong>{2 * mathValue + 1}</strong></div></div></>;

  if (mode === "ui") return <><DemoDescription>Interact with a small sample interface to explore components, state, and user feedback. This preview illustrates UI behavior; it does not compile the framework source snippet.</DemoDescription><div className="lesson-live-ui-demo"><div className="lesson-live-ui-top"><span>CODELEAF / DEMO APP</span><button type="button" className="is-secondary" onClick={() => setClicks((n) => n + 1)}>Action {clicks ? `(${clicks})` : ""}</button></div><div className="lesson-live-ui-body"><aside>{["Overview", "Activity", "Settings"].map((tab) => <button type="button" className={activeTab === tab ? "is-current" : "is-secondary"} onClick={() => setActiveTab(tab)} key={tab}>{tab}</button>)}</aside><section><span className="lesson-live-eyebrow">ACTIVE VIEW</span><h4>{activeTab}</h4><p>{activeTab === "Overview" ? `This component has been activated ${clicks} time${clicks === 1 ? "" : "s"}.` : activeTab === "Activity" ? `Latest interaction count: ${clicks}.` : "Settings are local to this example."}</p><button type="button" onClick={() => setClicks((n) => n + 1)}>Update state</button></section></div></div></>;

  // Generic interactive fallback for lessons whose runtime cannot safely run in
  // a browser. It still gives the learner a real input/edge-case exploration.
  const selected = conceptCase === "typical" ? "A normal, expected input" : conceptCase === "boundary" ? "An input near the supported limit" : "An empty or invalid input";
  const inputPlaceholder = conceptCase === "typical" ? "example value" : conceptCase === "boundary" ? "0" : "";
  return <><DemoDescription>This guided experiment is an illustrative model for “{titleSnippet}”. It does not execute {codeLanguage || "the lesson"} code; use it to think through normal inputs and edge cases before testing the lesson's own example.</DemoDescription><div className="lesson-live-case-tabs" role="group" aria-label="Choose a test case">{[{ value: "typical", label: "Typical case" }, { value: "boundary", label: "Boundary case" }, { value: "invalid", label: "Invalid case" }].map((item) => <button type="button" className={conceptCase === item.value ? "is-current" : "is-secondary"} onClick={() => setConceptCase(item.value)} key={item.value}>{item.label}</button>)}</div><div className="lesson-live-generic"><div><span>TEST CASE</span><strong>{selected}</strong><code>{JSON.stringify(inputPlaceholder)}</code></div><ArrowRight size={20} /><div><span>WHAT TO INSPECT</span><strong>{conceptCase === "typical" ? "Expected behavior" : conceptCase === "boundary" ? "Limit handling" : "Validation and recovery"}</strong><p>{intro || "Trace the lesson's rule from input to observable result, then compare it with the code example."}</p></div></div></>;
}

export default function LessonLiveExample({ courseSlug, courseTitle, lessonTitle, code, codeLanguage, expectedOutput, intro }) {
  const mode = useMemo(() => getLessonLiveExampleMode({ courseSlug, lessonTitle, codeLanguage }), [courseSlug, lessonTitle, codeLanguage]);
  const isBrowser = mode.startsWith("browser-");
  return (
    <section className="lesson-live-example lesson-content-block" aria-labelledby="lesson-live-example-heading">
      <div className="lesson-live-heading-row">
        <span className="lesson-live-icon" aria-hidden="true">{isBrowser ? <Code2 size={19} /> : <Sparkles size={19} />}</span>
        <div className="lesson-live-heading-copy">
          <span className="lesson-live-eyebrow">LEARN BY TRYING</span>
          <h2 id="lesson-live-example-heading">{MODE_TITLES[mode] || MODE_TITLES.concept}</h2>
          <p>{lessonTitle}{courseTitle ? ` · ${courseTitle}` : ""}</p>
        </div>
        <span className="lesson-live-badge"><Activity size={13} /> Interactive</span>
      </div>
      <div className="lesson-live-surface">
        {isBrowser ? <BrowserPreview mode={mode} code={code} lessonTitle={lessonTitle} /> : <Simulator mode={mode} lessonTitle={lessonTitle} codeLanguage={codeLanguage} intro={intro} />}
      </div>
      {!isBrowser && <div className="lesson-live-safety-note"><Lightbulb size={14} /> {mode === "concept" ? "Use this as a reasoning guide; compare the selected case with the actual code and lesson notes." : `Illustrative ${mode.replaceAll("-", " ")} simulator. It does not execute arbitrary ${codeLanguage || "course"} code.`}</div>}
      {isBrowser && expectedOutput && <details className="lesson-live-expected"><summary>Compare with the lesson's expected result</summary><pre>{expectedOutput}</pre></details>}
    </section>
  );
}
