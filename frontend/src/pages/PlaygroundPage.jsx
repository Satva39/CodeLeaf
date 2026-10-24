import { useEffect, useMemo, useState } from "react";

import { FileCode2, Monitor, Play, ShieldCheck, TerminalSquare } from "lucide-react";

import { PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";

const DEFAULT_HTML = "<main>\n  <h1>Hello, CodeLeaf!</h1>\n  <p>Build an idea one line at a time.</p>\n  <button onclick=\"document.querySelector('p').textContent = 'You made it interactive!'\">Try me</button>\n</main>";
const DEFAULT_CSS = "body {\n  font-family: system-ui, sans-serif;\n  padding: 2rem;\n  color: #172033;\n}\nbutton {\n  padding: .65rem 1rem;\n  border-radius: .6rem;\n  border: 0;\n  background: #0da875;\n  color: white;\n}";
const FINAL_RUNNER_STATES = new Set(["completed", "failed", "timeout", "output_limit", "cancelled", "expired"]);

async function responsePayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.detail || payload.message || `Request failed (${response.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return payload;
}

export default function PlaygroundPage() {
  const [html, setHtml] = useState(DEFAULT_HTML);
  const [css, setCss] = useState(DEFAULT_CSS);
  const [view, setView] = useState("html");
  const [refresh, setRefresh] = useState(0);
  const [runnerLanguage, setRunnerLanguage] = useState("python");
  const [runnerSource, setRunnerSource] = useState("name = input('What is your name? ')\nprint(f'Hello, {name}!')");
  const [runnerInput, setRunnerInput] = useState("CodeLeaf");
  const [runnerStatus, setRunnerStatus] = useState("idle");
  const [runnerResult, setRunnerResult] = useState(null);
  const [runnerMessage, setRunnerMessage] = useState("");
  const [running, setRunning] = useState(false);
  const [runnerConfigured, setRunnerConfigured] = useState(false);
  const [runnerConfigChecked, setRunnerConfigChecked] = useState(false);

  useEffect(() => {
    let active = true;
    async function loadRunnerStatus() {
      try {
        const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/status`));
        if (!active) return;
        setRunnerConfigured(payload.configured === true);
        setRunnerMessage(payload.configured === true ? "" : (payload.message || "The isolated runner is not configured yet."));
      } catch {
        if (!active) return;
        setRunnerConfigured(false);
        setRunnerMessage("Runner availability could not be checked. Browser preview is still available.");
      } finally {
        if (active) setRunnerConfigChecked(true);
      }
    }
    loadRunnerStatus();
    return () => { active = false; };
  }, []);

  const doc = useMemo(
    () => `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'"><style>${css}</style></head><body>${html}</body></html>`,
    [html, css, refresh],
  );

  async function runRemoteCode() {
    setRunning(true);
    setRunnerMessage("");
    setRunnerResult(null);
    setRunnerStatus("submitting");
    try {
      const created = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: runnerLanguage, source: runnerSource, stdin: runnerInput }),
      }));
      const jobId = created.job?.id;
      if (!jobId) throw new Error("The API did not return a valid job reference.");
      setRunnerStatus(created.job.status || "queued");
      // Poll only for a bounded window. Every execution still has a server-side timeout.
      for (let attempt = 0; attempt < 12; attempt += 1) {
        const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(jobId)}`));
        const result = payload.job || {};
        setRunnerStatus(result.status || "unknown");
        setRunnerResult({ ...(result.result || {}), job_id: jobId });
        if (FINAL_RUNNER_STATES.has(result.status)) return;
        await new Promise((resolve) => setTimeout(resolve, 600));
      }
      setRunnerMessage("The job is still queued or running. Use Check status to retrieve its latest result.");
      setRunnerStatus("running");
      setRunnerResult({ job_id: jobId });
    } catch (error) {
      setRunnerStatus("unavailable");
      setRunnerMessage(error instanceof Error ? error.message : "Could not run the code.");
    } finally {
      setRunning(false);
    }
  }

  async function checkRunnerStatus() {
    const jobId = runnerResult?.job_id;
    if (!jobId || running) return;
    setRunning(true);
    setRunnerMessage("");
    try {
      const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(jobId)}`));
      const result = payload.job || {};
      setRunnerStatus(result.status || "unknown");
      setRunnerResult({ ...(result.result || {}), job_id: jobId });
      if (!FINAL_RUNNER_STATES.has(result.status)) setRunnerMessage("This job has not finished yet.");
    } catch (error) {
      setRunnerMessage(error instanceof Error ? error.message : "Could not retrieve job status.");
    } finally {
      setRunning(false);
    }
  }

  async function cancelRunnerJob() {
    const jobId = runnerResult?.job_id;
    if (!jobId || running) return;
    setRunning(true);
    setRunnerMessage("");
    try {
      const result = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(jobId)}`, { method: "DELETE" }));
      setRunnerStatus(result.status || "cancelled");
      setRunnerResult((previous) => ({ ...(previous || {}), message: "Job cancellation requested.", job_id: jobId }));
    } catch (error) {
      setRunnerMessage(error instanceof Error ? error.message : "Could not cancel this job.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <PageShell className="playground-page">
      <div className="playground-heading">
        <div>
          <div className="eyebrow">BROWSER PLAYGROUND</div>
          <h1>Try an idea. See what happens.</h1>
          <p>Preview HTML and CSS in your browser, or submit a small Python or JavaScript program to the separately configured isolated runner.</p>
        </div>
        <button className="button button-primary" onClick={() => setRefresh((x) => x + 1)}>
          <Play size={15} fill="currentColor" /> Run preview
        </button>
      </div>
      <div className="playground-workspace panel">
        <div className="playground-editor">
          <div className="editor-tabs">
            {["html", "css"].map((x) => (
              <button key={x} className={view === x ? "active" : ""} onClick={() => setView(x)}>
                <FileCode2 size={14} /> {x === "html" ? "index.html" : "styles.css"}
              </button>
            ))}
            <button className="editor-reset" onClick={() => { setHtml(DEFAULT_HTML); setCss(DEFAULT_CSS); }}>Reset</button>
          </div>
          <label htmlFor="playground-code" className="sr-only">Code editor</label>
          <textarea id="playground-code" spellCheck="false" value={view === "html" ? html : css}
            onChange={(event) => view === "html" ? setHtml(event.target.value) : setCss(event.target.value)} />
          <div className="editor-status"><span><span className="live-dot" /> Ready</span><span>Demo workspace · No files saved to an account</span></div>
        </div>
        <div className="playground-preview">
          <div className="preview-topbar"><span><Monitor size={15} /> Preview</span><button onClick={() => setRefresh((x) => x + 1)}><Play size={12} /> Refresh</button></div>
          <iframe key={refresh} title="Code preview" sandbox="allow-scripts" srcDoc={doc} />
        </div>
      </div>
      <div className="playground-note"><ShieldCheck size={16} /><span>This browser preview has a sandboxed iframe and a restrictive Content Security Policy. Server-executed code is sent only to the separate runner service; the main FastAPI process does not execute learner code.</span></div>

      <section className="runner-panel panel" aria-labelledby="runner-heading">
        <div className="runner-heading">
          <div><div className="eyebrow">ISOLATED CODE RUNNER</div><h2 id="runner-heading"><TerminalSquare size={19} /> Run Python or JavaScript</h2></div>
          <span className={`runner-status runner-status-${runnerStatus}`}>{runnerStatus.replaceAll("_", " ")}</span>
        </div>
        <p className="runner-disclaimer" role="status">{!runnerConfigChecked ? "Checking isolated runner availability…" : runnerConfigured ? "The isolated runner is configured. Sign in to run code; execution happens in a separate sandbox." : "The isolated runner is not configured yet. Browser HTML/CSS/JavaScript preview remains available; server-side execution is disabled until a secure runner is deployed."}</p>
        <div className="runner-controls">
          <label>Language<select value={runnerLanguage} onChange={(event) => { const language = event.target.value; setRunnerLanguage(language); setRunnerSource(language === "python" ? "name = input('What is your name? ')\nprint(f'Hello, {name}!')" : "console.log('Hello from CodeLeaf!');"); setRunnerResult(null); setRunnerStatus("idle"); }}><option value="python">Python 3</option><option value="javascript">JavaScript (Node.js)</option></select></label>
          <label>Program<textarea value={runnerSource} onChange={(event) => setRunnerSource(event.target.value)} maxLength={16000} rows={8} spellCheck="false" /></label>
          <label>Standard input<textarea value={runnerInput} onChange={(event) => setRunnerInput(event.target.value)} maxLength={8000} rows={3} spellCheck="false" /></label>
        </div>
        <div className="runner-actions">
          <button className="button button-primary" onClick={runRemoteCode} disabled={running || !runnerSource.trim() || !runnerConfigChecked || !runnerConfigured}><Play size={14} /> {running ? "Working…" : "Run isolated code"}</button>
          <button className="button button-secondary" onClick={checkRunnerStatus} disabled={running || !runnerResult?.job_id}>Check status</button>
          <button className="button button-secondary" onClick={cancelRunnerJob} disabled={running || !runnerResult?.job_id || FINAL_RUNNER_STATES.has(runnerStatus)}>Cancel job</button>
        </div>
        {runnerMessage && <p className="runner-message" role="status">{runnerMessage}</p>}
        {runnerResult && <div className="runner-output" aria-live="polite"><div><strong>stdout</strong><pre>{runnerResult.stdout || "(empty)"}</pre></div><div><strong>stderr / result</strong><pre>{runnerResult.stderr || runnerResult.error || runnerResult.message || "(empty)"}</pre></div>{runnerResult.exit_code !== undefined && <p>Exit code: {runnerResult.exit_code}</p>}{runnerResult.job_id && <small>Job ID: {runnerResult.job_id}</small>}</div>}
      </section>
    </PageShell>
  );
}
