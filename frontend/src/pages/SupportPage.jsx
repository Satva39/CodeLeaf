import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, LifeBuoy, RefreshCw, Send } from "lucide-react";
import { PageShell, EmptyState } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";

async function readPayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    const error = new Error(typeof detail === "string" ? detail : detail?.message || "The support request could not be completed.");
    error.status = response.status;
    throw error;
  }
  return payload;
}

export default function SupportPage() {
  const navigate = useNavigate();
  const [membership, setMembership] = useState(null);
  const [items, setItems] = useState([]);
  const [subject, setSubject] = useState("");
  const [category, setCategory] = useState("general");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    setError("");
    try {
      const [supportResponse, planResponse] = await Promise.all([
        apiFetch(`${API_BASE}/api/me/support-requests`, { credentials: "include" }),
        apiFetch(`${API_BASE}/api/me/entitlements`, { credentials: "include" }),
      ]);
      const support = await readPayload(supportResponse);
      const plan = await readPayload(planResponse);
      setItems(Array.isArray(support.items) ? support.items : []);
      setMembership(plan);
    } catch (err) {
      if (err.status === 401) setError("Sign in to create and track support requests.");
      else setError(err.message || "Support requests could not be loaded.");
    } finally { setLoading(false); }
  }

  useEffect(() => { void refresh(); }, []);

  async function submit(event) {
    event.preventDefault();
    setBusy(true); setNotice(""); setError("");
    try {
      const payload = await readPayload(await apiFetch(`${API_BASE}/api/me/support-requests`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: subject.trim(), category, message: message.trim() }),
      }));
      setNotice(payload.message || "Support request saved.");
      setSubject(""); setMessage("");
      await refresh();
    } catch (err) {
      if (err.status === 401) { navigate(`/login?next=${encodeURIComponent("/support")}`); return; }
      setError(err.message || "Support request could not be saved.");
    } finally { setBusy(false); }
  }

  const planId = membership?.current_plan?.id || "free";
  const queue = ["max", "full_access"].includes(planId) ? "Priority" : planId === "pro" ? "Standard" : "General";

  return <PageShell className="support-page narrow-page">
    <header className="support-hero panel"><span className="support-hero-icon"><LifeBuoy size={26} /></span><div><div className="eyebrow">CODELEAF HELP DESK</div><h1>How can we help?</h1><p>Submit a request and check its status here. Queue priority is derived from your verified account plan, not a form selection.</p><div className="support-plan-pill">Current queue: <strong>{queue}</strong>{membership?.current_plan?.title ? ` · ${membership.current_plan.title}` : ""}</div></div></header>
    {(error || notice) && <div className={`panel support-notice ${error ? "is-error" : "is-success"}`} role="status">{error || notice}{error.includes("Sign in") && <> <Link to={`/login?next=${encodeURIComponent("/support")}`}>Sign in <ArrowRight size={13} /></Link></>}</div>}
    <section className="support-form-panel panel"><div className="section-title-row"><div><div className="eyebrow">NEW REQUEST</div><h2>Tell us what happened</h2></div></div><form onSubmit={submit} className="support-form"><label htmlFor="support-category">Category</label><select id="support-category" value={category} onChange={(event) => setCategory(event.target.value)}><option value="general">General question</option><option value="billing">Billing or subscription</option><option value="account">Account or login</option><option value="course_content">Course content</option><option value="project">Projects and portfolio</option><option value="runner">Code runner</option><option value="ai">AI tools</option><option value="bug">Report a bug</option></select><label htmlFor="support-subject">Subject</label><input id="support-subject" value={subject} onChange={(event) => setSubject(event.target.value)} maxLength={160} minLength={3} required placeholder="Briefly describe the issue"/><label htmlFor="support-message">Details</label><textarea id="support-message" value={message} onChange={(event) => setMessage(event.target.value)} minLength={10} maxLength={5000} required rows={6} placeholder="What were you trying to do, and what happened? Do not include passwords, payment secrets, or private authentication codes."/><p className="support-privacy-note">Avoid including passwords, card numbers, API keys, or private authentication codes. A maximum of 10 requests may remain open per account.</p><button type="submit" className="button button-primary" disabled={busy}>{busy ? "Sending…" : "Submit support request"} <Send size={15}/></button></form></section>
    <section className="support-history panel"><div className="section-title-row"><div><div className="eyebrow">YOUR REQUESTS</div><h2>Support history</h2></div><button type="button" className="button button-secondary button-small" onClick={() => void refresh()} disabled={loading}><RefreshCw size={14}/> Refresh</button></div>{loading ? <p>Loading support history…</p> : items.length ? <div className="support-request-list">{items.map((item) => <article className="support-request-item" key={item.id}><div className="support-request-top"><div><strong>{item.subject}</strong><small>{item.category.replaceAll("_", " ")} · {new Date(item.created_at).toLocaleString("en-IN")}</small></div><div className="support-request-tags"><span className={`support-status status-${item.status}`}>{item.status.replaceAll("_", " ")}</span><span className={`support-priority priority-${item.priority}`}>{item.priority} queue</span></div></div><p>{item.message}</p>{item.staff_reply && <blockquote><strong>CodeLeaf support</strong><p>{item.staff_reply}</p></blockquote>}</article>)}</div> : <EmptyState title="No support requests yet" detail="Requests you submit will appear here with their current status."/>}</section>
  </PageShell>;
}
