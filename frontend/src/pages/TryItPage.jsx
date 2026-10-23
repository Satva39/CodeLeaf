import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeft, Copy, Download, ExternalLink, Play, RotateCcw, ShieldCheck, TerminalSquare } from "lucide-react";
import { PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import { createBrowserDocument, defaultSourceForLanguage, resolveLanguage, starterFiles } from "../lib/languageWorkspace.js";

const TERMINAL_STATES = new Set(["completed", "failed", "timeout", "output_limit", "cancelled", "expired"]);

async function readPayload(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || `Request failed (${response.status})`);
  return data;
}

function readSeed(id) {
  if (!id || typeof window === "undefined") return null;
  const key = `codeleaf:workspace-seed:${id}`;
  try {
    const value = JSON.parse(window.localStorage.getItem(key) || "null");
    return value && typeof value === "object" ? value : null;
  } catch { return null; }
}

function outputText(value) {
  if (value === null || value === undefined) return "";
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

export default function TryItPage() {
  const { courseSlug = "html", lessonSlug = "" } = useParams();
  const [searchParams] = useSearchParams();
  const seedId = searchParams.get("seed") || "";
  const seeded = useMemo(() => readSeed(seedId), [seedId]);
  const [loading, setLoading] = useState(!seeded && Boolean(lessonSlug));
  const [error, setError] = useState("");
  const [title, setTitle] = useState(seeded?.title || "Try it yourself");
  const [course, setCourse] = useState(seeded?.courseSlug || courseSlug);
  const [codeLanguage, setCodeLanguage] = useState(seeded?.language || "");
  const [code, setCode] = useState(seeded?.code || "");
  const [expectedOutput, setExpectedOutput] = useState(seeded?.expectedOutput || "");
  const [runMode, setRunMode] = useState(seeded?.runMode || "");
  const [runCount, setRunCount] = useState(0);
  const [result, setResult] = useState(null);
  const [runnerStatus, setRunnerStatus] = useState("idle");
  const [runnerMessage, setRunnerMessage] = useState("");
  const [running, setRunning] = useState(false);
  const [stdin, setStdin] = useState("");
  const frameRef = useRef(null);

  useEffect(() => {
    if (seeded) {
      setTitle(seeded.title || "Try it yourself");
      setCourse(seeded.courseSlug || courseSlug);
      setCodeLanguage(seeded.language || "");
      setCode(seeded.code || "");
      setExpectedOutput(seeded.expectedOutput || "");
      setRunMode(seeded.runMode || "");
      try { window.localStorage.removeItem(`codeleaf:workspace-seed:${seedId}`); } catch { /* local storage may be blocked */ }
      setLoading(false);
      return;
    }
    if (!lessonSlug) {
      const language = resolveLanguage(courseSlug);
      setCodeLanguage(language.key);
      setCode(defaultSourceForLanguage(language.key));
      setTitle(`${language.label} playground`);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    apiFetch(`${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(lessonSlug)}`, { signal: controller.signal })
      .then(readPayload)
      .then((lesson) => {
        const blocks = Array.isArray(lesson?.content?.content_blocks) ? lesson.content.content_blocks : [];
        const block = blocks.find((item) => String(item?.type || "").toLowerCase().replaceAll("-", "_") === "code");
        const language = resolveLanguage(courseSlug, block?.language || "");
        setTitle(lesson.title || "Try it yourself");
        setCourse(courseSlug);
        setCodeLanguage(language.key);
        setCode(block?.code || defaultSourceForLanguage(language.key));
        setExpectedOutput(block?.expected_output || block?.output || lesson?.content?.expected_output || "");
        setRunMode(lesson?.content?.run_mode || "");
      })
      .catch((err) => {
        if (err.name !== "AbortError") {
          const language = resolveLanguage(courseSlug);
          setCodeLanguage(language.key);
          setCode(defaultSourceForLanguage(language.key));
          setTitle("Try it yourself");
          setError(err.message || "Could not load this lesson's example. A language starter is shown instead.");
        }
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [seedId, seeded, courseSlug, lessonSlug]);

  const language = resolveLanguage(course, codeLanguage);
  const isBrowser = language.execution === "browser-html";
  const browserFiles = starterFiles({ courseSlug: course, codeLanguage: language.key, source: code, title });
  const doc = useMemo(() => createBrowserDocument(browserFiles), [code, course, language.key, title]);

  useEffect(() => {
    function receive(event) {
      if (event.source !== frameRef.current?.contentWindow || event.data?.source !== "codeleaf-try-output") return;
      setResult({ kind: "browser", stdout: outputText(event.data.output), stderr: event.data.error || "", exit_code: event.data.error ? 1 : 0 });
    }
    window.addEventListener("message", receive);
    return () => window.removeEventListener("message", receive);
  }, []);

  async function runIsolated() {
    if (!["python", "javascript"].includes(language.key)) {
      setRunnerStatus("unsupported");
      setRunnerMessage(`${language.label} is editable and downloadable, but its isolated runtime is not configured yet. CodeLeaf has not executed this code.`);
      setResult(null);
      return;
    }
    setRunning(true); setRunnerMessage(""); setResult(null); setRunnerStatus("submitting");
    try {
      const created = await readPayload(await apiFetch(`${API_BASE}/api/runner/jobs`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: language.key, source: code, stdin }),
      }));
      const jobId = created.job?.id;
      if (!jobId) throw new Error("The API did not return a runner job ID.");
      for (let attempt = 0; attempt < 12; attempt += 1) {
        const payload = await readPayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(jobId)}`));
        const job = payload.job || {};
        setRunnerStatus(job.status || "unknown");
        if (TERMINAL_STATES.has(job.status)) {
          setResult({ kind: "runner", ...(job.result || {}), job_id: jobId });
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      setRunnerStatus("running");
      setResult({ kind: "runner", job_id: jobId, message: "The job is still running. Open the Playground to check the latest status." });
    } catch (err) {
      setRunnerStatus("unavailable");
      setRunnerMessage(err.message || "The isolated runner is unavailable.");
    } finally { setRunning(false); }
  }

  function runExample() {
    setResult(null); setRunnerMessage("");
    if (isBrowser) {
      setRunCount((value) => value + 1);
      setRunnerStatus("preview");
      return;
    }
    void runIsolated();
  }

  function resetExample() {
    setCode(defaultSourceForLanguage(language.key)); setResult(null); setRunnerMessage(""); setRunnerStatus("idle"); setRunCount((value) => value + 1);
  }

  function downloadExample() {
    const file = starterFiles({ courseSlug: course, codeLanguage: language.key, source: code, title })[0];
    const blob = new Blob([code], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = file?.name || language.filename; anchor.click();
    URL.revokeObjectURL(url);
  }

  const filename = starterFiles({ courseSlug: course, codeLanguage: language.key, source: code, title })[0]?.name || language.filename;

  return (
    <PageShell className="tryit-page">
      <div className="tryit-heading">
        <div>
          <Link to={lessonSlug ? `/learn/${course}/${lessonSlug}` : "/playground"} className="text-link"><ArrowLeft size={14} /> {lessonSlug ? "Back to lesson" : "Back to Playground"}</Link>
          <div className="eyebrow">CODELEAF TRY-IT WORKSPACE</div>
          <h1>{title}</h1>
          <p>Edit the example, run it in the appropriate sandbox, and compare the result. This workspace is separate from the lesson content.</p>
        </div>
        <span className="tryit-language-pill">{language.label} · {filename}</span>
      </div>
      {error && <p className="phase5-alert" role="status">{error}</p>}
      {loading ? <div className="panel tryit-loading">Loading example…</div> : (
        <div className={`tryit-workspace ${isBrowser ? "tryit-browser-workspace" : "tryit-code-workspace"}`}>
          <section className="tryit-editor-panel panel">
            <div className="tryit-toolbar">
              <span><TerminalSquare size={15} /> {filename}</span>
              <div className="tryit-actions">
                <button type="button" onClick={() => navigator.clipboard?.writeText(code).catch(() => {})}><Copy size={13} /> Copy</button>
                <button type="button" onClick={downloadExample}><Download size={13} /> Download</button>
                <button type="button" onClick={resetExample}><RotateCcw size={13} /> Reset</button>
                <button type="button" className="button button-primary button-small" disabled={running || !code.trim()} onClick={runExample}><Play size={13} /> {running ? "Running…" : isBrowser ? "Run" : "Run code"}</button>
              </div>
            </div>
            <textarea className="tryit-code-editor" aria-label={`${filename} source code`} value={code} onChange={(event) => { setCode(event.target.value); setResult(null); setRunnerMessage(""); }} spellCheck="false" maxLength={100000} />
            {!isBrowser && ["python", "javascript"].includes(language.key) && <label className="tryit-stdin">Standard input <textarea value={stdin} onChange={(event) => setStdin(event.target.value)} rows={2} maxLength={8000} placeholder="Input provided to your program" /></label>}
            <div className="tryit-status"><span><span className="live-dot" /> {runnerStatus.replaceAll("_", " ")}</span><span>Local draft · independent from lesson code</span></div>
          </section>
          <section className="tryit-result-panel panel" aria-labelledby="tryit-result-title">
            <div className="tryit-result-heading"><h2 id="tryit-result-title">{isBrowser ? "Live result" : "Program output"}</h2><span>{isBrowser ? "Sandboxed browser preview" : "Isolated runner only"}</span></div>
            {isBrowser ? <iframe key={`${runCount}-${language.key}`} ref={frameRef} title="Try-it browser result" sandbox="allow-scripts" srcDoc={doc} /> : result ? <div className="tryit-console" aria-live="polite"><strong>stdout</strong><pre>{result.stdout || "(empty)"}</pre><strong>stderr / result</strong><pre>{result.stderr || result.error || result.message || "(empty)"}</pre>{result.exit_code !== undefined && <p>Exit code: {result.exit_code}</p>}</div> : <div className="tryit-empty-output"><ShieldCheck size={22} /><h3>Ready to run</h3><p>{["python", "javascript"].includes(language.key) ? "Run submits this program to the separately configured isolated runner." : `${language.label} execution is not configured in the runner yet. Your code stays editable; it will not be simulated as if it ran.`}</p>{expectedOutput && <details><summary>Reference output</summary><pre>{expectedOutput}</pre></details>}</div>}
            {runnerMessage && <p className="runner-message" role="status">{runnerMessage}</p>}
            {!isBrowser && result?.kind === "runner" && expectedOutput && <details className="tryit-expected-output"><summary>Compare with reference output</summary><pre>{expectedOutput}</pre></details>}
          </section>
        </div>
      )}
      <div className="playground-note"><ShieldCheck size={16} /><span>Browser previews use a restricted sandbox and do not share the CodeLeaf app's origin. Server execution is only available for runtimes explicitly supported by the separate runner service.</span></div>
      <div className="tryit-footer-links"><Link to={`/playground?language=${encodeURIComponent(language.key)}`}>Open the full multi-file Playground <ExternalLink size={13} /></Link></div>
    </PageShell>
  );
}
