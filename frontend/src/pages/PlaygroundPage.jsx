import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Check, Copy, Download, FileCode2, FilePlus2, FolderOpen, Monitor, Play, RotateCcw, Save, ShieldCheck, TerminalSquare, Trash2, Upload, X } from "lucide-react";
import { PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import { createBrowserDocument, defaultSourceForLanguage, getLanguageForFilename, isBrowserWorkspace, resolveLanguage, safeWorkspaceFilename, starterFiles } from "../lib/languageWorkspace.js";

const WORKSPACE_SEED_PREFIX = "codeleaf:workspace-seed:";
const WORKSPACE_PREFIX = "codeleaf:workspace:";
const FINAL_RUNNER_STATES = new Set(["completed", "failed", "timeout", "output_limit", "cancelled", "expired"]);

function safeParse(raw, fallback = null) { try { return JSON.parse(raw); } catch { return fallback; } }
function readSeed(id) {
  if (!id || typeof window === "undefined") return null;
  const value = safeParse(window.localStorage.getItem(`${WORKSPACE_SEED_PREFIX}${id}`));
  return value && typeof value === "object" ? value : null;
}
async function responsePayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || payload.message || `Request failed (${response.status})`);
  return payload;
}
function makeId(name) { return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}-${name}`; }
function downloadText(filename, text, type = "text/plain;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
function initialWorkspace(seed, languageFromUrl) {
  if (Array.isArray(seed?.files) && seed.files.length) return seed.files.map((file) => ({ id: makeId(file.name), name: file.name, language: file.language || getLanguageForFilename(file.name).key, content: String(file.content || "") }));
  return starterFiles({
    courseSlug: seed?.courseSlug || languageFromUrl || "html",
    codeLanguage: seed?.language || languageFromUrl || "html",
    source: seed?.code || "",
    title: seed?.title || "",
  });
}

export default function PlaygroundPage() {
  const [searchParams] = useSearchParams();
  const seedId = searchParams.get("seed") || "";
  const requestedLanguage = searchParams.get("language") || "html";
  const seed = useMemo(() => readSeed(seedId), [seedId]);
  const workspaceId = seedId || "main";
  const workspaceKey = `${WORKSPACE_PREFIX}${workspaceId}`;
  const [files, setFiles] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = safeParse(window.localStorage.getItem(workspaceKey));
      if (Array.isArray(saved) && saved.length) return saved;
    }
    return initialWorkspace(seed, requestedLanguage);
  });
  const [activeId, setActiveId] = useState(() => files[0]?.id || "");
  const [showNewFile, setShowNewFile] = useState(false);
  const [newFileName, setNewFileName] = useState("");
  const [renameId, setRenameId] = useState("");
  const [renameValue, setRenameValue] = useState("");
  const [notice, setNotice] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [runnerStatus, setRunnerStatus] = useState("idle");
  const [runnerResult, setRunnerResult] = useState(null);
  const [runnerMessage, setRunnerMessage] = useState("");
  const [runnerInput, setRunnerInput] = useState("");
  const [running, setRunning] = useState(false);
  const [lastSaved, setLastSaved] = useState("Not saved yet");
  const activeFile = files.find((file) => file.id === activeId) || files[0] || null;
  const browserWorkspace = isBrowserWorkspace(files);
  const activeIsBrowserPreview = Boolean(activeFile && (/\.html?$/i.test(activeFile.name) || /\.css$/i.test(activeFile.name) || (browserWorkspace && /\.(js|mjs|cjs)$/i.test(activeFile.name))));
  const previewDocument = useMemo(() => createBrowserDocument(files), [files, refresh]);
  const activeLanguage = getLanguageForFilename(activeFile?.name || "");
  const canRunActiveFile = activeIsBrowserPreview || ["runner-python", "runner-javascript"].includes(activeLanguage.execution);
  const runButtonHelp = canRunActiveFile ? undefined : `${activeLanguage.label} can be edited and exported, but its isolated runtime is not configured yet.`;

  useEffect(() => {
    if (!activeId && files[0]) setActiveId(files[0].id);
  }, [activeId, files]);
  useEffect(() => {
    if (!seedId || !seed) return;
    const key = `${WORKSPACE_SEED_PREFIX}${seedId}`;
    // The seed is removed only after this workspace has mounted; the URL itself contains no source code.
    window.localStorage.removeItem(key);
  }, [seedId, seed]);
  useEffect(() => {
    try {
      window.localStorage.setItem(workspaceKey, JSON.stringify(files));
      setLastSaved(new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
    } catch {
      setNotice("Browser storage is full or unavailable. Download the project JSON to keep a copy.");
    }
  }, [files, workspaceKey]);

  function updateActiveFile(content) {
    if (!activeFile) return;
    setFiles((old) => old.map((file) => file.id === activeFile.id ? { ...file, content } : file));
    setRunnerResult(null); setRunnerMessage(""); setNotice("");
  }
  function addFile(event) {
    event?.preventDefault();
    const name = newFileName.trim();
    if (!safeWorkspaceFilename(name)) { setNotice("Enter a valid file name including its extension. Path separators and unsafe names are not allowed."); return; }
    if (files.some((file) => file.name.toLowerCase() === name.toLowerCase())) { setNotice("A file with that name already exists."); return; }
    const language = getLanguageForFilename(name);
    const file = { id: makeId(name), name, language: language.key, content: defaultSourceForLanguage(language.key) };
    setFiles((old) => [...old, file]); setActiveId(file.id); setNewFileName(""); setShowNewFile(false); setNotice(`${name} created.`);
  }
  function startRename(file) { setRenameId(file.id); setRenameValue(file.name); setNotice(""); }
  function saveRename(event, file) {
    event.preventDefault(); const name = renameValue.trim();
    if (!safeWorkspaceFilename(name)) { setNotice("Enter a valid file name including its extension."); return; }
    if (files.some((other) => other.id !== file.id && other.name.toLowerCase() === name.toLowerCase())) { setNotice("A file with that name already exists."); return; }
    setFiles((old) => old.map((item) => item.id === file.id ? { ...item, name, language: getLanguageForFilename(name).key } : item));
    setRenameId(""); setNotice(`File renamed to ${name}.`);
  }
  function deleteFile(file) {
    if (files.length <= 1) { setNotice("Keep at least one file in your workspace."); return; }
    if (!window.confirm(`Delete ${file.name} from this browser workspace?`)) return;
    const next = files.filter((item) => item.id !== file.id); setFiles(next);
    if (activeId === file.id) setActiveId(next[0]?.id || "");
    setNotice(`${file.name} deleted from this workspace.`);
  }
  function resetWorkspace() {
    if (!window.confirm("Reset all workspace files to the original starter? Your current browser draft will be replaced.")) return;
    const next = initialWorkspace(seed, requestedLanguage); setFiles(next); setActiveId(next[0]?.id || ""); setRunnerResult(null); setRunnerMessage(""); setNotice("Workspace reset to its starter files.");
  }
  function exportProject() {
    downloadText("codeleaf-workspace.json", JSON.stringify({ format: "codeleaf-workspace-v1", files: files.map(({ name, language, content }) => ({ name, language, content })) }, null, 2), "application/json;charset=utf-8");
  }
  async function importProject(event) {
    const picked = event.target.files?.[0]; event.target.value = "";
    if (!picked) return;
    try {
      if (picked.size > 2_000_000) throw new Error("Workspace imports are limited to 2 MB.");
      const payload = safeParse(await picked.text());
      const incoming = Array.isArray(payload) ? payload : payload?.files;
      if (!Array.isArray(incoming) || !incoming.length || incoming.length > 100) throw new Error("Choose a CodeLeaf workspace JSON containing 1–100 files.");
      const seen = new Set();
      const parsed = incoming.map((file) => {
        if (!safeWorkspaceFilename(file?.name) || seen.has(file.name.toLowerCase())) throw new Error("The workspace contains an invalid or duplicate file name.");
        seen.add(file.name.toLowerCase());
        const content = String(file.content ?? "");
        if (content.length > 1_000_000) throw new Error(`${file.name} is too large to import.`);
        return { id: makeId(file.name), name: file.name, language: getLanguageForFilename(file.name).key, content };
      });
      setFiles(parsed); setActiveId(parsed[0].id); setNotice(`Imported ${parsed.length} file(s).`); setRunnerResult(null); setRunnerMessage("");
    } catch (err) { setNotice(err.message || "Could not import that workspace file."); }
  }

  async function runRemoteFile() {
    if (!activeFile) return;
    const language = getLanguageForFilename(activeFile.name);
    if (!["python", "javascript"].includes(language.key)) {
      setRunnerStatus("unsupported"); setRunnerMessage(`${language.label} files are editable and downloadable, but an isolated ${language.label} runtime is not configured. CodeLeaf did not execute this file.`); setRunnerResult(null); return;
    }
    setRunning(true); setRunnerMessage(""); setRunnerResult(null); setRunnerStatus("submitting");
    try {
      const created = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ language: language.key, source: activeFile.content, stdin: runnerInput }) }));
      const jobId = created.job?.id;
      if (!jobId) throw new Error("The API did not return a valid job reference.");
      for (let attempt = 0; attempt < 12; attempt += 1) {
        const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(jobId)}`));
        const job = payload.job || {}; setRunnerStatus(job.status || "unknown");
        if (FINAL_RUNNER_STATES.has(job.status)) { setRunnerResult({ ...(job.result || {}), job_id: jobId }); return; }
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      setRunnerStatus("running"); setRunnerResult({ job_id: jobId, message: "The job is still running. Use Check status to retrieve the latest result." });
    } catch (err) { setRunnerStatus("unavailable"); setRunnerMessage(err.message || "The isolated runner is unavailable."); }
    finally { setRunning(false); }
  }
  async function checkRunnerStatus() {
    if (!runnerResult?.job_id || running) return;
    setRunning(true); setRunnerMessage("");
    try {
      const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(runnerResult.job_id)}`));
      const job = payload.job || {}; setRunnerStatus(job.status || "unknown"); setRunnerResult({ ...(job.result || {}), job_id: runnerResult.job_id });
      if (!FINAL_RUNNER_STATES.has(job.status)) setRunnerMessage("The job is still running.");
    } catch (err) { setRunnerMessage(err.message || "Could not retrieve runner status."); }
    finally { setRunning(false); }
  }
  function runWorkspace() {
    setRunnerMessage(""); setRunnerResult(null);
    if (activeIsBrowserPreview) { setRefresh((value) => value + 1); setRunnerStatus("preview"); return; }
    void runRemoteFile();
  }

  return (
    <PageShell className="playground-page workspace-page">
      <div className="playground-heading workspace-heading">
        <div><div className="eyebrow">CODELEAF WORKSPACE</div><h1>Build anything, file by file.</h1><p>A persistent, multi-file browser workspace. Add any file extension, rename or remove files, and export/import a workspace. Browser preview and server execution are intentionally separate.</p></div>
        <div className="workspace-heading-actions">
          <label className="button button-secondary button-small workspace-import-label"><Upload size={14} /> Import project<input type="file" accept=".json,application/json" onChange={importProject} hidden /></label>
          <button type="button" className="button button-secondary button-small" onClick={exportProject}><Download size={14} /> Export project</button>
          <button type="button" className="button button-secondary button-small" onClick={resetWorkspace}><RotateCcw size={14} /> Reset</button>
        </div>
      </div>
      <div className="workspace-save-line"><span><Save size={13} /> Auto-saved in this browser at {lastSaved}</span><span>Files are not uploaded to your CodeLeaf account.</span></div>
      {notice && <p className="workspace-notice" role="status"><Check size={14} /> {notice}</p>}
      <div className="ide-workspace panel">
        <aside className="ide-file-explorer" aria-label="Workspace files">
          <div className="ide-explorer-heading"><span><FolderOpen size={15} /> EXPLORER</span><button type="button" title="Create file" aria-label="Create file" onClick={() => { setShowNewFile((value) => !value); setNotice(""); }}><FilePlus2 size={16} /></button></div>
          {showNewFile && <form className="ide-new-file" onSubmit={addFile}><input autoFocus value={newFileName} onChange={(event) => setNewFileName(event.target.value)} placeholder="example.py" aria-label="New file name" maxLength={100} /><button type="submit" aria-label="Create file"><Check size={14} /></button><button type="button" aria-label="Cancel create file" onClick={() => { setShowNewFile(false); setNewFileName(""); }}><X size={14} /></button></form>}
          <div className="ide-file-list">{files.map((file) => <div key={file.id} className={`ide-file-row ${file.id === activeId ? "active" : ""}`}>
            {renameId === file.id ? <form className="ide-rename-form" onSubmit={(event) => saveRename(event, file)}><input autoFocus value={renameValue} onChange={(event) => setRenameValue(event.target.value)} aria-label={`Rename ${file.name}`} maxLength={100} /><button type="submit" aria-label="Save new file name"><Check size={13} /></button><button type="button" onClick={() => setRenameId("")} aria-label="Cancel rename"><X size={13} /></button></form> : <><button type="button" className="ide-file-select" onClick={() => { setActiveId(file.id); setNotice(""); }}><FileCode2 size={14} /><span>{file.name}</span></button><div className="ide-file-tools"><button type="button" title={`Rename ${file.name}`} aria-label={`Rename ${file.name}`} onClick={() => startRename(file)}>✎</button><button type="button" title={`Delete ${file.name}`} aria-label={`Delete ${file.name}`} disabled={files.length <= 1} onClick={() => deleteFile(file)}><Trash2 size={12} /></button></div></>}
          </div>)}</div>
          <div className="ide-explorer-footer"><span>{files.length} file{files.length === 1 ? "" : "s"}</span><button type="button" onClick={() => setShowNewFile(true)}><FilePlus2 size={12} /> New file</button></div>
        </aside>
        <section className="ide-editor-pane">
          <div className="ide-editor-toolbar"><div className="ide-active-tab"><FileCode2 size={14} /><span>{activeFile?.name || "No file selected"}</span></div><div className="ide-editor-actions"><button type="button" onClick={() => navigator.clipboard?.writeText(activeFile?.content || "").catch(() => {})} disabled={!activeFile}><Copy size={13} /> Copy</button><button type="button" onClick={() => activeFile && downloadText(activeFile.name, activeFile.content)} disabled={!activeFile}><Download size={13} /> Download</button><button type="button" className="button button-primary button-small" onClick={runWorkspace} disabled={running || !activeFile || !canRunActiveFile} title={runButtonHelp} aria-label={runButtonHelp || (activeIsBrowserPreview ? "Run browser preview" : "Run file in isolated runner")}><Play size={13} fill="currentColor" /> {running ? "Running…" : activeIsBrowserPreview ? "Run preview" : "Run file"}</button></div></div>
          <label htmlFor="ide-active-code" className="sr-only">Edit {activeFile?.name || "code"}</label>
          <textarea id="ide-active-code" className="ide-code-editor" spellCheck="false" value={activeFile?.content || ""} onChange={(event) => updateActiveFile(event.target.value)} disabled={!activeFile} />
          <div className="ide-status-bar"><span><span className="live-dot" /> {activeLanguage.label}</span><span>UTF-8</span><span>LF</span><span>{(activeFile?.content || "").split("\n").length} lines</span></div>
        </section>
        <section className="ide-result-pane" aria-label={activeIsBrowserPreview ? "Browser preview" : "Execution output"}>
          <div className="ide-result-toolbar"><span>{activeIsBrowserPreview ? <><Monitor size={14} /> Browser preview</> : <><TerminalSquare size={14} /> Output</>}</span><span>{activeIsBrowserPreview ? "Restricted iframe" : runnerStatus.replaceAll("_", " ")}</span>{activeIsBrowserPreview && <button type="button" onClick={() => setRefresh((value) => value + 1)}><RotateCcw size={12} /> Refresh</button>}</div>
          {activeIsBrowserPreview ? <iframe key={refresh} title="CodeLeaf workspace preview" sandbox="allow-scripts" srcDoc={previewDocument} /> : <div className="ide-terminal-output" aria-live="polite"><p className="ide-execution-note"><ShieldCheck size={16} /> {activeLanguage.execution === "runner-python" || activeLanguage.execution === "runner-javascript" ? "Execution is sent only to the separately configured runner. This app server never executes learner code." : `${activeLanguage.label} is available for editing/export, but its isolated runtime is not configured yet.`}</p>{runnerMessage && <p className="phase5-alert">{runnerMessage}</p>}{runnerResult ? <><strong>stdout</strong><pre>{runnerResult.stdout || runnerResult.message || "(empty)"}</pre><strong>stderr / result</strong><pre>{runnerResult.stderr || runnerResult.error || "(empty)"}</pre>{runnerResult.exit_code !== undefined && <p>Exit code: {runnerResult.exit_code}</p>}</> : <p className="ide-terminal-placeholder">Run the selected file to see output here.</p>}{runnerResult?.job_id && !FINAL_RUNNER_STATES.has(runnerStatus) && <button type="button" className="button button-secondary button-small" onClick={checkRunnerStatus} disabled={running}>Check job status</button>}{["python", "javascript"].includes(activeLanguage.key) && <label className="ide-stdin">Standard input <textarea value={runnerInput} onChange={(event) => setRunnerInput(event.target.value)} rows={2} maxLength={8000} placeholder="Optional stdin" /></label>}</div>}
        </section>
      </div>
      <div className="playground-note"><ShieldCheck size={16} /><span>HTML/CSS previews run in a sandboxed iframe with a restrictive Content Security Policy. Only Python and JavaScript have runner adapters; other languages are not simulated or executed until a matching isolated runtime is deployed. Do not store secrets in a browser workspace.</span></div>
    </PageShell>
  );
}
