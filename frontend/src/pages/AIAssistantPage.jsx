import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, BrainCircuit, Code2, Crown, LoaderCircle, Send, ShieldCheck, Sparkles } from "lucide-react";
import { PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";

const REQUEST_KEY = () => typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
  ? crypto.randomUUID()
  : `${Date.now()}-${Math.random().toString(36).slice(2, 14)}`;

async function readResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail ?? payload.message ?? `Request failed (${response.status})`;
    if (detail && typeof detail === "object") {
      const error = new Error(detail.message || JSON.stringify(detail));
      error.code = detail.code;
      error.status = response.status;
      throw error;
    }
    const error = new Error(String(detail));
    error.status = response.status;
    throw error;
  }
  return payload;
}

export default function AIAssistantPage() {
  const [mode, setMode] = useState("tutor");
  const [prompt, setPrompt] = useState("");
  const [context, setContext] = useState("");
  const [language, setLanguage] = useState("javascript");
  const [code, setCode] = useState("");
  const [membership, setMembership] = useState(null);
  const [integrations, setIntegrations] = useState({ ai_available: false });
  const [loadingMembership, setLoadingMembership] = useState(true);
  const [working, setWorking] = useState(false);
  const [answer, setAnswer] = useState("");
  const [notice, setNotice] = useState("");
  const [noticeKind, setNoticeKind] = useState("info");
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [membershipResponse, plansResponse] = await Promise.all([
          apiFetch(`${API_BASE}/api/me/entitlements`, { credentials: "include" }),
          apiFetch(`${API_BASE}/api/plans`, { credentials: "include" }),
        ]);
        const payload = await readResponse(membershipResponse);
        const planCatalog = plansResponse.ok ? await plansResponse.json().catch(() => ({})) : {};
        if (active) {
          setMembership(payload);
          setIntegrations(planCatalog.integrations || { ai_available: false });
        }
      } catch (error) {
        if (active && error.status === 401) setMembership(null);
      } finally {
        if (active) setLoadingMembership(false);
      }
    })();
    return () => { active = false; };
  }, []);

  async function submit(event) {
    event.preventDefault();
    if (!prompt.trim()) {
      setNotice("Enter a question or review request first.");
      setNoticeKind("error");
      return;
    }
    if (mode === "review" && !code.trim()) {
      setNotice("Add the code you want reviewed first.");
      setNoticeKind("error");
      return;
    }
    setWorking(true);
    setAnswer("");
    setNotice("");
    try {
      const endpoint = mode === "review" ? "/api/me/ai/code-review" : "/api/me/ai/tutor";
      const response = await apiFetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "Idempotency-Key": REQUEST_KEY() },
        body: JSON.stringify({ prompt: prompt.trim(), context: context.trim(), language, code: code.slice(0, 16000) }),
      });
      const payload = await readResponse(response);
      setAnswer(payload.answer || "The configured provider returned no answer.");
      setNotice("Request completed. One request was charged to your daily AI allowance.");
      setNoticeKind("success");
      try {
        const refreshed = await apiFetch(`${API_BASE}/api/me/entitlements`, { credentials: "include" });
        if (refreshed.ok) setMembership(await refreshed.json());
      } catch { /* The generated answer is already displayed; allow a later status refresh. */ }
    } catch (error) {
      if (error.status === 401) {
        navigate(`/login?next=${encodeURIComponent("/ai")}`);
        return;
      }
      setNotice(error.message || "The AI request could not be completed.");
      setNoticeKind("error");
    } finally {
      setWorking(false);
    }
  }

  const currentPlan = membership?.current_plan?.id || "free";
  const entitled = currentPlan === "max" || currentPlan === "full_access";
  const allowance = membership?.limits?.ai_requests_per_day ?? (currentPlan === "pro" || currentPlan === "free" ? 0 : null);

  return (
    <PageShell className="ai-assistant-page">
      <div className="ai-assistant-hero">
        <div className="eyebrow"><Sparkles size={12} /> MAX & FULL ACCESS FEATURE</div>
        <h1>Learn with the CodeLeaf AI coach.</h1>
        <p>Ask programming questions or request a code review. Responses come from the configured AI provider; when the provider is unavailable, CodeLeaf reports the issue instead of inventing an answer.</p>
        <div className="ai-assistant-membership">
          <span><Crown size={15} /> {loadingMembership ? "Checking membership…" : `${membership?.current_plan?.title || "Free"} plan`}</span>
          <span>{loadingMembership ? "" : `${allowance ?? 0} AI requests per UTC day`}</span>
        </div>
      </div>

      {!loadingMembership && !entitled && (
        <section className="ai-lock-panel panel">
          <Crown size={20} />
          <div><strong>AI coaching is included with Max and Full Access.</strong><p>Your account can continue using all free learning content, exercises and certificates. Upgrade to unlock the AI tutor and code-review service.</p><Link to="/plans" className="button button-primary button-small">Compare plans <Crown size={13} /></Link></div>
        </section>
      )}

      {!loadingMembership && entitled && !integrations.ai_available && (
        <section className="ai-provider-unavailable panel" role="status">
          <AlertCircle size={18} />
          <div><strong>AI provider is not configured.</strong><p>The AI tutor and code review stay unavailable until the backend has <code>AI_API_BASE_URL</code>, <code>AI_API_KEY</code>, and <code>AI_MODEL</code> configured. No placeholder answers are generated.</p></div>
        </section>
      )}

      <div className={`ai-workspace panel ${!entitled ? "ai-workspace-locked" : ""}`}>
        <div className="ai-mode-tabs" role="tablist" aria-label="AI assistant mode">
          <button type="button" role="tab" aria-selected={mode === "tutor"} className={mode === "tutor" ? "active" : ""} onClick={() => { setMode("tutor"); setAnswer(""); setNotice(""); }}><BrainCircuit size={15} /> Ask tutor</button>
          <button type="button" role="tab" aria-selected={mode === "review"} className={mode === "review" ? "active" : ""} onClick={() => { setMode("review"); setAnswer(""); setNotice(""); }}><Code2 size={15} /> Review code</button>
        </div>
        <form onSubmit={submit} className="ai-assistant-form">
          <label htmlFor="ai-language">Programming language</label>
          <select id="ai-language" value={language} onChange={(event) => setLanguage(event.target.value)}>
            {["javascript", "python", "html", "css", "sql", "c", "cpp", "java", "php", "react", "other"].map((item) => <option key={item} value={item}>{item === "cpp" ? "C++" : item.charAt(0).toUpperCase() + item.slice(1)}</option>)}
          </select>
          <label htmlFor="ai-prompt">{mode === "review" ? "What should be reviewed?" : "What are you learning?"}</label>
          <textarea id="ai-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} maxLength={6000} rows={3} placeholder={mode === "review" ? "Review for correctness, readability, and edge cases…" : "Explain closures in JavaScript with a small example…"} required />
          <label htmlFor="ai-context">Extra context <span>(optional)</span></label>
          <textarea id="ai-context" value={context} onChange={(event) => setContext(event.target.value)} maxLength={4000} rows={2} placeholder="What have you tried? What part is confusing?" />
          {mode === "review" && <><label htmlFor="ai-code">Code to review</label><textarea id="ai-code" className="ai-code-input" value={code} onChange={(event) => setCode(event.target.value)} maxLength={16000} rows={10} spellCheck="false" placeholder="Paste code here…" required /></>}
          <div className="ai-submit-row"><span><ShieldCheck size={14} /> Code is sent to the configured AI provider for this request.</span><button className="button button-primary" type="submit" disabled={working || !entitled}>{working ? <><LoaderCircle size={15} className="ai-spin" /> Processing…</> : <><Send size={15} /> Send request</>}</button></div>
        </form>
        {notice && <div className={`ai-notice ai-notice-${noticeKind}`} role="status"><AlertCircle size={15} /> <span>{notice}</span></div>}
        {answer && <section className="ai-answer"><div className="ai-answer-heading"><Sparkles size={16} /> <strong>{mode === "review" ? "Code review" : "Tutor response"}</strong></div><div className="ai-answer-content">{answer}</div></section>}
      </div>
      <p className="ai-disclaimer">AI responses can be wrong. Review suggestions carefully and never paste passwords, API keys or other secrets. This assistant does not execute code and does not replace the isolated CodeLeaf runner.</p>
    </PageShell>
  );
}
