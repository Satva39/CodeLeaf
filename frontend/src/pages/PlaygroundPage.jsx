import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Code2,
  Download,
  FilePlus2,
  FileCode2,
  FileDown,
  FolderOpen,
  Monitor,
  Play,
  RefreshCw,
  ShieldCheck,
  TerminalSquare,
  Trash2,
  Pencil,
  X,
} from "lucide-react";
import { PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import {
  createBrowserDocument,
  defaultSourceForLanguage,
  getLanguageForFilename,
  isBrowserWorkspace,
  safeWorkspaceFilename,
  starterFiles,
} from "../lib/languageWorkspace.js";

const WORKSPACE_STORAGE_KEY = "codeleaf:playground-workspace:v1";
const FINAL_RUNNER_STATES = new Set(["completed", "failed", "timeout", "output_limit", "cancelled", "expired"]);

async function responsePayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.detail || payload.message || `Request failed (${response.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return payload;
}

function readSeed(id) {
  if (!id || typeof window === "undefined") return null;
  try {
    const value = JSON.parse(window.localStorage.getItem(`codeleaf:workspace-seed:${id}`) || "null");
    return value && typeof value === "object" ? value : null;
  } catch {
    return null;
  }
}

function fileId(name) {
  return typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 9)}-${name}`;
}

function normalizeFiles(value) {
  if (!Array.isArray(value)) return [];
  return value
    .filter((file) => file && typeof file.name === "string" && safeWorkspaceFilename(file.name))
    .slice(0, 100)
    .map((file) => ({
      id: typeof file.id === "string" && file.id ? file.id : fileId(file.name),
      name: file.name,
      language: getLanguageForFilename(file.name).key,
      content: typeof file.content === "string" ? file.content.slice(0, 100_000) : "",
    }));
}

function loadInitialWorkspace(seed, queryLanguage) {
  if (Array.isArray(seed?.files) && seed.files.length) {
    const files = normalizeFiles(seed.files);
    if (files.length) return { files, activeFileId: files.find((file) => file.id === seed.activeFileId)?.id || files[0].id };
  }
  if (seed) {
    const courseSlug = seed.courseSlug || queryLanguage || "html";
    const language = seed.language || seed.codeLanguage || queryLanguage || courseSlug;
    const files = starterFiles({
      courseSlug,
      codeLanguage: language,
      source: typeof seed.code === "string" ? seed.code : typeof seed.source === "string" ? seed.source : "",
      title: seed.title || "",
    });
    return { files, activeFileId: files[0]?.id || "" };
  }
  try {
    const saved = JSON.parse(window.localStorage.getItem(WORKSPACE_STORAGE_KEY) || "null");
    const files = normalizeFiles(saved?.files);
    if (files.length) return { files, activeFileId: files.find((file) => file.id === saved.activeFileId)?.id || files[0].id };
  } catch {
    // A blocked or stale local draft should not prevent opening the editor.
  }
  const language = queryLanguage || "html";
  const files = starterFiles({ courseSlug: language, codeLanguage: language });
  return { files, activeFileId: files[0]?.id || "" };
}

