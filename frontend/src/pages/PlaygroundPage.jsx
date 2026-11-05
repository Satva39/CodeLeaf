import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Code2,
  Download,
  FilePlus2,
  FileCode2,
  FileDown,
  FileUp,
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
  createReactPreviewDocument,
  createSassPreviewDocument,
  createAngularJSPreviewDocument,
  detectOutputMode,
  defaultSourceForLanguage,
  getLanguageForFilename,
  safeWorkspaceFilename,
  starterFiles,
} from "../lib/languageWorkspace.js";

const WORKSPACE_STORAGE_KEY = "codeleaf:playground-workspace:v1";
const WORKSPACE_CONFIG_FILE = "__codeleaf_project_config__.json";
const FINAL_RUNNER_STATES = new Set(["completed", "failed", "timeout", "output_limit", "cancelled", "expired"]);
const RUNNER_MAX_FILES = 10;
const RUNNER_MAX_FILE_BYTES = 65_536;
const RUNNER_MAX_TOTAL_BYTES = 131_072;
const RUNNER_DATA_FILE_LANGUAGES = new Set(["json", "xml", "yaml", "markdown", "plain", "excel", "toml"]);
const STRUCTURED_TOOL_LANGUAGES = new Set(["xml", "json", "yaml", "excel", "markdown", "plain", "docker", "aws", "githubactions", "git", "toml", "redis"]);

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
    .filter((file) => file && typeof file.name === "string" && file.name !== WORKSPACE_CONFIG_FILE && safeWorkspaceFilename(file.name))
    .slice(0, 100)
    .map((file) => ({
      id: typeof file.id === "string" && file.id ? file.id : fileId(file.name),
      name: file.name,
      language: getLanguageForFilename(file.name, file.language).key,
      content: typeof file.content === "string" ? file.content.slice(0, 100_000) : "",
    }));
}

function normalizeWorkspace(value) {
  const rawFiles = Array.isArray(value?.files) ? value.files : [];
  const configFile = rawFiles.find((file) => file?.name === WORKSPACE_CONFIG_FILE);
  let savedConfig = null;
  try { savedConfig = configFile?.content ? JSON.parse(configFile.content) : null; } catch { savedConfig = null; }
  const files = normalizeFiles(rawFiles);
  const candidate = value?.webConnection || savedConfig?.webConnection || null;
  const validEntry = files.some((file) => file.name === candidate?.entryFile && /\.html?$/i.test(file.name));
  const validLanguage = files.some((file) => file.name === candidate?.languageFile && getLanguageForFilename(file.name, file.language).key === candidate?.language);
  const webConnection = candidate?.enabled === true && validEntry && validLanguage
    ? { enabled: true, mode: "stdout-bridge", entryFile: candidate.entryFile, languageFile: candidate.languageFile, language: candidate.language }
    : null;
  return { files, webConnection };
}

function savedWorkspaceFiles(files, webConnection) {
  return [
    ...files.map(({ id, name, language, content }) => ({ id, name, language, content })),
    {
      id: fileId(WORKSPACE_CONFIG_FILE),
      name: WORKSPACE_CONFIG_FILE,
      language: "json",
      content: JSON.stringify({ version: 1, webConnection: webConnection || null }),
    },
  ];
}

