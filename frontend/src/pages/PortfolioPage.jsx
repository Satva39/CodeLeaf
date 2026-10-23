import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowRight, ExternalLink, FolderKanban, LockKeyhole, Save, Share2 } from "lucide-react";
import { EmptyState, PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import { recordAnalyticsEvent } from "../lib/analytics.js";

async function request(path, options = {}) {
  const response = await apiFetch(`${API_BASE}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) { const err = new Error(body.detail || "Portfolio request failed."); err.status = response.status; throw err; }
  return body;
}

export default function PortfolioPage() {
  const { username } = useParams();
  const isPublic = Boolean(username);
  const [items, setItems] = useState([]);
  const [owner, setOwner] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState("");
  const [notice, setNotice] = useState("");
  const [submissionDraft, setSubmissionDraft] = useState({ course_slug: "html", project_slug: "personal-profile-page", title: "", code_bundle_text: '{\n  "index.html": "<!-- Replace this with your own work -->"\n}' });
  const [submitting, setSubmitting] = useState(false);
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const body = isPublic ? await request(`/api/portfolio/${encodeURIComponent(username)}`) : await request("/api/me/portfolio");
      setItems(body.items || []); setOwner({ username: body.username, display_name: isPublic ? body.display_name : null });
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
    let code_bundle;
    try { code_bundle = JSON.parse(submissionDraft.code_bundle_text); }
    catch { setError("Files must be a valid JSON object mapping safe relative file paths to code strings."); return; }
    if (!code_bundle || typeof code_bundle !== "object" || Array.isArray(code_bundle) || Object.keys(code_bundle).length === 0) { setError("Add at least one file of your own work before submitting a project."); return; }
    setSubmitting(true);
    try {
      const body = await request("/api/me/portfolio/submissions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ course_slug: submissionDraft.course_slug, project_slug: submissionDraft.project_slug, title: submissionDraft.title || null, code_bundle }) });
      setItems((rows) => [body.submission, ...rows]);
      setNotice("Project submission saved privately. Choose summary, skills and technologies, then enable public sharing only when ready.");
      void recordAnalyticsEvent({ event_type: "project_completion", course_slug: submissionDraft.course_slug, item_key: submissionDraft.project_slug, outcome: "success" });
    } catch (err) { setError(err.message || "Project submission could not be saved."); }
    finally { setSubmitting(false); }
  };

  if (loading) return <PageShell><div className="panel phase5-state">Loading portfolio…</div></PageShell>;
  if (!isPublic && error && /sign in|session|database is not configured/i.test(error)) return <PageShell><EmptyState icon={LockKeyhole} title="Sign in to manage your portfolio" detail={error} action={<Link to="/login" className="button button-primary">Sign in <ArrowRight size={14} /></Link>} /></PageShell>;

  return <PageShell className="phase5-page">
    <div className="phase5-hero panel"><div><div className="eyebrow">LEARNER WORK</div><h1>{isPublic ? `${owner?.display_name || username}'s portfolio` : "My portfolio"}</h1><p>{isPublic ? "Only project fields explicitly made public by the learner appear here." : "Submissions start private. Select the information you want to share before making a project public."}</p></div><FolderKanban size={34} /></div>
    {error && <p className="phase5-alert" role="alert">{error}</p>}{notice && <p className="phase5-notice" role="status">{notice}</p>}
    {owner && <p className="phase5-public-link"><Share2 size={15} /> Public portfolio link (only explicitly shared projects appear): <code>{window.location.origin}/portfolio/{owner.username}</code></p>}
    {!isPublic && <div className="phase5-privacy-note"><LockKeyhole size={18}/><span><strong>Private by default</strong><small>Code files, account details, email and private profile attributes are never returned by the public portfolio API.</small></span></div>}
    {!isPublic && <section className="panel phase5-section phase5-submission-form"><div className="phase5-section-title"><div><div className="eyebrow">REAL PROJECT WORK</div><h2>Submit a project</h2></div><FolderKanban size={21}/></div><p className="phase5-muted">Use a published project slug from its project guide. The submission is validated against the course manifest and stays private until you explicitly share its metadata.</p><form className="phase5-studio-form" onSubmit={createSubmission}><label>Course slug<input required maxLength={100} value={submissionDraft.course_slug} onChange={(event) => setSubmissionDraft((value) => ({ ...value, course_slug: event.target.value }))}/></label><label>Project slug<input required maxLength={180} value={submissionDraft.project_slug} onChange={(event) => setSubmissionDraft((value) => ({ ...value, project_slug: event.target.value }))}/></label><label>Title (optional)<input maxLength={200} value={submissionDraft.title} onChange={(event) => setSubmissionDraft((value) => ({ ...value, title: event.target.value }))} placeholder="My project"/></label><label className="phase5-studio-json-field">Your files (JSON mapping of relative file paths to source text)<textarea required rows={8} spellCheck="false" value={submissionDraft.code_bundle_text} onChange={(event) => setSubmissionDraft((value) => ({ ...value, code_bundle_text: event.target.value }))}/></label><button className="button button-primary" type="submit" disabled={submitting}>{submitting ? "Submitting…" : "Save private submission"}</button></form></section>}
    {items.length === 0 ? <EmptyState icon={FolderKanban} title={isPublic ? "No public projects yet" : "No project submissions yet"} detail={isPublic ? "This learner has not chosen to share a project." : "Submit a project from a published course to add real work here. A portfolio card is created only from a saved submission; no sample completion is generated."} action={!isPublic ? <Link to="/projects" className="button button-primary">Browse projects <ArrowRight size={14}/></Link> : undefined} /> : <div className="phase5-portfolio-grid">{items.map((item) => <article className="panel phase5-portfolio-card" key={item.id}>
      <div className="phase5-portfolio-card-top"><span className="phase5-pill">{isPublic ? "Shared project" : item.visibility === "public" ? "Public" : "Private"}</span>{!isPublic && <label className="phase5-visibility"><input type="checkbox" checked={item.visibility === "public"} disabled={savingId === item.id} onChange={(event) => void updateItem(item, { visibility: event.target.checked ? "public" : "private" })}/> Share publicly</label>}</div>
      {isPublic ? <h2>{item.title}</h2> : <label className="phase5-field">Project title<input defaultValue={item.title} maxLength={200} onBlur={(event) => { if (event.target.value.trim() && event.target.value.trim() !== item.title) void updateItem(item, { title: event.target.value.trim() }); }}/></label>}
      {isPublic ? <p>{item.summary || "Project submission"}</p> : <label className="phase5-field">Summary<textarea rows={3} maxLength={1000} defaultValue={item.summary || ""} placeholder="What did you build?" onBlur={(event) => { if (event.target.value !== (item.summary || "")) void updateItem(item, { summary: event.target.value }); }}/></label>}
      <div className="phase5-field-pair">{!isPublic && <label className="phase5-field">Skills<input defaultValue={(item.skills || []).join(", ")} placeholder="HTML, accessibility" onBlur={(event) => { const value = event.target.value.split(",").map((term) => term.trim()).filter(Boolean); if (JSON.stringify(value) !== JSON.stringify(item.skills || [])) void updateItem(item, { skills: value.slice(0, 20) }); }}/></label>}<div className="phase5-tag-row">{(item.skills || []).map((tag) => <span key={tag}>{tag}</span>)}</div></div>
      {!isPublic && <label className="phase5-field">Technologies<input defaultValue={(item.technologies || []).join(", ")} placeholder="React, CSS" onBlur={(event) => { const value = event.target.value.split(",").map((term) => term.trim()).filter(Boolean); if (JSON.stringify(value) !== JSON.stringify(item.technologies || [])) void updateItem(item, { technologies: value.slice(0, 20) }); }}/></label>}
      <div className="phase5-tag-row">{(item.technologies || []).map((tag) => <span key={tag}>{tag}</span>)}</div>
      {!isPublic && <label className="phase5-field">Screenshot URLs (one HTTPS URL per line)<textarea rows={2} defaultValue={(item.screenshot_urls || []).join("\n")} placeholder="https://…" onBlur={(event) => { const value = event.target.value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean); if (JSON.stringify(value) !== JSON.stringify(item.screenshot_urls || [])) void updateItem(item, { screenshot_urls: value.slice(0, 5) }); }}/></label>}
      {(item.screenshot_urls || []).length > 0 && <div className="phase5-screenshot-grid">{item.screenshot_urls.map((url) => <a key={url} href={url} rel="noreferrer" target="_blank"><img src={url} alt={`Screenshot for ${item.title}`} loading="lazy" referrerPolicy="no-referrer"/><span>Open screenshot <ExternalLink size={12}/></span></a>)}</div>}
      <footer><small>Submitted {new Date(item.submitted_at).toLocaleDateString()}</small>{!isPublic && <span className="phase5-save-status">{savingId === item.id ? "Saving…" : <><Save size={12}/> Auto-saves on field exit</>}</span>}</footer>
    </article>)}</div>}
  </PageShell>;
}