function downloadText(filename, text, type = "text/plain;charset=utf-8") {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export default function PlaygroundPage() {
  const [searchParams] = useSearchParams();
  const seedId = searchParams.get("seed") || "";
  const [seed] = useState(() => readSeed(seedId));
  const [workspace, setWorkspace] = useState(() => loadInitialWorkspace(seed, searchParams.get("language")));
  const [refresh, setRefresh] = useState(0);
  const [browserOutput, setBrowserOutput] = useState([]);
  const [runnerStatus, setRunnerStatus] = useState("idle");
  const [runnerResult, setRunnerResult] = useState(null);
  const [runnerMessage, setRunnerMessage] = useState("");
  const [running, setRunning] = useState(false);
  const [runnerConfigured, setRunnerConfigured] = useState(false);
  const [runnerConfigChecked, setRunnerConfigChecked] = useState(false);
  const [stdin, setStdin] = useState("");
  const [fileDialog, setFileDialog] = useState("");
  const [fileNameDraft, setFileNameDraft] = useState("");
  const [fileDialogError, setFileDialogError] = useState("");
  const [savedWorkspaces, setSavedWorkspaces] = useState([]);
  const [selectedSavedWorkspaceId, setSelectedSavedWorkspaceId] = useState("");
  const [workspaceName, setWorkspaceName] = useState(seed?.title || "My workspace");
  const [workspaceBusy, setWorkspaceBusy] = useState(false);
  const [workspaceNotice, setWorkspaceNotice] = useState("");
  const [workspaceUsage, setWorkspaceUsage] = useState({ used: 0, limit: 3, current_plan: "free" });
  const [savedSnippets, setSavedSnippets] = useState([]);
  const [snippetUsage, setSnippetUsage] = useState({ used: 0, limit: 10 });
  const [snippetName, setSnippetName] = useState("");
  const [selectedSnippetId, setSelectedSnippetId] = useState("");

  const files = workspace.files;
  const activeFile = files.find((file) => file.id === workspace.activeFileId) || files[0] || null;
  const activeLanguage = activeFile ? getLanguageForFilename(activeFile.name) : null;
  const browserProject = isBrowserWorkspace(files);
  const browserActiveFile = Boolean(browserProject && activeFile && /\.(html?|css|m?js|cjs)$/i.test(activeFile.name));
  const browserDocument = useMemo(() => createBrowserDocument(files, "codeleaf-playground-output"), [files, refresh]);

  useEffect(() => {
    if (seedId) {
      try { window.localStorage.removeItem(`codeleaf:workspace-seed:${seedId}`); } catch { /* Storage can be blocked. */ }
    }
  }, [seedId]);

  useEffect(() => {
    try { window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(workspace)); } catch { /* Editing still works without local persistence. */ }
  }, [workspace]);

  async function refreshSavedWorkspaces() {
    try {
      const payload = await responsePayload(await apiFetch(`${API_BASE}/api/me/workspaces`));
      setSavedWorkspaces(Array.isArray(payload.items) ? payload.items : []);
      setWorkspaceUsage(payload.usage || { used: 0, limit: 3, current_plan: payload.current_plan || "free" });
      setSelectedSavedWorkspaceId((current) => current && payload.items?.some((item) => item.id === current) ? current : "");
    } catch (error) {
      const status = Number(error?.status);
      if (status === 401 || /401|unauthorized|not authenticated/i.test(error?.message || "")) {
        setWorkspaceNotice("Sign in to save workspaces to your CodeLeaf account. Your browser draft will continue to auto-save.");
      } else {
        setWorkspaceNotice(error?.message || "Account workspaces could not be loaded.");
      }
    }
  }

  async function refreshSavedSnippets() {
    try {
      const payload = await responsePayload(await apiFetch(`${API_BASE}/api/me/snippets`));
      setSavedSnippets(Array.isArray(payload.items) ? payload.items : []);
      setSnippetUsage(payload.usage || { used: 0, limit: 10 });
      setSelectedSnippetId((current) => current && payload.items?.some((item) => item.id === current) ? current : "");
    } catch (error) {
      if (Number(error?.status) !== 401 && !/401|unauthorized|not authenticated/i.test(error?.message || "")) {
        setWorkspaceNotice(error?.message || "Saved snippets could not be loaded.");
      }
    }
  }

  useEffect(() => {
    void refreshSavedWorkspaces();
    void refreshSavedSnippets();
  }, []);

  async function saveWorkspaceToAccount(createNew = false) {
    const cleanName = workspaceName.trim();
    if (!cleanName) {
      setWorkspaceNotice("Enter a name for this saved workspace.");
      return;
    }
    if (!files.length) {
      setWorkspaceNotice("Add at least one file before saving this workspace.");
      return;
    }
    setWorkspaceBusy(true);
    setWorkspaceNotice("");
    const body = { name: cleanName, language: activeLanguage?.key || "plain", files: files.map(({ id, name, language, content }) => ({ id, name, language, content })) };
    try {
      const isUpdate = !createNew && Boolean(selectedSavedWorkspaceId);
      const response = await apiFetch(`${API_BASE}/api/me/workspaces${isUpdate ? `/${encodeURIComponent(selectedSavedWorkspaceId)}` : ""}`, {
        method: isUpdate ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const payload = await responsePayload(response);
      const saved = payload.workspace;
      if (saved?.id) setSelectedSavedWorkspaceId(saved.id);
      setWorkspaceName(saved?.name || cleanName);
      setWorkspaceNotice(isUpdate ? "Workspace updated in your account." : "Workspace saved to your account.");
      await refreshSavedWorkspaces();
    } catch (error) {
      setWorkspaceNotice(error instanceof Error ? error.message : "Could not save this workspace.");
    } finally {
      setWorkspaceBusy(false);
    }
  }

  async function saveActiveSnippet(createNew = false) {
    if (!activeFile) {
      setWorkspaceNotice("Create or open a file before saving a snippet.");
      return;
    }
    const name = snippetName.trim() || activeFile.name;
    const selected = savedSnippets.find((item) => item.id === selectedSnippetId);
    const update = !createNew && Boolean(selected);
    setWorkspaceBusy(true);
    setWorkspaceNotice("");
    try {
      const response = await apiFetch(`${API_BASE}/api/me/snippets${update ? `/${encodeURIComponent(selectedSnippetId)}` : ""}`, {
        method: update ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, language: activeLanguage?.key || activeFile.language || "plain", code: activeFile.content }),
      });
      const payload = await responsePayload(response);
      const saved = payload.snippet;
      setSnippetName(saved?.name || name);
      if (saved?.id) setSelectedSnippetId(saved.id);
      setWorkspaceNotice(update ? "Snippet updated in your account." : "Snippet saved to your account.");
      await refreshSavedSnippets();
    } catch (error) {
      setWorkspaceNotice(error instanceof Error ? error.message : "Could not save this snippet.");
    } finally {
      setWorkspaceBusy(false);
    }
  }

  function loadSavedSnippet() {
    const saved = savedSnippets.find((item) => item.id === selectedSnippetId);
    if (!saved) {
      setWorkspaceNotice("Choose a saved snippet first.");
      return;
    }
    if (activeFile) {
      setWorkspace((current) => ({ ...current, files: current.files.map((file) => file.id === current.activeFileId ? { ...file, content: saved.code } : file) }));
    } else {
      const language = getLanguageForFilename(saved.name);
      const newFile = { id: fileId(saved.name), name: saved.name, language: language.key, content: saved.code };
      setWorkspace({ files: [newFile], activeFileId: newFile.id });
    }
    setWorkspaceNotice(`Loaded snippet “${saved.name}” into the current file. Save the workspace separately to persist the complete project.`);
    setRunnerResult(null);
    setRunnerStatus("idle");
  }

  async function deleteSavedSnippet() {
    if (!selectedSnippetId) return;
    const selected = savedSnippets.find((item) => item.id === selectedSnippetId);
    if (!window.confirm(`Delete saved snippet “${selected?.name || "snippet"}”?`)) return;
    setWorkspaceBusy(true);
    try {
      await responsePayload(await apiFetch(`${API_BASE}/api/me/snippets/${encodeURIComponent(selectedSnippetId)}`, { method: "DELETE" }));
      setSelectedSnippetId("");
      setSnippetName("");
      setWorkspaceNotice("Saved snippet deleted.");
      await refreshSavedSnippets();
    } catch (error) {
      setWorkspaceNotice(error instanceof Error ? error.message : "Could not delete this snippet.");
    } finally {
      setWorkspaceBusy(false);
    }
  }

  function loadSavedWorkspace() {
    const saved = savedWorkspaces.find((item) => item.id === selectedSavedWorkspaceId);
    if (!saved) {
      setWorkspaceNotice("Choose a saved workspace to load.");
      return;
    }
    const files = normalizeFiles(saved.files);
    if (!files.length) {
      setWorkspaceNotice("This saved workspace has no valid files.");
      return;
    }
    setWorkspace({ files, activeFileId: files[0].id });
    setWorkspaceName(saved.name);
    setWorkspaceNotice(`Loaded “${saved.name}” from your account. Your browser draft now mirrors these files.`);
    setRunnerResult(null);
    setRunnerStatus("idle");
    setBrowserOutput([]);
  }

  async function deleteSavedWorkspace() {
    if (!selectedSavedWorkspaceId) return;
    const selected = savedWorkspaces.find((item) => item.id === selectedSavedWorkspaceId);
    if (!window.confirm(`Delete the saved account workspace “${selected?.name || "workspace"}”? This does not delete your browser draft.`)) return;
    setWorkspaceBusy(true);
    setWorkspaceNotice("");
    try {
      await responsePayload(await apiFetch(`${API_BASE}/api/me/workspaces/${encodeURIComponent(selectedSavedWorkspaceId)}`, { method: "DELETE" }));
      setSelectedSavedWorkspaceId("");
      setWorkspaceNotice("Saved account workspace deleted. Your browser draft remains available.");
      await refreshSavedWorkspaces();
    } catch (error) {
      setWorkspaceNotice(error instanceof Error ? error.message : "Could not delete this workspace.");
    } finally {
      setWorkspaceBusy(false);
    }
  }

  useEffect(() => {
    let active = true;
    async function loadRunnerStatus() {
      try {
        const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/status`));
        if (!active) return;
        setRunnerConfigured(payload.configured === true);
        if (payload.configured !== true) setRunnerMessage(payload.message || "The isolated runner is not configured yet.");
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

  useEffect(() => {
    function receive(event) {
      if (event.source !== document.getElementById("playground-preview-frame")?.contentWindow || event.data?.source !== "codeleaf-playground-output") return;
      const message = event.data.output || event.data.error || "";
      if (message) setBrowserOutput((previous) => [...previous, { kind: event.data.kind || "log", text: String(message) }].slice(-100));
    }
    window.addEventListener("message", receive);
    return () => window.removeEventListener("message", receive);
  }, []);

  function updateActiveContent(value) {
    if (!activeFile) return;
    setWorkspace((current) => ({
      ...current,
      files: current.files.map((file) => file.id === activeFile.id ? { ...file, content: value } : file),
    }));
    setRunnerResult(null);
    setBrowserOutput([]);
  }

  function openNewFileDialog() {
    setFileNameDraft("new-file.txt");
    setFileDialogError("");
    setFileDialog("new");
  }

  function openRenameDialog() {
    if (!activeFile) return;
    setFileNameDraft(activeFile.name);
    setFileDialogError("");
    setFileDialog("rename");
  }

  function submitFileDialog(event) {
    event.preventDefault();
    const name = fileNameDraft.trim();
    if (!safeWorkspaceFilename(name)) {
      setFileDialogError("Use a valid file name with an optional extension. Folder paths and reserved filename characters are not supported.");
      return;
    }
    const duplicate = files.some((file) => file.id !== (fileDialog === "rename" ? activeFile?.id : "") && file.name.toLowerCase() === name.toLowerCase());
    if (duplicate) {
      setFileDialogError("A file with this name already exists.");
      return;
    }
    if (fileDialog === "rename" && activeFile) {
      setWorkspace((current) => ({ ...current, files: current.files.map((file) => file.id === activeFile.id ? { ...file, name, language: getLanguageForFilename(name).key } : file) }));
    } else {
      const language = getLanguageForFilename(name);
      const file = { id: fileId(name), name, language: language.key, content: defaultSourceForLanguage(language.key) };
      setWorkspace((current) => ({ files: [...current.files, file], activeFileId: file.id }));
    }
    setFileDialog("");
    setFileDialogError("");
    setRunnerResult(null);
    setRunnerStatus("idle");
  }

  function deleteActiveFile() {
    if (!activeFile) return;
    if (!window.confirm(`Delete ${activeFile.name} from this local workspace?`)) return;
    setWorkspace((current) => {
      const nextFiles = current.files.filter((file) => file.id !== activeFile.id);
      return { files: nextFiles, activeFileId: nextFiles[0]?.id || "" };
    });
    setRunnerResult(null);
    setRunnerStatus("idle");
    setBrowserOutput([]);
  }

  function downloadActiveFile() {
    if (activeFile) downloadText(activeFile.name, activeFile.content);
  }

  function exportWorkspace() {
    downloadText("codeleaf-workspace.json", JSON.stringify({ version: 1, exportedAt: new Date().toISOString(), files }, null, 2), "application/json;charset=utf-8");
  }

  async function runRemoteCode(language, source) {
    if (!runnerConfigChecked) {
      setRunnerMessage("Checking isolated runner availability. Try again in a moment.");
      return;
    }
    if (!runnerConfigured) {
      setRunnerStatus("unavailable");
      setRunnerMessage("The isolated runner is not configured. Your source remains editable and has not been executed.");
      return;
    }
    setRunning(true);
    setRunnerMessage("");
    setRunnerResult(null);
    setRunnerStatus("submitting");
    try {
      const created = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          language,
          source,
          stdin,
          idempotency_key: typeof crypto !== "undefined" && typeof crypto.randomUUID === "function" ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`,
        }),
      }));
      const jobId = created.job?.id;
      if (!jobId) throw new Error("The API did not return a valid job reference.");
      setRunnerStatus(created.job.status || "queued");
      for (let attempt = 0; attempt < 12; attempt += 1) {
        const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(jobId)}`));
        const result = payload.job || {};
        setRunnerStatus(result.status || "unknown");
        setRunnerResult({ ...(result.result || {}), job_id: jobId });
        if (FINAL_RUNNER_STATES.has(result.status)) return;
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      setRunnerMessage("The job is still running. Use Check status to retrieve the latest result.");
      setRunnerStatus("running");
      setRunnerResult((previous) => ({ ...(previous || {}), job_id: jobId }));
    } catch (error) {
      setRunnerStatus("unavailable");
      setRunnerMessage(error instanceof Error ? error.message : "Could not run the code.");
    } finally {
      setRunning(false);
    }
  }

  async function runCurrentFile() {
    if (!activeFile || !activeFile.content.trim()) {
      setRunnerStatus("idle");
      setRunnerMessage("Create a file and add some code before running it.");
      return;
    }
    setRunnerMessage("");
    setRunnerResult(null);
    if (browserActiveFile) {
      setBrowserOutput([]);
      setRunnerStatus("preview");
      setRefresh((value) => value + 1);
      return;
    }
    if (activeLanguage && ["python", "javascript"].includes(activeLanguage.key)) {
      await runRemoteCode(activeLanguage.key, activeFile.content);
      return;
    }
    setRunnerStatus("unsupported");
    setRunnerMessage(`${activeLanguage?.label || "This file type"} is editable, saveable, and downloadable. Its isolated runtime is not configured, so CodeLeaf has not executed the code.`);
  }

  async function checkRunnerStatus() {
    const jobId = runnerResult?.job_id;
    if (!jobId || running) return;
    setRunning(true);
    setRunnerMessage("");
    try {
      const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(jobId)}`));
      const job = payload.job || {};
      setRunnerStatus(job.status || "unknown");
      setRunnerResult({ ...(job.result || {}), job_id: jobId });
      if (!FINAL_RUNNER_STATES.has(job.status)) setRunnerMessage("This job has not finished yet.");
    } catch (error) {
      setRunnerMessage(error instanceof Error ? error.message : "Could not retrieve job status.");
    } finally { setRunning(false); }
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
    } finally { setRunning(false); }
  }

  const languageLabel = activeLanguage?.label || "Workspace";

  return (
    <PageShell className="playground-page workspace-page">
      <div className="playground-heading workspace-heading">
        <div>
          <div className="eyebrow">CODELEAF WORKSPACE</div>
          <h1>{seed?.title ? `${seed.title} · Playground` : "Try an idea. See what happens."}</h1>
          <p>A personal, multi-file workspace. Create files with any extension, edit them independently, and run only in a runtime CodeLeaf has explicitly configured.</p>
        </div>
        <div className="workspace-primary-actions">
          <button type="button" className="button button-primary" onClick={runCurrentFile} disabled={running}>
            <Play size={15} fill="currentColor" /> {running ? "Running…" : browserActiveFile ? "Run preview" : "Run file"}
          </button>
          <button type="button" className="button button-secondary" onClick={() => { setRefresh((value) => value + 1); setBrowserOutput([]); }} disabled={!browserProject}>
            <RefreshCw size={14} /> Refresh preview
          </button>
        </div>
      </div>

      <div className="workspace-shell panel">
        <aside className="workspace-files" aria-label="Workspace files">
          <div className="workspace-files-heading"><span><FolderOpen size={15} /> EXPLORER</span><button type="button" title="Create file" aria-label="Create file" onClick={openNewFileDialog}><FilePlus2 size={15} /></button></div>
          <div className="workspace-file-list">
            {files.map((file) => (
              <button type="button" key={file.id} className={`workspace-file-entry ${file.id === activeFile?.id ? "active" : ""}`} onClick={() => setWorkspace((current) => ({ ...current, activeFileId: file.id }))} aria-current={file.id === activeFile?.id ? "page" : undefined}>
                <FileCode2 size={14} /><span>{file.name}</span>
              </button>
            ))}
            {!files.length && <p className="workspace-no-files">No files yet. Create your first file.</p>}
          </div>
          <div className="workspace-file-actions">
            <button type="button" onClick={openNewFileDialog}><FilePlus2 size={14} /> New file</button>
            <button type="button" onClick={openRenameDialog} disabled={!activeFile}><Pencil size={14} /> Rename</button>
            <button type="button" onClick={deleteActiveFile} disabled={!activeFile}><Trash2 size={14} /> Delete</button>
          </div>
          <div className="account-workspace-panel">
            <div className="account-workspace-heading"><strong>Account saves</strong><button type="button" title="Refresh saved workspaces" onClick={() => void refreshSavedWorkspaces()} disabled={workspaceBusy}><RefreshCw size={12} /></button></div>
            <small className="account-workspace-usage">{workspaceUsage.used} / {workspaceUsage.limit} workspaces · {workspaceUsage.current_plan || "free"} plan</small>
            <label htmlFor="account-workspace-name">Workspace name</label>
            <input id="account-workspace-name" value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} maxLength={120} placeholder="My workspace" />
            <label htmlFor="account-workspace-select">Saved workspace</label>
            <select id="account-workspace-select" value={selectedSavedWorkspaceId} onChange={(event) => { setSelectedSavedWorkspaceId(event.target.value); const match = savedWorkspaces.find((item) => item.id === event.target.value); if (match) setWorkspaceName(match.name); }}>
              <option value="">Choose a workspace…</option>
              {savedWorkspaces.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <button type="button" onClick={() => void saveWorkspaceToAccount(true)} disabled={workspaceBusy || !files.length}><ShieldCheck size={13} /> {workspaceBusy ? "Saving…" : "Save as new"}</button>
            <button type="button" onClick={() => void saveWorkspaceToAccount(false)} disabled={workspaceBusy || !selectedSavedWorkspaceId}><Pencil size={13} /> Update selected</button>
            <button type="button" onClick={loadSavedWorkspace} disabled={workspaceBusy || !selectedSavedWorkspaceId}><FolderOpen size={13} /> Load selected</button>
            <button type="button" onClick={() => void deleteSavedWorkspace()} disabled={workspaceBusy || !selectedSavedWorkspaceId}><Trash2 size={13} /> Delete saved</button>
            <div className="account-snippet-divider" />
            <div className="account-workspace-heading"><strong>Saved snippets</strong><button type="button" title="Refresh saved snippets" onClick={() => void refreshSavedSnippets()} disabled={workspaceBusy}><RefreshCw size={12} /></button></div>
            <small className="account-workspace-usage">{snippetUsage.used} / {snippetUsage.limit} snippets · included in project storage</small>
            <label htmlFor="account-snippet-name">Snippet name</label>
            <input id="account-snippet-name" value={snippetName} onChange={(event) => setSnippetName(event.target.value)} maxLength={120} placeholder={activeFile?.name || "Reusable code snippet"} />
            <label htmlFor="account-snippet-select">Saved snippet</label>
            <select id="account-snippet-select" value={selectedSnippetId} onChange={(event) => { setSelectedSnippetId(event.target.value); const match = savedSnippets.find((item) => item.id === event.target.value); if (match) setSnippetName(match.name); }}>
              <option value="">Choose a snippet…</option>
              {savedSnippets.map((item) => <option key={item.id} value={item.id}>{item.name} · {item.language}</option>)}
            </select>
            <button type="button" onClick={() => void saveActiveSnippet(true)} disabled={workspaceBusy || !activeFile}><ShieldCheck size={13} /> Save new snippet</button>
            <button type="button" onClick={() => void saveActiveSnippet(false)} disabled={workspaceBusy || !activeFile || !selectedSnippetId}><Pencil size={13} /> Update selected</button>
            <button type="button" onClick={loadSavedSnippet} disabled={workspaceBusy || !selectedSnippetId}><FolderOpen size={13} /> Load into file</button>
            <button type="button" onClick={() => void deleteSavedSnippet()} disabled={workspaceBusy || !selectedSnippetId}><Trash2 size={13} /> Delete snippet</button>
            {workspaceNotice && <p role="status" className="account-workspace-notice">{workspaceNotice}</p>}
          </div>
        </aside>

        <section className="workspace-editor" aria-label="Code editor">
          <div className="workspace-tabbar" role="tablist" aria-label="Open files">
            {files.map((file) => <button type="button" role="tab" aria-selected={file.id === activeFile?.id} key={file.id} className={file.id === activeFile?.id ? "active" : ""} onClick={() => setWorkspace((current) => ({ ...current, activeFileId: file.id }))}><FileCode2 size={13} /> {file.name}</button>)}
            <div className="workspace-tabbar-actions"><button type="button" title="Download active file" aria-label="Download active file" onClick={downloadActiveFile} disabled={!activeFile}><Download size={14} /></button><button type="button" title="Export all files" aria-label="Export all files" onClick={exportWorkspace}><FileDown size={14} /></button></div>
          </div>
          {fileDialog && <form className="workspace-file-dialog" onSubmit={submitFileDialog}>
            <label htmlFor="workspace-filename">{fileDialog === "rename" ? "Rename current file" : "New file name"}</label>
            <input id="workspace-filename" value={fileNameDraft} onChange={(event) => setFileNameDraft(event.target.value)} autoFocus maxLength={100} placeholder="example.py" />
            <button className="button button-primary button-small" type="submit">{fileDialog === "rename" ? "Save name" : "Create file"}</button>
            <button className="workspace-dialog-cancel" type="button" aria-label="Cancel file operation" onClick={() => { setFileDialog(""); setFileDialogError(""); }}><X size={15} /></button>
            {fileDialogError && <p role="alert">{fileDialogError}</p>}
          </form>}
          {activeFile ? <>
            <div className="workspace-editor-label"><span>{activeFile.name}</span><span>{activeLanguage?.label || "Plain text"} · {activeFile.content.length.toLocaleString()} characters</span></div>
            <label htmlFor="workspace-source" className="sr-only">Edit {activeFile.name}</label>
            <textarea id="workspace-source" className="workspace-source" spellCheck="false" autoCapitalize="off" autoCorrect="off" value={activeFile.content} onChange={(event) => updateActiveContent(event.target.value)} maxLength={100_000} />
          </> : <div className="workspace-empty-editor"><FilePlus2 size={24} /><h2>No file selected</h2><p>Create a file to start writing.</p><button type="button" className="button button-primary" onClick={openNewFileDialog}>Create file</button></div>}
          <div className="workspace-statusbar"><span><span className="live-dot" /> {runnerStatus.replaceAll("_", " ")}</span><span>Browser auto-save · account save optional</span><span>{languageLabel}</span></div>
        </section>

        <section className="workspace-output" aria-label="Run result">
          <div className="workspace-output-heading"><span>{browserActiveFile ? <Monitor size={15} /> : <TerminalSquare size={15} />} {browserActiveFile ? "Preview" : "Terminal"}</span><span className={`runner-status runner-status-${runnerStatus}`}>{runnerStatus.replaceAll("_", " ")}</span></div>
          {browserActiveFile ? <>
            <iframe id="playground-preview-frame" key={refresh} title="Playground preview" sandbox="allow-scripts" srcDoc={browserDocument} />
            {!!browserOutput.length && <div className="workspace-console"><strong>Browser console</strong>{browserOutput.map((entry, index) => <pre key={`${index}-${entry.kind}`} className={`console-${entry.kind}`}>{entry.text}</pre>)}</div>}
          </> : runnerResult ? <div className="workspace-terminal" aria-live="polite"><strong>stdout</strong><pre>{runnerResult.stdout || "(empty)"}</pre><strong>stderr / result</strong><pre>{runnerResult.stderr || runnerResult.error || runnerResult.message || "(empty)"}</pre>{runnerResult.exit_code !== undefined && <p>Exit code: {runnerResult.exit_code}</p>}{runnerResult.job_id && <small>Job ID: {runnerResult.job_id}</small>}</div> : activeFile ? <div className="workspace-terminal workspace-terminal-idle" aria-live="polite"><div className="workspace-terminal-prompt"><span>CODELEAF TERMINAL</span><span>{languageLabel}</span></div><pre>{runnerMessage || (activeLanguage && ["python", "javascript"].includes(activeLanguage.key) ? "Ready. Select Run file to execute your program and view stdout/stderr here." : `${languageLabel} uses the terminal-style output panel. CodeLeaf's configured isolated runner currently accepts Python and JavaScript only; this language needs a compatible isolated runtime before it can execute. No output is being fabricated.`)}</pre></div> : <div className="workspace-output-empty"><Code2 size={25} /><h2>Your workspace is empty</h2><p>Create a file in Explorer to get started.</p></div>}
          {runnerMessage && <p className="workspace-runner-message" role="status">{runnerMessage}</p>}
          {runnerResult?.job_id && <div className="workspace-output-actions"><button type="button" className="button button-secondary button-small" onClick={checkRunnerStatus} disabled={running}>Check status</button><button type="button" className="button button-secondary button-small" onClick={cancelRunnerJob} disabled={running || FINAL_RUNNER_STATES.has(runnerStatus)}>Cancel</button></div>}
          {!browserActiveFile && !runnerResult?.job_id && activeFile && ["python", "javascript"].includes(activeLanguage?.key) && <label className="workspace-stdin">Standard input <textarea value={stdin} onChange={(event) => setStdin(event.target.value)} rows={3} maxLength={8000} placeholder="Input provided to your program" /></label>}
        </section>
      </div>

      <div className="playground-note"><ShieldCheck size={16} /><span>Files auto-save in this browser. Use Account saves to persist workspaces and reusable snippets to your signed-in account; these are subject to plan-specific count and storage allowances. HTML previews run in a sandboxed frame with restrictive Content Security Policy. Server-side code is sent only to CodeLeaf's separate isolated runner; unsupported languages are not executed.</span></div>
    </PageShell>
  );
}