function loadInitialWorkspace(seed, queryLanguage) {
  if (Array.isArray(seed?.files) && seed.files.length) {
    const parsed = normalizeWorkspace(seed);
    if (parsed.files.length) return { ...parsed, activeFileId: parsed.files.find((file) => file.id === seed.activeFileId)?.id || parsed.files[0].id };
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
    return { files, activeFileId: files[0]?.id || "", webConnection: null };
  }
  try {
    const saved = JSON.parse(window.localStorage.getItem(WORKSPACE_STORAGE_KEY) || "null");
    const parsed = normalizeWorkspace(saved);
    if (parsed.files.length) return { ...parsed, activeFileId: parsed.files.find((file) => file.id === saved.activeFileId)?.id || parsed.files[0].id };
  } catch {
    // A blocked or stale local draft should not prevent opening the editor.
  }
  const language = queryLanguage || "html";
  const files = starterFiles({ courseSlug: language, codeLanguage: language });
  return { files, activeFileId: files[0]?.id || "", webConnection: null };
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
  const [runnerSupportedLanguages, setRunnerSupportedLanguages] = useState([]);
  const [runnerConfigChecked, setRunnerConfigChecked] = useState(false);
  const [connectedOutput, setConnectedOutput] = useState(null);
  const [connectionEntryDraft, setConnectionEntryDraft] = useState("");
  const [connectionLanguageDraft, setConnectionLanguageDraft] = useState("");
  const [stdin, setStdin] = useState("");
  const [databaseSetupSql, setDatabaseSetupSql] = useState("");
  const [structuredQuery, setStructuredQuery] = useState("");
  const [fileDialog, setFileDialog] = useState("");
  const [fileNameDraft, setFileNameDraft] = useState("");
  const [fileDialogError, setFileDialogError] = useState("");
  const importInputRef = useRef(null);
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
  const activeLanguage = activeFile ? getLanguageForFilename(activeFile.name, activeFile.language) : null;
  const isDatabaseLanguage = ["sqlite", "mysql", "postgresql"].includes(activeLanguage?.key);
  const outputMode = detectOutputMode({ currentFile: activeFile, files, runnerCapabilities: runnerSupportedLanguages, webConnection: workspace.webConnection });
  const isStructuredTool = STRUCTURED_TOOL_LANGUAGES.has(activeLanguage?.key);
  const isConnectedPreview = outputMode.mode === "connected-preview";
  const runnerAvailabilityPending = !isStructuredTool && !runnerConfigChecked
    && (outputMode.mode === "terminal" || outputMode.mode === "connected-preview");
  const isReactPreview = outputMode.mode === "react-preview";
  const isSassPreview = outputMode.mode === "sass-preview";
  const isAngularJSPreview = outputMode.mode === "angularjs-preview";
  const isBrowserPreview = outputMode.mode === "browser-preview" || isConnectedPreview || isSassPreview || isAngularJSPreview;
  const previewEntryFile = files.find((file) => file.name === (outputMode.entryFile || activeFile?.name)) || activeFile;
  const previewHasContent = Boolean(previewEntryFile?.content?.trim());
  const emptyBrowserPreview = !isConnectedPreview && (isBrowserPreview || isReactPreview) && !previewHasContent;
  const connectedExecutionFailed = isConnectedPreview && Boolean(runnerResult?.job_id)
    && (runnerResult.status !== "completed" || (runnerResult.exit_code !== undefined && Number(runnerResult.exit_code) !== 0));
  const connectedRunReady = isConnectedPreview && Boolean(connectedOutput);
  const showPreview = (isBrowserPreview || isReactPreview) && (!isConnectedPreview || connectedRunReady) && !connectedExecutionFailed && !emptyBrowserPreview;
  const browserDocument = useMemo(() => createBrowserDocument(files, "codeleaf-playground-output", {
    entryFile: outputMode.entryFile, activeFileName: activeFile?.name, connectedOutput,
  }), [files, refresh, outputMode.entryFile, activeFile?.name, connectedOutput]);
  const reactDocument = useMemo(() => createReactPreviewDocument(files, outputMode.entryFile || activeFile?.name, "codeleaf-playground-output"), [files, outputMode.entryFile, activeFile?.name, refresh]);
  const sassDocument = useMemo(() => createSassPreviewDocument(
    activeFile?.content || "",
    "codeleaf-playground-output",
    String(activeFile?.name || "").toLowerCase().endsWith(".sass") ? "indented" : "scss",
  ), [activeFile?.content, activeFile?.name, refresh]);
  const angularJSPreviewDocument = useMemo(() => createAngularJSPreviewDocument(
    activeFile?.content || "",
    "codeleaf-playground-output",
  ), [activeFile?.content, refresh]);
  const htmlEntryFiles = files.filter((file) => /\.html?$/i.test(file.name));
  const connectableFiles = files.filter((file) => runnerSupportedLanguages.includes(getLanguageForFilename(file.name, file.language).key));

  useEffect(() => {
    setConnectionEntryDraft((current) => htmlEntryFiles.some((file) => file.name === current) ? current : workspace.webConnection?.entryFile || htmlEntryFiles[0]?.name || "");
    setConnectionLanguageDraft((current) => connectableFiles.some((file) => file.name === current) ? current : workspace.webConnection?.languageFile || connectableFiles.find((file) => getLanguageForFilename(file.name, file.language).key === "python")?.name || connectableFiles[0]?.name || "");
  }, [files, workspace.webConnection, runnerSupportedLanguages]);

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
    const body = { name: cleanName, language: activeLanguage?.key || "plain", files: savedWorkspaceFiles(files, workspace.webConnection) };
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
    const parsed = normalizeWorkspace(saved);
    const files = parsed.files;
    if (!files.length) {
      setWorkspaceNotice("This saved workspace has no valid files.");
      return;
    }
    setWorkspace({ ...parsed, activeFileId: files[0].id });
    setConnectedOutput(null);
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
        setRunnerSupportedLanguages(Array.isArray(payload.supported_languages) ? payload.supported_languages.map((item) => String(item).toLowerCase()) : []);
        if (payload.configured !== true) setRunnerMessage(payload.message || "No server-side execution provider is configured yet.");
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
    setConnectedOutput(null);
    setBrowserOutput([]);
  }

  function insertStarterCode() {
    if (!activeFile || !activeLanguage) return;
    const starter = defaultSourceForLanguage(activeLanguage.key);
    if (!starter) return;
    setWorkspace((current) => ({
      ...current,
      files: current.files.map((file) => file.id === activeFile.id ? { ...file, content: starter } : file),
    }));
    setRunnerResult(null);
    setConnectedOutput(null);
    setBrowserOutput([]);
    setRunnerStatus("idle");
    setRunnerMessage("");
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
      setFileDialogError("Use a valid file name with an optional extension. Folder paths, reserved names and reserved filename characters are not supported.");
      return;
    }
    const duplicate = files.some((file) => file.id !== (fileDialog === "rename" ? activeFile?.id : "") && file.name.toLowerCase() === name.toLowerCase());
    if (duplicate) {
      setFileDialogError("A file with this name already exists.");
      return;
    }
    if (fileDialog === "rename" && activeFile) {
      setWorkspace((current) => ({ ...current, files: current.files.map((file) => file.id === activeFile.id ? { ...file, name, language: getLanguageForFilename(name).key } : file), webConnection: current.webConnection && [current.webConnection.entryFile, current.webConnection.languageFile].includes(activeFile.name) ? null : current.webConnection }));
      setConnectedOutput(null);
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
      const webConnection = current.webConnection && [current.webConnection.entryFile, current.webConnection.languageFile].includes(activeFile.name) ? null : current.webConnection;
      return { files: nextFiles, activeFileId: nextFiles[0]?.id || "", webConnection };
    });
    setRunnerResult(null);
    setRunnerStatus("idle");
    setConnectedOutput(null);
    setBrowserOutput([]);
  }

  function downloadActiveFile() {
    if (activeFile) downloadText(activeFile.name, activeFile.content);
  }

  function exportWorkspace() {
    downloadText("codeleaf-workspace.json", JSON.stringify({ version: 1, exportedAt: new Date().toISOString(), files, webConnection: workspace.webConnection || null }, null, 2), "application/json;charset=utf-8");
  }

  async function importWorkspaceFile(event) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) return;
    setWorkspaceNotice("");
    try {
      if (file.size > 2 * 1024 * 1024) {
        throw new Error("Workspace JSON must be 2 MB or smaller.");
      }
      const document = JSON.parse(await file.text());
      if (document?.version !== 1 || !Array.isArray(document.files)) {
        throw new Error("Choose a CodeLeaf workspace JSON exported from the playground.");
      }
      if (document.files.length < 1 || document.files.length > 100) {
        throw new Error("A workspace import must contain between 1 and 100 files.");
      }
      const normalized = [];
      const names = new Set();
      for (const source of document.files) {
        if (source?.name === WORKSPACE_CONFIG_FILE) continue;
        if (!source || typeof source.name !== "string" || !safeWorkspaceFilename(source.name)) {
          throw new Error("The workspace contains an unsafe file path. No files were imported.");
        }
        if (typeof source.content !== "string" || source.content.length > 100_000) {
          throw new Error(`File ${source.name} must contain text of 100,000 characters or less.`);
        }
        const key = source.name.toLowerCase();
        if (names.has(key)) throw new Error(`The workspace contains a duplicate filename: ${source.name}.`);
        names.add(key);
        normalized.push({
          id: fileId(source.name),
          name: source.name,
          language: getLanguageForFilename(source.name, source.language).key,
          content: source.content,
        });
      }
      const candidate = document.webConnection || null;
      const validEntry = normalized.some((item) => item.name === candidate?.entryFile && /\.html?$/i.test(item.name));
      const validLanguage = normalized.some((item) => item.name === candidate?.languageFile && getLanguageForFilename(item.name, item.language).key === candidate?.language);
      const webConnection = candidate?.enabled === true && validEntry && validLanguage
        ? { enabled: true, mode: "stdout-bridge", entryFile: candidate.entryFile, languageFile: candidate.languageFile, language: candidate.language }
        : null;
      setWorkspace({ files: normalized, activeFileId: normalized[0]?.id || "", webConnection });
      setConnectedOutput(null);
      setRunnerResult(null);
      setRunnerStatus("idle");
      setBrowserOutput([]);
      setWorkspaceNotice(`Imported ${normalized.length} file${normalized.length === 1 ? "" : "s"}. Your browser draft is now auto-saved.`);
    } catch (error) {
      setWorkspaceNotice(error instanceof Error ? error.message : "Could not import this workspace.");
    } finally {
      input.value = "";
    }
  }

  async function runRemoteCode(language, source, projectFiles = null, setupSql = "") {
    if (!runnerConfigChecked) {
      setRunnerMessage("Checking execution-provider availability. Try again in a moment.");
      return;
    }
    if (!runnerConfigured) {
      setRunnerStatus("unavailable");
      setRunnerMessage("No server-side execution provider is configured. Your source remains editable and has not been executed.");
      return;
    }
    setRunning(true);
    setRunnerMessage("");
    setRunnerResult(null);
    setRunnerStatus("submitting");
    try {
      const requestBody = {
        language,
        stdin: ["sqlite", "mysql", "postgresql"].includes(language) ? "" : stdin,
        idempotency_key: typeof crypto !== "undefined" && typeof crypto.randomUUID === "function" ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`,
      };
      if (["sqlite", "mysql", "postgresql"].includes(language)) {
        requestBody.setup_sql = setupSql;
      }
      if (Array.isArray(projectFiles) && projectFiles.length > 1) {
        requestBody.files = projectFiles.map((file) => ({ name: file.name, content: file.content }));
      } else {
        requestBody.source = source;
      }
      const created = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      }));
      const jobId = created.job?.id;
      if (!jobId) throw new Error("The API did not return a valid job reference.");
      setRunnerStatus(created.job.status || "queued");
      for (let attempt = 0; attempt < 12; attempt += 1) {
        const payload = await responsePayload(await apiFetch(`${API_BASE}/api/runner/jobs/${encodeURIComponent(jobId)}`));
        const result = payload.job || {};
        setRunnerStatus(result.status || "unknown");
        const completedResult = { ...(result.result || {}), job_id: jobId, status: result.status || "unknown" };
        setRunnerResult(completedResult);
        if (FINAL_RUNNER_STATES.has(result.status)) return completedResult;
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
      setRunnerMessage("The job is still running. Use Check status to retrieve the latest result.");
      setRunnerStatus("running");
      const pendingResult = { job_id: jobId, status: "running" };
      setRunnerResult(pendingResult);
      return pendingResult;
    } catch (error) {
      setRunnerStatus("unavailable");
      setRunnerMessage(error instanceof Error ? error.message : "Could not run the code.");
      return null;
    } finally {
      setRunning(false);
    }
  }

  async function runStructuredTool(language, source, query = "") {
    setRunning(true);
    setRunnerMessage("");
    setRunnerResult(null);
    setRunnerStatus("submitting");
    try {
      const payload = await responsePayload(await apiFetch(`${API_BASE}/api/playground/tools/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language, source, query }),
      }));
      const result = payload.result;
      if (!result || typeof result.success !== "boolean") {
        throw new Error("The Playground tool returned an invalid result.");
      }
      setRunnerResult(result);
      setRunnerStatus(result.success ? "completed" : "failed");
      return result;
    } catch (error) {
      setRunnerStatus("failed");
      setRunnerMessage(error instanceof Error ? error.message : "Could not process this file.");
      return null;
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
    if (outputMode.mode === "connected-preview") {
      setConnectedOutput(null);
      const execution = await runRemoteCode(activeLanguage.key, activeFile.content);
      if (!execution) return;
      const succeeded = execution.status === "completed"
        && (execution.exit_code === undefined || Number(execution.exit_code) === 0)
        && !execution.error;
      if (!succeeded) {
        setConnectedOutput(null);
        return;
      }
      setConnectedOutput({
        language: activeLanguage.key,
        stdout: execution.stdout || "",
        stderr: execution.stderr || "",
        exit_code: execution.exit_code ?? 0,
      });
      setRunnerStatus("preview");
      setRefresh((value) => value + 1);
      return;
    }
    if (outputMode.mode === "sass-preview" || outputMode.mode === "angularjs-preview"
      || outputMode.mode === "browser-preview" || outputMode.mode === "react-preview") {
      setBrowserOutput([]);
      setRunnerStatus("preview");
      setRefresh((value) => value + 1);
      return;
    }
    if (STRUCTURED_TOOL_LANGUAGES.has(activeLanguage?.key)) {
      await runStructuredTool(activeLanguage.key, activeFile.content, activeLanguage.key === "xml" ? structuredQuery : "");
      return;
    }
    if (runnerSupportedLanguages.includes(activeLanguage?.key)) {
      if (["sqlite", "mysql", "postgresql"].includes(activeLanguage.key)) {
        await runRemoteCode(activeLanguage.key, activeFile.content, null, databaseSetupSql);
        return;
      }
      // Include source files belonging to the active runtime plus common text/data
      // assets. HTML/CSS/JS preview files are not sent into a terminal job unless
      // they are the active language itself.
      const companionFiles = files.filter((file) => {
        if (!file || typeof file.name !== "string" || !safeWorkspaceFilename(file.name)) return false;
        const key = getLanguageForFilename(file.name, file.language).key;
        if (key === activeLanguage.key || RUNNER_DATA_FILE_LANGUAGES.has(key)) return true;
        if (activeLanguage.key === "cpp" && /\.(?:h|hpp|hh|hxx)$/i.test(file.name)) return true;
        if (activeLanguage.key === "c" && /\.(?:h)$/i.test(file.name)) return true;
        return false;
      });
      const orderedFiles = [activeFile, ...companionFiles.filter((file) => file.id !== activeFile.id)];
      const uniqueFiles = orderedFiles.filter((file, index, all) => all.findIndex((candidate) => candidate.name.toLowerCase() === file.name.toLowerCase()) === index);
      if (uniqueFiles.length > RUNNER_MAX_FILES) {
        setRunnerStatus("unsupported");
        setRunnerMessage(`This project has ${uniqueFiles.length} relevant files. The isolated Runner accepts up to ${RUNNER_MAX_FILES} files per job. Remove unrelated files or run a smaller project.`);
        return;
      }
      const fileSizes = uniqueFiles.map((file) => new Blob([file.content]).size);
      if (fileSizes.some((size) => size > RUNNER_MAX_FILE_BYTES)) {
        setRunnerStatus("unsupported");
        setRunnerMessage("Each source or data file must be 64 KB or smaller for an isolated multi-file run.");
        return;
      }
      if (fileSizes.reduce((sum, size) => sum + size, 0) > RUNNER_MAX_TOTAL_BYTES) {
        setRunnerStatus("unsupported");
        setRunnerMessage("The combined source and data files must be 128 KB or smaller for this isolated run.");
        return;
      }
      await runRemoteCode(activeLanguage.key, activeFile.content, uniqueFiles.length > 1 ? uniqueFiles : null);
      return;
    }
    const environmentGuidance = {
      angular: "Modern Angular is a project framework, not a standalone TypeScript file. It needs an Angular CLI workspace, installed Angular packages, and a project build step; CodeLeaf does not yet have that full project builder configured.",
      asp: "Classic ASP requires a Windows IIS server with its ASP runtime. The current CodeLeaf Runner is Linux/Piston-based, so it cannot execute ASP pages as a normal compiler job.",
      pytorch: "PyTorch is not part of OnlineCompiler's published Python packages, and no PyTorch-enabled Runner image is currently advertised. NumPy, SciPy, scikit-learn and the other documented Python packages use OnlineCompiler's Python runtime.",
    };
    setRunnerStatus("unsupported");
    setRunnerMessage(environmentGuidance[activeLanguage?.key]
      || `No compatible execution adapter is currently available for ${activeLanguage?.label || "this file type"}. The source is unchanged and downloadable; CodeLeaf will not claim it ran.`);
  }

  function connectLanguageToHtml() {
    const entry = htmlEntryFiles.find((file) => file.name === connectionEntryDraft);
    const languageFile = connectableFiles.find((file) => file.name === connectionLanguageDraft);
    if (!entry || !languageFile) {
      setWorkspaceNotice("Choose an existing HTML entry file and a file whose language is supported by the configured runner.");
      return;
    }
    const language = getLanguageForFilename(languageFile.name, languageFile.language).key;
    if (!runnerSupportedLanguages.includes(language)) {
      setWorkspaceNotice(`The configured runner does not currently support ${getLanguageForFilename(languageFile.name).label}.`);
      return;
    }
    setWorkspace((current) => ({ ...current, webConnection: { enabled: true, mode: "stdout-bridge", entryFile: entry.name, languageFile: languageFile.name, language } }));
    setConnectedOutput(null);
    setRunnerResult(null);
    setRunnerStatus("idle");
    setWorkspaceNotice(`${languageFile.name} is connected to ${entry.name}. Run the language file through the configured server-side provider. The preview receives the real result through window.CODELEAF_CONNECTED_OUTPUT and the codeleaf:language-output event.`);
  }

  function removeLanguageConnection() {
    setWorkspace((current) => ({ ...current, webConnection: null }));
    setConnectedOutput(null);
    setRunnerResult(null);
    setRunnerStatus("idle");
    setWorkspaceNotice("The HTML-language connection was removed. The programming file now uses normal terminal execution.");
  }

  function selectWorkspaceFile(file) {
    setWorkspace((current) => ({ ...current, activeFileId: file.id }));
    setConnectedOutput(null);
    setRunnerResult(null);
    setRunnerStatus("idle");
    setRunnerMessage("");
    setBrowserOutput([]);
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
          <button type="button" className="button button-primary" onClick={runCurrentFile} disabled={running || runnerAvailabilityPending}>
            <Play size={15} fill="currentColor" /> {runnerAvailabilityPending ? "Checking…" : running ? "Running…" : showPreview ? "Run preview" : isConnectedPreview ? "Run connected app" : "Run file"}
          </button>
          <button type="button" className="button button-secondary" onClick={() => { setRefresh((value) => value + 1); setBrowserOutput([]); }} disabled={!showPreview}>
            <RefreshCw size={14} /> Refresh preview
          </button>
        </div>
      </div>

      <div className="workspace-shell panel">
        <aside className="workspace-files" aria-label="Workspace files">
          <div className="workspace-files-heading"><span><FolderOpen size={15} /> EXPLORER</span><button type="button" title="Create file" aria-label="Create file" onClick={openNewFileDialog}><FilePlus2 size={15} /></button></div>
          <div className="workspace-file-list">
            {files.map((file) => (
              <button type="button" key={file.id} className={`workspace-file-entry ${file.id === activeFile?.id ? "active" : ""}`} onClick={() => selectWorkspaceFile(file)} aria-current={file.id === activeFile?.id ? "page" : undefined}>
                <FileCode2 size={14} /><span>{file.name}</span>
              </button>
            ))}
            {!files.length && <p className="workspace-no-files">No files yet. Create your first file.</p>}
          </div>
          <div className="workspace-file-actions">
            <button type="button" onClick={() => importInputRef.current?.click()}><FileUp size={14} /> Import project</button>
            <input ref={importInputRef} type="file" accept=".json,application/json" className="sr-only" aria-label="Choose exported CodeLeaf workspace JSON" onChange={importWorkspaceFile} />
            <button type="button" onClick={openNewFileDialog}><FilePlus2 size={14} /> New file</button>
            <button type="button" onClick={openRenameDialog} disabled={!activeFile}><Pencil size={14} /> Rename</button>
            <button type="button" onClick={deleteActiveFile} disabled={!activeFile}><Trash2 size={14} /> Delete</button>
          </div>
          {htmlEntryFiles.length > 0 && <section className="workspace-web-connection" aria-label="HTML project connection">
            <div className="workspace-web-connection-title"><strong>Web project connection</strong><span>{workspace.webConnection ? "Connected" : "Optional"}</span></div>
            <label>HTML entry file<select value={connectionEntryDraft} onChange={(event) => setConnectionEntryDraft(event.target.value)}><option value="">Choose HTML file…</option>{htmlEntryFiles.map((file) => <option key={file.id} value={file.name}>{file.name}</option>)}</select></label>
            <label>Run this file<select value={connectionLanguageDraft} onChange={(event) => setConnectionLanguageDraft(event.target.value)}><option value="">Choose supported file…</option>{connectableFiles.map((file) => <option key={file.id} value={file.name}>{file.name} · {getLanguageForFilename(file.name, file.language).label}</option>)}</select></label>
            <small>Only an explicit connection enables backend output to reach the HTML preview. The selected file still runs on CodeLeaf’s isolated server runner.</small>
            <div className="workspace-web-connection-actions"><button type="button" onClick={connectLanguageToHtml} disabled={!runnerConfigChecked || !runnerConfigured || !connectionEntryDraft || !connectionLanguageDraft}>Connect files</button>{workspace.webConnection && <button type="button" className="is-muted" onClick={removeLanguageConnection}>Remove</button>}</div>
            {workspace.webConnection && <small className="workspace-web-connection-active">{workspace.webConnection.languageFile} → {workspace.webConnection.entryFile}</small>}
            {workspace.webConnection && <small className="workspace-web-connection-help">In your HTML, listen for <code>codeleaf:language-output</code> and read <code>event.detail.stdout</code>. Only the selected server file is executed; the browser never runs Python or another server language.</small>}
            {!runnerConfigured && runnerConfigChecked && <small>Configure a supported backend runner to enable language connections.</small>}
          </section>}

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
            {files.map((file) => <button type="button" role="tab" aria-selected={file.id === activeFile?.id} key={file.id} className={file.id === activeFile?.id ? "active" : ""} onClick={() => selectWorkspaceFile(file)}><FileCode2 size={13} /> {file.name}</button>)}
            <div className="workspace-tabbar-actions"><button type="button" title="Download active file" aria-label="Download active file" onClick={downloadActiveFile} disabled={!activeFile}><Download size={14} /></button><button type="button" title="Export all files" aria-label="Export project" onClick={exportWorkspace}><FileDown size={14} /></button></div>
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
            <textarea
              id="workspace-source"
              className="workspace-source"
              spellCheck="false"
              autoCapitalize="off"
              autoCorrect="off"
              value={activeFile.content}
              onChange={(event) => updateActiveContent(event.target.value)}
              maxLength={100_000}
              placeholder={`This ${activeLanguage?.label || "text"} file is empty. Start typing or insert the starter code.`}
              aria-describedby={!activeFile.content.trim() ? "workspace-empty-code-help" : undefined}
            />
            {!activeFile.content.trim() && <div className="workspace-empty-code-help" id="workspace-empty-code-help">
              <span>This saved file is empty. Your draft has been preserved.</span>
              <button type="button" onClick={insertStarterCode}>Insert starter code</button>
            </div>}
          </> : <div className="workspace-empty-editor"><FilePlus2 size={24} /><h2>No file selected</h2><p>Create a file to start writing.</p><button type="button" className="button button-primary" onClick={openNewFileDialog}>Create file</button></div>}
          <div className="workspace-statusbar"><span><span className="live-dot" /> {runnerStatus.replaceAll("_", " ")}</span><span>Auto-saved in this browser · account save optional</span><span>{languageLabel}</span></div>
        </section>

        <section className="workspace-output" aria-label="Run result">
          <div className="workspace-output-heading"><span>{(showPreview || emptyBrowserPreview) ? <Monitor size={15} /> : <TerminalSquare size={15} />} {(showPreview || emptyBrowserPreview) ? (isReactPreview ? "React Preview" : isSassPreview ? "Sass Preview" : isAngularJSPreview ? "AngularJS Preview" : "Preview") : isStructuredTool ? "Structured / command output" : "Program output"}</span><span className={`runner-status runner-status-${runnerStatus}`}>{runnerStatus.replaceAll("_", " ")}</span></div>
          {isConnectedPreview && !showPreview && !runnerResult?.job_id && <p className="workspace-connected-pending">Run the connected {activeLanguage?.label || "language"} file successfully to start the web preview. No browser preview is shown until the real execution result is available.</p>}
          {activeLanguage?.key === "xml" && <label className="workspace-stdin">Optional XPath query <input value={structuredQuery} onChange={(event) => setStructuredQuery(event.target.value)} maxLength={256} placeholder=".//product or .//product[@sku='P-101']" /></label>}
          {emptyBrowserPreview ? <div className="workspace-output-empty workspace-preview-empty"><Monitor size={24} /><h2>Preview is ready</h2><p>The selected preview file is empty, so there is nothing to render yet. Add HTML or JSX in the editor, or insert its starter code.</p></div> : showPreview ? <>
            <iframe id="playground-preview-frame" key={refresh} title={isReactPreview ? "React application preview" : isSassPreview ? "Sass compiled preview" : isAngularJSPreview ? "AngularJS application preview" : "Playground preview"} sandbox="allow-scripts" srcDoc={isSassPreview ? sassDocument : isAngularJSPreview ? angularJSPreviewDocument : isReactPreview ? reactDocument : browserDocument} />
            {!!browserOutput.length && <div className="workspace-console"><strong>Preview console</strong>{browserOutput.map((entry, index) => <pre key={`${index}-${entry.kind}`} className={`console-${entry.kind}`}>{entry.text}</pre>)}</div>}
            {isConnectedPreview && connectedOutput && <div className="workspace-console workspace-connected-output"><strong>{connectedOutput.language} execution result</strong><pre>{connectedOutput.stdout || "(no stdout)"}</pre>{connectedOutput.stderr && <pre className="console-error">{connectedOutput.stderr}</pre>}</div>}
          </> : runnerResult ? <div className="workspace-terminal" aria-live="polite">
            <div className="workspace-terminal-toolbar"><strong>Execution result</strong><span>{runnerResult.provider || "CodeLeaf runner"}</span></div>
            <div className="workspace-terminal-stream"><strong>stdout / compiler output</strong><pre>{runnerResult.stdout || "(no standard output or compiler output)"}</pre></div>
            {(runnerResult.stderr || runnerResult.error || runnerResult.message) && <div className="workspace-terminal-stream is-stderr"><strong>stderr / compiler messages</strong><pre>{runnerResult.stderr || runnerResult.error || runnerResult.message}</pre></div>}
            {runnerResult.truncated && <p className="workspace-runner-message" role="status">The execution provider truncated the output because it exceeded the display limit.</p>}
            {runnerResult.files_truncated && <p className="workspace-runner-message" role="status">Some output files were omitted because the provider or CodeLeaf reached its file-size limit.</p>}
            {Array.isArray(runnerResult.files) && runnerResult.files.some((file) => typeof file?.content_base64 === "string") && <div className="workspace-terminal-files"><strong>Output files</strong><div>{runnerResult.files.filter((file) => typeof file?.content_base64 === "string").map((file) => <a key={file.name} href={`data:${file.mime || "application/octet-stream"};base64,${file.content_base64}`} download={file.name}>{file.name} · {Number(file.size || 0).toLocaleString()} bytes <Download size={12} /></a>)}</div></div>}
            <div className="workspace-terminal-meta">{runnerResult.execution_status && <span>Execution: {runnerResult.execution_status}</span>}{runnerResult.exit_code !== undefined && <span>Exit code: {runnerResult.exit_code}</span>}{runnerResult.signal && <span>Signal: {runnerResult.signal}</span>}{runnerResult.engine && <span>Database: {runnerResult.engine}</span>}{runnerResult.row_count !== undefined && <span>Rows: {runnerResult.row_count}</span>}{runnerResult.execution_ms !== undefined && runnerResult.execution_ms !== null && <span>Time: {runnerResult.execution_ms} ms</span>}{runnerResult.total_time && <span>Total: {runnerResult.total_time}s</span>}{runnerResult.cpu_time && <span>Run: {runnerResult.cpu_time}s</span>}{runnerResult.memory && <span>Memory: {runnerResult.memory} KB</span>}{runnerResult.job_id && <span>Job: {runnerResult.job_id}</span>}</div>
          </div> : activeFile ? <div className="workspace-terminal workspace-terminal-idle" aria-live="polite"><div className="workspace-terminal-prompt"><span>CODELEAF TERMINAL</span><span>{languageLabel}</span></div><pre>{runnerMessage || (isStructuredTool ? `${languageLabel} uses a dedicated safe Playground tool. Select Run file to validate, format, preview, or simulate the supported commands for this file type.` : outputMode.reason === "connected-runtime-unavailable" ? "The selected server runtime is not enabled. Choose a language with an available compiler or configure its backend provider." : outputMode.runnerSupported ? "Terminal ready. Select Run file to compile or execute this program. Standard output and compiler/runtime errors will appear here." : `${languageLabel} uses terminal output. This language currently has no execution adapter configured, so the source has not been run.`)}</pre></div> : <div className="workspace-output-empty"><Code2 size={25} /><h2>Your workspace is empty</h2><p>Create a file in Explorer to get started.</p></div>}
          {runnerMessage && <p className="workspace-runner-message" role="status">{runnerMessage}</p>}
          {runnerResult?.job_id && <div className="workspace-output-actions"><button type="button" className="button button-secondary button-small" onClick={checkRunnerStatus} disabled={running}>Check status</button><button type="button" className="button button-secondary button-small" onClick={cancelRunnerJob} disabled={running || FINAL_RUNNER_STATES.has(runnerStatus)}>Cancel</button></div>}
          {!showPreview && !runnerResult?.job_id && activeFile && runnerSupportedLanguages.includes(activeLanguage?.key) && (isDatabaseLanguage
            ? <label className="workspace-stdin">Database setup SQL <textarea value={databaseSetupSql} onChange={(event) => setDatabaseSetupSql(event.target.value)} rows={4} maxLength={131072} placeholder="Optional: CREATE TABLE / INSERT statements run in a fresh temporary database before the query" /></label>
            : <label className="workspace-stdin">Standard input <textarea value={stdin} onChange={(event) => setStdin(event.target.value)} rows={3} maxLength={8000} placeholder="Input provided to your program" /></label>)}
        </section>
      </div>

      <div className="playground-note"><ShieldCheck size={16} /><span>Files auto-save in this browser. Use Account saves to persist workspaces and reusable snippets to your signed-in account; these are subject to plan-specific count and storage allowances. HTML previews run in a sandboxed frame with restrictive Content Security Policy. Server-side code is sent only to CodeLeaf's configured execution providers; structured formats use dedicated validators/previews; unsupported languages are not executed.</span></div>
    </PageShell>
  );
}
