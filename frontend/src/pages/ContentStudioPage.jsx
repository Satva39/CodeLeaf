import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Archive, ArrowDownToLine, CheckCircle2, ClipboardCheck, FileJson, History, LockKeyhole, Plus, Send, ShieldCheck } from "lucide-react";
import { EmptyState, PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";

async function request(path, options = {}) {
  const response = await apiFetch(`${API_BASE}${path}`, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) { const error = new Error(body.detail || "Content studio request failed."); error.status = response.status; throw error; }
  return body;
}

const INITIAL_JSON = '{\n  "slug": "example-item",\n  "title": "Example title",\n  "description": "Replace this sample with reviewed course content."\n}';

export default function ContentStudioPage() {
  const [items, setItems] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [draft, setDraft] = useState({ course_slug: "html", content_type: "lesson", content_slug: "example-item", content_json_text: INITIAL_JSON });
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const body = await request("/api/editor/content-revisions");
      const rows = body.items || [];
      setItems(rows);
      setSelectedId((current) => current || rows[0]?.id || "");
    } catch (err) { setError(err.message || "Editor access is unavailable."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const selected = items.find((item) => item.id === selectedId) || null;
  useEffect(() => { setPreview(selected); }, [selectedId, items]);

  const postAction = async (path, message, payload = undefined) => {
    setBusy(true); setError(""); setNotice("");
    try {
      await request(path, payload === undefined ? { method: "POST" } : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      await load();
      setNotice(message);
    } catch (err) { setError(err.message || "Action failed."); }
    finally { setBusy(false); }
  };

  const createDraft = async (event) => {
    event.preventDefault(); setError(""); setNotice("");
    let content;
    try { content = JSON.parse(draft.content_json_text); }
    catch { setError("Draft content is not valid JSON."); return; }
    setBusy(true);
    try {
      const body = await request("/api/editor/content-revisions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ course_slug: draft.course_slug.trim().toLowerCase(), content_type: draft.content_type, content_slug: draft.content_slug.trim().toLowerCase(), content_json: content }) });
      setItems((rows) => [body.revision, ...rows]);
      setSelectedId(body.revision.id);
      setNotice("Draft saved as a new immutable version.");
    } catch (err) { setError(err.message || "Draft could not be saved."); }
    finally { setBusy(false); }
  };

  const review = async (approved) => {
    if (!selected) return;
    const feedback = window.prompt(approved ? "Optional review feedback:" : "What needs to change before approval?") || "";
    await postAction(`/api/editor/content-revisions/${selected.id}/review`, approved ? "Revision approved for studio publication." : "Revision returned to draft with feedback.", { approved, feedback });
  };

  if (loading) return <PageShell><div className="panel phase5-state">Loading content studio…</div></PageShell>;
  if (error && ( /permission|editor|403/i.test(error) )) return <PageShell><EmptyState icon={LockKeyhole} title="Editor access required" detail={`${error} Editor roles must be granted by an authorized database/operator workflow; the client cannot assign itself a role.`} action={<Link to="/dashboard" className="button button-secondary">Back to dashboard</Link>} /></PageShell>;

  return <PageShell className="phase5-page phase5-studio-page">
    <div className="phase5-hero panel"><div><div className="eyebrow">AUTHORIZED CURRICULUM WORKFLOW</div><h1>Content studio</h1><p>Create versioned drafts, preview JSON safely, validate structure, collect review feedback, publish to the studio history, archive, or create a rollback draft.</p></div><FileJson size={34}/></div>
    {error && <p className="phase5-alert" role="alert">{error}</p>}{notice && <p className="phase5-notice" role="status">{notice}</p>}
    <div className="phase5-studio-grid">
      <section className="panel phase5-section">
        <div className="phase5-section-title"><div><div className="eyebrow">VERSION HISTORY</div><h2>Revisions</h2></div><History size={21}/></div>
        {items.length ? <div className="phase5-revision-list">{items.map((item) => <button type="button" key={item.id} className={`phase5-revision-item ${item.id === selectedId ? "active" : ""}`} onClick={() => setSelectedId(item.id)}><span><strong>{item.content_slug}</strong><small>{item.course_slug} · {item.content_type} · v{item.version}</small></span><em className={`phase5-status phase5-status-${item.status}`}>{item.status}</em></button>)}</div> : <p className="phase5-muted">No revision records yet. Create a draft to begin.</p>}
      </section>
      <section className="panel phase5-section phase5-studio-preview">
        <div className="phase5-section-title"><div><div className="eyebrow">ISOLATED PREVIEW</div><h2>{selected ? `${selected.content_slug} · v${selected.version}` : "Create a draft"}</h2></div><ShieldCheck size={21}/></div>
        {selected ? <>
          <div className="phase5-studio-meta"><span className={`phase5-status phase5-status-${selected.status}`}>{selected.status}</span><span>{new Date(selected.created_at).toLocaleString()}</span></div>
          <pre className="phase5-json-preview"><code>{JSON.stringify(selected.content_json, null, 2)}</code></pre>
          {selected.validation_report?.errors?.length > 0 && <ul className="phase5-validation-errors">{selected.validation_report.errors.map((entry) => <li key={entry}>{entry}</li>)}</ul>}
          {selected.review_feedback && <blockquote className="phase5-review-feedback">{selected.review_feedback}</blockquote>}
          <div className="phase5-actions phase5-studio-actions">
            <button className="button button-secondary button-small" disabled={busy || !["draft", "review", "reviewed"].includes(selected.status)} onClick={() => void postAction(`/api/editor/content-revisions/${selected.id}/validate`, "Structural validation finished.")}><ClipboardCheck size={14}/> Validate</button>
            <button className="button button-secondary button-small" disabled={busy || selected.status !== "review"} onClick={() => void review(false)}>Request changes</button>
            <button className="button button-secondary button-small" disabled={busy || selected.status !== "review"} onClick={() => void review(true)}><CheckCircle2 size={14}/> Approve</button>
            <button className="button button-primary button-small" disabled={busy || selected.status !== "reviewed" || !selected.validation_report?.valid} onClick={() => void postAction(`/api/editor/content-revisions/${selected.id}/publish`, "Revision published to studio history. Live course files remain unchanged until importer/release preflight.")}><Send size={14}/> Publish</button>
            <button className="button button-secondary button-small" disabled={busy} onClick={() => void postAction(`/api/editor/content-revisions/${selected.id}/rollback`, "Rollback copy created as a new draft; validate and review it before use.")}><ArrowDownToLine size={14}/> Rollback copy</button>
            <button className="button button-secondary button-small" disabled={busy || selected.status === "archived"} onClick={() => void postAction(`/api/editor/content-revisions/${selected.id}/archive`, "Revision archived.")}><Archive size={14}/> Archive</button>
          </div>
          <p className="phase5-muted">Publishing here records the approved version and who published it. It does not write the live course files or bypass course importer validation.</p>
        </> : <p className="phase5-muted">Choose a revision or start a draft below.</p>}
      </section>
    </div>
    <section className="panel phase5-section">
      <div className="phase5-section-title"><div><div className="eyebrow">AUTHORING</div><h2>New revision draft</h2></div><Plus size={21}/></div>
      <form className="phase5-studio-form" onSubmit={createDraft}>
        <label>Course slug<input required maxLength={100} value={draft.course_slug} onChange={(event) => setDraft((value) => ({ ...value, course_slug: event.target.value }))}/></label>
        <label>Content type<select value={draft.content_type} onChange={(event) => setDraft((value) => ({ ...value, content_type: event.target.value }))}>{["course","module","lesson","project","reference","diagram"].map((type) => <option key={type} value={type}>{type}</option>)}</select></label>
        <label>Content slug<input required maxLength={180} value={draft.content_slug} onChange={(event) => setDraft((value) => ({ ...value, content_slug: event.target.value }))}/></label>
        <label className="phase5-studio-json-field">Content JSON<textarea rows={10} spellCheck="false" value={draft.content_json_text} onChange={(event) => setDraft((value) => ({ ...value, content_json_text: event.target.value }))}/></label>
        <button className="button button-primary" type="submit" disabled={busy}><Plus size={15}/> Save new version</button>
      </form>
    </section>
  </PageShell>;
}
