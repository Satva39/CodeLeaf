import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Code2,
  Copy,
  Download,
  FileCode2,
  FileText,
  Folder,
  FolderTree,
  ListChecks,
  Play,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import { PageShell, EmptyState } from "../components/common.jsx";
import { API_BASE } from "../lib/demoState.js";
import { useCourseCatalog } from "../lib/useCourseCatalog.js";

function prettyLanguage(value) {
  const names = {
    jsx: "React JSX",
    tsx: "TypeScript JSX",
    javascript: "JavaScript",
    markdown: "Markdown",
    yaml: "YAML",
    bash: "Bash",
    powershell: "PowerShell",
    text: "Text",
  };
  const normalized = String(value || "text").toLowerCase();
  return names[normalized] || normalized.toUpperCase();
}

function rubricScore(rubric) {
  return (Array.isArray(rubric) ? rubric : []).reduce(
    (total, item) => total + (Number(item.points) || 0),
    0,
  );
}

function describeCriterion(item) {
  if (typeof item === "string") return item;
  if (!item || typeof item !== "object") return String(item ?? "");
  return item.name || item.title || item.description || item.purpose || item.command || JSON.stringify(item);
}

function SourceBadge({ kind }) {
  if (kind === "provided_in_manifest") return <span className="project-source-badge project-source-provided">Provided code</span>;
  if (kind === "provided_course_asset") return <span className="project-source-badge project-source-provided">Course file</span>;
  if (kind === "generated_scaffold") return <span className="project-source-badge project-source-generated">Starter scaffold</span>;
  return null;
}

function CodeFile({ file, copied, onCopy }) {
  return (
    <section className="project-code-file panel" aria-labelledby={`code-${file.path.replace(/[^a-zA-Z0-9]/g, "-")}`}>
      <div className="project-code-file-head">
        <div className="project-code-file-title">
          <FileCode2 size={17} />
          <div>
            <h3 id={`code-${file.path.replace(/[^a-zA-Z0-9]/g, "-")}`}>{file.path}</h3>
            {file.purpose && <p>{file.purpose}</p>}
          </div>
        </div>
        <div className="project-code-file-tools">
          <span className="project-code-language">{prettyLanguage(file.language)}</span>
          <SourceBadge kind={file.source_kind} />
          <button className="button button-secondary button-small" type="button" onClick={() => onCopy(file)}>
            {copied === file.path ? <ClipboardCheck size={14} /> : <Copy size={14} />}
            {copied === file.path ? "Copied" : "Copy code"}
          </button>
        </div>
      </div>
      <pre className="project-source-code"><code>{file.contents || "// This folder/file is listed in the project structure but does not contain source code."}</code></pre>
    </section>
  );
}

