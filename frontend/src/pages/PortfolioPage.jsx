import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, Award, Download, ExternalLink, FileArchive, FolderKanban, LockKeyhole, Save, Share2 } from "lucide-react";
import { EmptyState, PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import { recordAnalyticsEvent } from "../lib/analytics.js";

async function request(path, options = {}) {
  const response = await apiFetch(`${API_BASE}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = body?.detail;
    const message = typeof detail === "string" && detail.trim()
      ? detail
      : detail && typeof detail === "object"
        ? [detail.message, detail.detail, detail.error].find((value) => typeof value === "string" && value.trim()) || "Portfolio request failed."
        : "Portfolio request failed.";
    const err = new Error(message);
    err.status = response.status;
    err.payload = body;
    throw err;
  }
  return body;
}

const MAX_PROJECT_ZIP_BYTES = 500 * 1024 * 1024;
function toProjectSlug(value) {
  return String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 180).replace(/-+$/g, "");
}
function formatFileSize(size) {
  if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  return `${(size / 1024).toFixed(1)} KB`;
}

export default function PortfolioPage() {
  const { username } = useParams();
  const isPublic = Boolean(username);
  const [items, setItems] = useState([]);
  const [owner, setOwner] = useState(null);
  const [certificates, setCertificates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState("");
  const [notice, setNotice] = useState("");
  const [submissionDraft, setSubmissionDraft] = useState({ course_slug: "", project_slug: "", title: "" });
  const [archiveFile, setArchiveFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const body = isPublic ? await request(`/api/portfolio/${encodeURIComponent(username)}`) : await request("/api/me/portfolio");
      setItems(body.items || []); setCertificates(body.certificates || []); setOwner({ username: body.username, display_name: isPublic ? body.display_name : null });
    } catch (err) { setError(err.message || "Portfolio is unavailable."); }
    finally { setLoading(false); }
  }, [isPublic, username]);
  useEffect(() => { void load(); }, [load]);

  const updateItem = async (item, patch) => {
    setSavingId(item.id); setNotice(""); setError("");
    try {
      const body = await request(`/api/me/portfolio/${encodeURIComponent(item.id)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) });
      setItems((rows) => rows.map((row) => row.id === item.id ? body.item : row));
      setNotice(`Saved “${body.item.title}”. ${body.item.visibility === "public" ? "It is now visible on the public portfolio link." : "It is private."}`);
    } catch (err) { setError(err.message || "Changes could not be saved."); }
    finally { setSavingId(""); }
  };

  const createSubmission = async (event) => {
    event.preventDefault(); setError(""); setNotice("");
    if (!archiveFile) { setError("Choose a ZIP archive containing your project files."); return; }
    if (!archiveFile.name.toLowerCase().endsWith(".zip")) { setError("Only .zip project archives are accepted."); return; }
    if (archiveFile.size > MAX_PROJECT_ZIP_BYTES) { setError("Project ZIP files must be 500 MB or smaller."); return; }
    setSubmitting(true);
    setUploadProgress(0);
    let uploadId = "";
    try {
      const courseSlug = toProjectSlug(submissionDraft.course_slug);
      const generatedSlug = toProjectSlug(submissionDraft.project_slug || submissionDraft.title || archiveFile.name.replace(/\.zip$/i, "")) || "my-project";
      const session = await request("/api/me/portfolio/submissions/upload-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          course_slug: courseSlug,
          project_slug: generatedSlug,
          title: submissionDraft.title.trim() || null,
          filename: archiveFile.name,
          total_bytes: archiveFile.size,
        }),
      });
      uploadId = session.upload_id;
      const chunkSize = Number(session.chunk_size);
      const chunkCount = Number(session.chunk_count);
      if (!uploadId || !Number.isInteger(chunkSize) || chunkSize <= 0 || !Number.isInteger(chunkCount) || chunkCount <= 0) {
        throw new Error("The server returned an invalid upload session. Please retry.");
      }
      for (let sequence = 0; sequence < chunkCount; sequence += 1) {
        const start = sequence * chunkSize;
        const chunk = archiveFile.slice(start, Math.min(archiveFile.size, start + chunkSize));
        await request(`/api/me/portfolio/submissions/upload-session/${encodeURIComponent(uploadId)}/chunks/${sequence}`, {
          method: "PUT",
          headers: { "Content-Type": "application/octet-stream" },
          body: chunk,
        });
        setUploadProgress(Math.round(((sequence + 1) / chunkCount) * 100));
      }
      const body = await request(`/api/me/portfolio/submissions/upload-session/${encodeURIComponent(uploadId)}/finalize`, { method: "POST" });
      setItems((rows) => [body.submission, ...rows]);
      setArchiveFile(null);
      const input = document.getElementById("portfolio-project-zip");
      if (input) input.value = "";
      setNotice("Project ZIP validated and saved privately. Add a summary, then enable public sharing only when ready.");
      if (courseSlug) void recordAnalyticsEvent({ event_type: "project_completion", course_slug: courseSlug, item_key: generatedSlug, outcome: "success" });
    } catch (err) {
      if (uploadId) {
        try {
          await request(`/api/me/portfolio/submissions/upload-session/${encodeURIComponent(uploadId)}`, { method: "DELETE" });
        } catch {
          // Abandoned sessions are cleaned up when the learner starts another upload after 24 hours.
        }
      }
      setError(err.message || "Project ZIP could not be saved.");
    } finally {
      setSubmitting(false);
      setUploadProgress(0);
    }
  };

  if (loading) return <PageShell><div className="panel phase5-state">Loading portfolio…</div></PageShell>;
  if (!isPublic && error && /sign in|session|database is not configured/i.test(error)) return <PageShell><EmptyState icon={LockKeyhole} title="Sign in to manage your portfolio" detail={error} action={<Link to="/login" className="button button-primary">Sign in <ArrowRight size={14} /></Link>} /></PageShell>;

  return <PageShell className="phase5-page">
    <div className="phase5-hero panel"><div><div className="eyebrow">LEARNER WORK</div><h1>{isPublic ? `${owner?.display_name || username}'s portfolio` : "My portfolio"}</h1><p>{isPublic ? "Shared projects and earned certificates are shown here. Project downloads appear only for projects the learner made public." : "Project submissions start private. Earned certificates appear below, and you choose which project metadata visitors can see."}</p></div><FolderKanban size={34} /></div>
    {error && <p className="phase5-alert" role="alert">{error}</p>}{notice && <p className="phase5-notice" role="status">{notice}</p>}
    {owner && <p className="phase5-public-link"><Share2 size={15} /> Portfolio link (shared projects and earned certificates are visible): <code>{window.location.origin}/portfolio/{owner.username}</code></p>}
    {!isPublic && <div className="phase5-privacy-note"><LockKeyhole size={18}/><span><strong>Private by default</strong><small>Project files stay private until a project is shared. Active certificates are listed on the portfolio with public verification links; account email and private profile attributes are never exposed.</small></span></div>}
    {!isPublic && <section className="panel phase5-section phase5-submission-form"><div className="phase5-section-title"><div><div className="eyebrow">REAL PROJECT WORK</div><h2>Submit a project</h2></div><FolderKanban size={21}/></div><p className="phase5-muted">Upload any project you built yourself, whether it came from a CodeLeaf course or an independent project. A reviewed course-manifest match is not required. Uploads stay private until you explicitly enable sharing.</p><form className="phase5-studio-form" onSubmit={createSubmission}><label>Technology / course (optional)<input maxLength={100} value={submissionDraft.course_slug} onChange={(event) => setSubmissionDraft((value) => ({ ...value, course_slug: event.target.value }))} placeholder="HTML, Python, React…"/><small>Optional label for the technology or course.</small></label><label>Project slug (optional)<input maxLength={180} value={submissionDraft.project_slug} onChange={(event) => setSubmissionDraft((value) => ({ ...value, project_slug: event.target.value }))} placeholder="Auto-generated from title or ZIP name"/></label><label>Project title (optional)<input maxLength={200} value={submissionDraft.title} onChange={(event) => setSubmissionDraft((value) => ({ ...value, title: event.target.value }))} placeholder="My project"/></label><label className="phase5-studio-zip-field" htmlFor="portfolio-project-zip">Project ZIP file<input id="portfolio-project-zip" type="file" accept=".zip,application/zip" required onChange={(event) => setArchiveFile(event.target.files?.[0] || null)}/><small>Upload any .zip of your project files. Maximum 500 MB compressed, up to 10,000 files and 1 GB total uncompressed. For large projects, exclude dependency folders such as node_modules and build caches. The archive is stored privately and becomes downloadable only when you enable public sharing.</small></label>{archiveFile && <p className="phase5-upload-selected"><FileArchive size={15}/> {archiveFile.name} · {formatFileSize(archiveFile.size)}</p>}<button className="button button-primary" type="submit" disabled={submitting}>{submitting ? `Uploading ZIP… ${uploadProgress}%` : "Upload ZIP privately"}</button></form></section>}
    {certificates.length > 0 && <section className="phase5-section phase5-earned-certificates"><div className="phase5-section-title"><div><div className="eyebrow">VERIFIED ACHIEVEMENTS</div><h2>Certificates earned</h2></div><Award size={23}/></div><p className="phase5-muted">Active certificates are included in this portfolio and can be verified publicly.</p><div className="phase5-certificate-grid">{certificates.map((certificate) => <article className="panel phase5-certificate-card" key={certificate.public_id}><span className="phase5-pill"><Award size={12}/> Verified certificate</span><h3>{certificate.course_title}</h3><p>Issued {new Date(certificate.issued_at).toLocaleDateString()}</p><small>Credential ID: <code>{certificate.public_id}</code></small><a className="button button-secondary button-small" href={`${API_BASE}${certificate.verification_url}`} target="_blank" rel="noreferrer">Verify certificate <ExternalLink size={13}/></a></article>)}</div></section>}
    {items.length === 0 ? <EmptyState icon={FolderKanban} title={isPublic ? "No public projects yet" : "No project submissions yet"} detail={isPublic ? "This learner has not chosen to share a project." : "Upload a ZIP of your project files to create a portfolio entry. New submissions stay private until you share them."} action={!isPublic ? <Link to="/projects" className="button button-primary">Browse projects <ArrowRight size={14}/></Link> : undefined} /> : <div className="phase5-portfolio-grid">{items.map((item) => <article className="panel phase5-portfolio-card" key={item.id}>
      <div className="phase5-portfolio-card-top"><span className="phase5-pill">{isPublic ? "Shared project" : item.visibility === "public" ? "Public" : "Private"}</span>{!isPublic && <label className="phase5-visibility"><input type="checkbox" checked={item.visibility === "public"} disabled={savingId === item.id} onChange={(event) => void updateItem(item, { visibility: event.target.checked ? "public" : "private" })}/> Share publicly</label>}</div>
      {isPublic ? <h2>{item.title}</h2> : <label className="phase5-field">Project title<input defaultValue={item.title} maxLength={200} onBlur={(event) => { if (event.target.value.trim() && event.target.value.trim() !== item.title) void updateItem(item, { title: event.target.value.trim() }); }}/></label>}
      {isPublic ? <p>{item.summary || "Project submission"}</p> : <label className="phase5-field">Summary<textarea rows={3} maxLength={1000} defaultValue={item.summary || ""} placeholder="What did you build?" onBlur={(event) => { if (event.target.value !== (item.summary || "")) void updateItem(item, { summary: event.target.value }); }}/></label>}
      <div className="phase5-field-pair">{!isPublic && <label className="phase5-field">Skills<input defaultValue={(item.skills || []).join(", ")} placeholder="HTML, accessibility" onBlur={(event) => { const value = event.target.value.split(",").map((term) => term.trim()).filter(Boolean); if (JSON.stringify(value) !== JSON.stringify(item.skills || [])) void updateItem(item, { skills: value.slice(0, 20) }); }}/></label>}<div className="phase5-tag-row">{(item.skills || []).map((tag) => <span key={tag}>{tag}</span>)}</div></div>
      {!isPublic && <label className="phase5-field">Technologies<input defaultValue={(item.technologies || []).join(", ")} placeholder="React, CSS" onBlur={(event) => { const value = event.target.value.split(",").map((term) => term.trim()).filter(Boolean); if (JSON.stringify(value) !== JSON.stringify(item.technologies || [])) void updateItem(item, { technologies: value.slice(0, 20) }); }}/></label>}
      <div className="phase5-tag-row">{(item.technologies || []).map((tag) => <span key={tag}>{tag}</span>)}</div>
      {!isPublic && <label className="phase5-field">Screenshot URLs (one HTTPS URL per line)<textarea rows={2} defaultValue={(item.screenshot_urls || []).join("\n")} placeholder="https://…" onBlur={(event) => { const value = event.target.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean); if (JSON.stringify(value) !== JSON.stringify(item.screenshot_urls || [])) void updateItem(item, { screenshot_urls: value.slice(0, 5) }); }}/></label>}
      {(item.screenshot_urls || []).length > 0 && <div className="phase5-screenshot-grid">{item.screenshot_urls.map((url) => <a key={url} href={url} rel="noreferrer" target="_blank"><img src={url} alt={`Screenshot for ${item.title}`} loading="lazy" referrerPolicy="no-referrer"/><span>Open screenshot <ExternalLink size={12}/></span></a>)}</div>}
      <footer><small>Submitted {new Date(item.submitted_at).toLocaleDateString()}</small><div className="phase5-card-actions">{item.has_downloadable_zip && <a className="button button-secondary button-small" href={isPublic ? `${API_BASE}/api/portfolio/${encodeURIComponent(username)}/projects/${encodeURIComponent(item.id)}/download` : `${API_BASE}/api/me/portfolio/${encodeURIComponent(item.id)}/download`}><Download size={13}/> Download ZIP</a>}{!isPublic && <span className="phase5-save-status">{savingId === item.id ? "Saving…" : <><Save size={12}/> Auto-saves on field exit</>}</span>}</div></footer>
    </article>)}</div>}
  </PageShell>;
}