export default function ProjectGuidePage() {
  const { courseSlug, projectSlug } = useParams();
  const courses = useCourseCatalog();
  const course = courses.find((item) => item.slug === courseSlug);
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeFilePath, setActiveFilePath] = useState("");
  const [copied, setCopied] = useState("");
  const [treeMode, setTreeMode] = useState("tree");

  useEffect(() => {
    const controller = new AbortController();
    setGuide(null);
    setLoading(true);
    setError("");
    apiFetch(`${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/projects/${encodeURIComponent(projectSlug)}`, {
      credentials: "include",
      signal: controller.signal,
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "This project guide could not be loaded.");
        return payload;
      })
      .then((payload) => {
        setGuide(payload);
        const firstFile = (payload.files || []).find((file) => !file.is_directory && typeof file.contents === "string");
        setActiveFilePath(firstFile?.path || "");
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message || "This project guide could not be loaded.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [courseSlug, projectSlug]);

  const project = guide?.project;
  const codeFiles = useMemo(
    () => (Array.isArray(guide?.files) ? guide.files.filter((file) => !file.is_directory && typeof file.contents === "string") : []),
    [guide],
  );
  const activeFile = codeFiles.find((file) => file.path === activeFilePath) || codeFiles[0];
  const courseTitle = guide?.course?.title || course?.title || courseSlug;
  const milestones = Array.isArray(guide?.milestones) ? guide.milestones : [];
  const requiredFeatures = Array.isArray(guide?.required_features) ? guide.required_features : [];
  const stretchFeatures = Array.isArray(guide?.stretch_features) ? guide.stretch_features : [];
  const rubric = Array.isArray(guide?.rubric) ? guide.rubric : [];
  const runtime = guide?.runtime || {};
  const fileSummary = guide?.file_summary || {};
  const prerequisites = Array.isArray(project?.prerequisites) ? project.prerequisites : Array.isArray(project?.prerequisite_lesson_ids) ? project.prerequisite_lesson_ids : [];
  const skillList = Array.isArray(project?.skills) ? project.skills : Array.isArray(project?.target_skills) ? project.target_skills : [];

  async function handleCopy(file) {
    try {
      await navigator.clipboard.writeText(file.contents || "");
      setCopied(file.path);
      window.setTimeout(() => setCopied((current) => current === file.path ? "" : current), 1800);
    } catch {
      setCopied("");
    }
  }

  async function copyText(text, key) {
    try {
      await navigator.clipboard.writeText(text || "");
      setCopied(key);
      window.setTimeout(() => setCopied((current) => current === key ? "" : current), 1800);
    } catch {
      setCopied("");
    }
  }

  if (loading) {
    return <PageShell className="project-guide-page"><div className="panel project-guide-loading">Preparing the project guide and its files…</div></PageShell>;
  }

  if (error || !guide || !project) {
    return (
      <PageShell className="project-guide-page">
        <EmptyState
          icon={FolderTree}
          title="Project guide unavailable"
          detail={error || "This project may not be published yet, or its guide could not be found."}
          action={<Link className="button button-primary" to={courseSlug ? `/projects/${encodeURIComponent(courseSlug)}` : "/projects"}><ArrowLeft size={15} /> Back to projects</Link>}
        />
      </PageShell>
    );
  }

  const downloadUrl = `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/projects/${encodeURIComponent(projectSlug)}/starter-kit.zip`;

  return (
    <PageShell className="project-guide-page">
      <nav className="project-guide-breadcrumb" aria-label="Breadcrumb">
        <Link to="/projects">Projects</Link><ChevronRight size={14} /><Link to={`/projects/${encodeURIComponent(courseSlug)}`}>{courseTitle}</Link><ChevronRight size={14} /><span>{project.title}</span>
      </nav>

      <header className="project-guide-hero panel">
        <div className="project-guide-hero-copy">
          <span className="pill pill-mint">BUILD GUIDE · {String(project.tier || project.difficulty || "CORE").replaceAll("_", " ").toUpperCase()}</span>
          <h1>{project.title}</h1>
          <p className="project-guide-objective">{project.objective || project.scenario || "Build this project by following the milestones and acceptance checks below."}</p>
          {project.scenario && project.scenario !== project.objective && <p className="project-guide-scenario">{project.scenario}</p>}
          <div className="project-guide-hero-meta">
            <span><ListChecks size={15} /> {milestones.length} build milestones</span>
            <span><FileCode2 size={15} /> {fileSummary.total_files || codeFiles.length} files</span>
            <span><Terminal size={15} /> {runtime.label || "Project setup"}</span>
          </div>
          <div className="project-guide-hero-actions">
            <a href={downloadUrl} className="button button-primary"><Download size={16} /> Download starter project</a>
            <Link to={`/learn/${encodeURIComponent(courseSlug)}`} className="button button-secondary">Review lessons <ArrowRight size={15} /></Link>
          </div>
        </div>
        <div className="project-guide-summary-card">
          <span className="project-guide-summary-icon"><Code2 size={23} /></span>
          <h2>Build it step by step</h2>
          <p>Read one milestone, edit the corresponding file, run the project, and verify the acceptance checks before moving on.</p>
          <div className="project-guide-summary-stats">
            <div><strong>{fileSummary.provided_files || 0}</strong><span>provided files</span></div>
            <div><strong>{fileSummary.generated_scaffolds || 0}</strong><span>starter scaffolds</span></div>
          </div>
        </div>
      </header>

      {Number(fileSummary.generated_scaffolds) > 0 && (
        <div className="project-guide-notice" role="note">
          <ShieldCheck size={18} />
          <div><strong>About the included code</strong><p>{guide.content_notice || "Some project manifests only describe a file path and purpose. These files are labelled starter scaffolds, not finished reference solutions. Complete the milestones and test the result."}</p></div>
        </div>
      )}

      <section className="project-guide-section panel">
        <div className="project-guide-section-heading"><div><span className="eyebrow">01 · SETUP</span><h2>Before you start</h2><p>Install the tools that match this project, then keep your work inside one project folder.</p></div></div>
        <div className="project-guide-requirements">
          {(runtime.requirements || []).map((item) => <div className="project-guide-requirement" key={item}><CheckCircle2 size={17} /><span>{item}</span></div>)}
        </div>
        {!!prerequisites.length && (
          <div className="project-guide-prerequisites"><h3>Recommended prerequisites</h3><div className="project-guide-chip-list">{prerequisites.map((item) => <span key={item}>{item}</span>)}</div></div>
        )}
        {!!skillList.length && (
          <div className="project-guide-prerequisites"><h3>Skills you will practise</h3><div className="project-guide-chip-list">{skillList.map((item) => <span key={item}>{item}</span>)}</div></div>
        )}
      </section>

      <section className="project-guide-section panel">
        <div className="project-guide-section-heading project-guide-section-heading-row"><div><span className="eyebrow">02 · ORGANIZE</span><h2>Folder and file structure</h2><p>These are the files CodeLeaf includes in the downloadable starter bundle.</p></div><button className="button button-secondary button-small" type="button" onClick={() => setTreeMode((mode) => mode === "tree" ? "paths" : "tree")}>{treeMode === "tree" ? "Show paths" : "Show tree"}</button></div>
        <div className="project-folder-tree" role="list" aria-label="Project file tree">
          {treeMode === "tree" ? (guide.folder_tree || []).map((item) => (
            <div className={`project-folder-row is-${item.type}`} key={`${item.path}-${item.depth}`} style={{ paddingLeft: `${12 + (item.depth || 0) * 20}px` }} role="listitem">
              {item.type === "directory" ? <Folder size={15} /> : <FileText size={15} />}
              <code>{item.name}{item.type === "directory" ? "/" : ""}</code>
            </div>
          )) : <pre>{(guide.folder_tree || []).map((item) => `${"  ".repeat(item.depth || 0)}${item.type === "directory" ? "📁 " : "📄 "}${item.name}${item.type === "directory" ? "/" : ""}`).join("\n")}</pre>}
        </div>
      </section>

      {!!(guide.architecture || []).length && <section className="project-guide-section panel"><div className="project-guide-section-heading"><span className="eyebrow">03 · ARCHITECTURE</span><h2>How the project fits together</h2><p>Use this map to understand each file’s responsibility before you implement the milestones.</p></div><div className="project-guide-feature-grid">{guide.architecture.map((item, index) => <div key={`${index}-${describeCriterion(item)}`}><FileText size={16} /><div><strong>{typeof item === "string" ? item : item.component || item.name || item.title || item.path || `Component ${index + 1}`}</strong><p>{typeof item === "string" ? "" : item.responsibility || item.description || item.purpose || "Review the file and its imports to understand its role."}</p></div></div>)}</div></section>}

      <section className="project-guide-section panel">
        <div className="project-guide-section-heading"><span className="eyebrow">03 · BUILD</span><h2>Step-by-step implementation</h2><p>Each step includes a result you can check before continuing.</p></div>
        <div className="project-milestone-list">
          {milestones.map((milestone, index) => {
            const checks = Array.isArray(milestone.acceptance_criteria) ? milestone.acceptance_criteria : [];
            return <article className="project-milestone-card" key={`${milestone.sequence || index}-${milestone.title}`}>
              <div className="project-milestone-number">{String(milestone.sequence || index + 1).padStart(2, "0")}</div>
              <div className="project-milestone-copy"><h3>{milestone.title || `Step ${index + 1}`}</h3>
                {milestone.description && <p>{milestone.description}</p>}
                {!!checks.length && <div className="project-milestone-checks"><strong>Done when:</strong><ul>{checks.map((criterion) => <li key={criterion}>{criterion}</li>)}</ul></div>}
                {milestone.expected_result && <p className="project-milestone-result"><CheckCircle2 size={15} /> Expected result: {milestone.expected_result}</p>}
              </div>
            </article>;
          })}
        </div>
      </section>

      <section className="project-guide-section panel project-guide-files-section">
        <div className="project-guide-section-heading"><span className="eyebrow">04 · WRITE THE CODE</span><h2>All project files and code</h2><p>Select a file to see its code. Use Copy code to bring it into your editor, or download the complete starter bundle above.</p></div>
        {!codeFiles.length ? <div className="project-guide-inline-empty">No source files are attached to this project yet. Review the milestones and add the required files to the course manifest.</div> : (
          <div className="project-code-workbench">
            <aside className="project-code-file-list" aria-label="Project code files">
              {codeFiles.map((file) => <button key={file.path} type="button" className={activeFile?.path === file.path ? "active" : ""} onClick={() => setActiveFilePath(file.path)}><FileCode2 size={15} /><span>{file.path}</span>{file.source_kind === "generated_scaffold" && <i aria-label="Starter scaffold" />}</button>)}
            </aside>
            <div className="project-code-editor-panel">
              {activeFile && <CodeFile file={activeFile} copied={copied} onCopy={handleCopy} />}
            </div>
          </div>
        )}
      </section>

      {!!requiredFeatures.length && <section className="project-guide-section panel"><div className="project-guide-section-heading"><span className="eyebrow">05 · REQUIREMENTS</span><h2>Required features</h2></div><div className="project-guide-feature-grid">{requiredFeatures.map((feature) => <div key={feature}><CheckCircle2 size={16} /><span>{feature}</span></div>)}</div></section>}
      {!!stretchFeatures.length && <section className="project-guide-section panel"><div className="project-guide-section-heading"><span className="eyebrow">OPTIONAL EXTENSIONS</span><h2>Make it even better</h2><p>Attempt these after the required features work.</p></div><ul className="project-guide-normal-list">{stretchFeatures.map((item) => <li key={typeof item === "string" ? item : JSON.stringify(item)}>{describeCriterion(item)}</li>)}</ul></section>}

      <section className="project-guide-section panel">
        <div className="project-guide-section-heading"><span className="eyebrow">06 · RUN AND VERIFY</span><h2>Run the project</h2><p>Commands are common defaults for this technology. Follow the file-specific entry point and pinned versions in the project README first.</p></div>
        <div className="project-run-commands">
          {(runtime.commands || []).map((step, index) => <div className="project-run-command" key={`${step.label}-${index}`}><div className="project-run-command-main"><span>{String(index + 1).padStart(2, "0")}</span><div><h3>{step.label}</h3><code>{step.command}</code></div></div><button className="button button-secondary button-small" type="button" onClick={() => copyText(step.command, `command-${index}`)}>{copied === `command-${index}` ? <ClipboardCheck size={14} /> : <Copy size={14} />}{copied === `command-${index}` ? "Copied" : "Copy"}</button></div>)}
        </div>
        {runtime.note && <p className="project-guide-runtime-note"><ShieldCheck size={16} /> {runtime.note}</p>}
      </section>

      {!!(guide.quality_checks || []).length && <section className="project-guide-section panel"><div className="project-guide-section-heading"><span className="eyebrow">07 · TEST</span><h2>Testing and validation</h2><p>Use these checks to prove that the project works and handles edge cases.</p></div><div className="project-guide-feature-grid">{guide.quality_checks.map((item, index) => <div key={`${index}-${describeCriterion(item)}`}><CheckCircle2 size={16} /><span>{describeCriterion(item)}</span></div>)}</div></section>}

      {!!(guide.troubleshooting || []).length && <section className="project-guide-section panel"><div className="project-guide-section-heading"><span className="eyebrow">TROUBLESHOOTING</span><h2>When something goes wrong</h2><p>Start with a clear symptom, isolate one cause, and verify the fix.</p></div><div className="project-milestone-list">{guide.troubleshooting.map((item, index) => <article className="project-milestone-card" key={`${index}-${describeCriterion(item)}`}><div className="project-milestone-number">{String(index + 1).padStart(2, "0")}</div><div className="project-milestone-copy"><h3>{typeof item === "string" ? item : item.problem || item.title || item.symptom || `Troubleshooting step ${index + 1}`}</h3><p>{typeof item === "string" ? "Inspect the first error, change one thing at a time, then repeat the relevant test." : item.check || item.solution || item.description || item.fix || "Inspect the first error and compare the actual result with the expected result."}</p></div></article>)}</div></section>}

      {!!rubric.length && <section className="project-guide-section panel"><div className="project-guide-section-heading"><span className="eyebrow">REVIEW RUBRIC</span><h2>How the project is evaluated</h2><p>Use the rubric as your final self-review before submitting.</p></div><div className="project-rubric-list">{rubric.map((item, index) => <div key={`${item.criterion || item.title || index}`}><span>{item.criterion || item.title || describeCriterion(item)}</span><strong>{Number(item.points) || 0} pts</strong></div>)}</div><div className="project-rubric-total"><span>Total possible</span><strong>{Number(project.rubric_total) || rubricScore(rubric)} points</strong></div></section>}

      <footer className="project-guide-finish panel"><span className="project-guide-summary-icon"><Play size={21} /></span><div><h2>Ready to build?</h2><p>Start with the first milestone, run your code, and verify every acceptance check. Small verified steps make larger projects easier to finish.</p></div><a href={downloadUrl} className="button button-primary"><Download size={15} /> Get starter files</a></footer>
      <div className="project-guide-back-link"><Link to={`/projects/${encodeURIComponent(courseSlug)}`}><ArrowLeft size={15} /> Back to {courseTitle} projects</Link></div>
    </PageShell>
  );
}
