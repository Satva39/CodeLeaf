import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  CircleHelp,
  Compass,
  Settings,
  ShieldCheck,
  Sparkles,
  Star,
  Zap,
} from "lucide-react";
import { PLANS } from "../data.js";
import { hasCompletePlanCatalog, mergePlanCatalog, normalizePlanCatalogPayload } from "../lib/planCatalog.js";
import { API_BASE } from "../lib/demoState.js";
import { PageShell } from "../components/common.jsx";

function loadRazorpayCheckout() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const existing = document.querySelector(
      'script[data-razorpay-checkout="true"]',
    );
    if (existing) {
      existing.addEventListener("load", () => resolve(true), { once: true });
      existing.addEventListener(
        "error",
        () => reject(new Error("Could not load Razorpay Checkout.")),
        { once: true },
      );
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.dataset.razorpayCheckout = "true";
    script.onload = () => resolve(true);
    script.onerror = () =>
      reject(
        new Error(
          "Could not load Razorpay Checkout. Check your connection and try again.",
        ),
      );
    document.body.appendChild(script);
  });
}

export default function PlansPage() {
  const [pending, setPending] = useState("");
  const [checkoutMessage, setCheckoutMessage] = useState("");
  const [billing, setBilling] = useState(null);
  const [entitlements, setEntitlements] = useState(null);
  const [planCatalog, setPlanCatalog] = useState([]);
  const [catalogStatus, setCatalogStatus] = useState("loading");
  const [integrations, setIntegrations] = useState({ ai_available: false, supported_runner_languages: ["python", "javascript"] });
  const [cancelPending, setCancelPending] = useState("");
  const navigate = useNavigate();
  async function refreshBilling() {
    try {
      const [billingResponse, entitlementResponse, catalogResponse] = await Promise.all([
        apiFetch(`${API_BASE}/api/me/billing`, { credentials: "include" }),
        apiFetch(`${API_BASE}/api/me/entitlements`, { credentials: "include" }),
        apiFetch(`${API_BASE}/api/plans`, { credentials: "include" }),
      ]);
      if (billingResponse.ok) setBilling(await billingResponse.json());
      else if (billingResponse.status === 401) setBilling(null);
      if (entitlementResponse.ok) setEntitlements(await entitlementResponse.json());
      else if (entitlementResponse.status === 401) setEntitlements(null);
      if (catalogResponse.ok) {
        const catalog = await catalogResponse.json();
        const items = normalizePlanCatalogPayload(catalog);
        setPlanCatalog(items);
        setCatalogStatus(hasCompletePlanCatalog(items) ? "live" : "fallback");
        setIntegrations(catalog.integrations || { ai_available: false, supported_runner_languages: ["python", "javascript"] });
      } else {
        setPlanCatalog([]);
        setCatalogStatus("fallback");
      }
    } catch {
      setPlanCatalog([]);
      setCatalogStatus("fallback");
      /* The public comparison has a complete local fallback if the API is offline. */
    }
  }
  useEffect(() => {
    void refreshBilling();
  }, []);
  const currentPlanId = entitlements?.current_plan?.id
    || billing?.current_plan?.id
    || (typeof billing?.current_plan === "string" ? billing.current_plan : "");
  const planPriority = { free: 0, pro: 1, max: 2, full_access: 3 };
  const planById = useMemo(() => new Map(mergePlanCatalog(planCatalog).map((plan) => [plan.id, plan])), [planCatalog]);
  const money = (paise) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format((Number(paise) || 0) / 100);
  const formatBytes = (value) => {
    const bytes = Number(value) || 0;
    if (bytes >= 1024 ** 3) return `${(bytes / (1024 ** 3)).toFixed(bytes % (1024 ** 3) ? 1 : 0)} GB`;
    if (bytes >= 1024 ** 2) return `${Math.round(bytes / (1024 ** 2))} MB`;
    return `${bytes} B`;
  };
  const comparisonRows = [
    { label: "Published tutorials, references and standard lessons", kind: "feature", key: "published_learning" },
    { label: "Standard exercises, progress, XP and streaks", kind: "feature", key: "learning_progress" },
    { label: "Available course certification exams and earned certificates", kind: "feature", key: "course_exams" },
    { label: "Public project browsing and personal portfolio", kind: "feature", key: "portfolio" },
    { label: "Advanced learning analytics and performance reports", kind: "feature", key: "advanced_analytics" },
    { label: "Activity-based personalized recommendations", kind: "feature", key: "personalized_recommendations" },
    { label: "Expanded practice collections and timed mock assessments", kind: "feature", key: "premium_practice" },
    { label: "Professional, specialist and capstone practice sets", kind: "feature", key: "premium_practice_sets" },
    { label: "Saved project milestone checklists", kind: "feature", key: "project_planning" },
    { label: "Weekly and all-time learning leaderboards", kind: "feature", key: "leaderboards" },
    { label: "Premium capstones and interview-preparation projects", kind: "feature", key: "premium_projects" },
    { label: "AI tutor and AI code review when configured", kind: "feature", key: "ai_tutor" },
    { label: "Ad-free learning", kind: "feature", key: "ad_free" },
    { label: "XP multiplier", kind: "limit", key: "xp_multiplier", format: (value) => `${value}×` },
    { label: "Saved workspaces", kind: "limit", key: "workspaces" },
    { label: "Saved code snippets", kind: "limit", key: "saved_snippets" },
    { label: "Total portfolio / project storage", kind: "limit", key: "project_storage_bytes", format: formatBytes },
    { label: "Supported code executions per day", kind: "limit", key: "code_executions_per_day" },
    { label: "AI requests per day", kind: "limit", key: "ai_requests_per_day" },
    { label: "Maximum individual ZIP size", kind: "limit", key: "max_single_zip_bytes", format: formatBytes },
    { label: "Advertisements", kind: "limit", key: "ads_enabled", format: (value) => value ? "Shown" : "Ad-free" },
    { label: "Support queue", kind: "support" },
    { label: "Lifetime entitlement", kind: "lifetime" },
    { label: "Earned certificates and saved work after paid expiry", kind: "retained_data" },
  ];
  async function cancelSubscription(subscription) {
    if (
      !window.confirm(
        "Request cancellation of auto-renewal at the end of the current billing period?",
      )
    )
      return;
    setCancelPending(subscription.subscription_id);
    setCheckoutMessage("");
    try {
      const response = await apiFetch(
        `${API_BASE}/api/payments/${encodeURIComponent(subscription.subscription_id)}/cancel`,
        { method: "POST", credentials: "include" },
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(data.detail || "Could not request cancellation.");
      setCheckoutMessage(
        "Cancellation requested. Your paid access should remain available until the current cycle ends.",
      );
      await refreshBilling();
    } catch (error) {
      setCheckoutMessage(error.message || "Could not cancel the subscription.");
    } finally {
      setCancelPending("");
    }
  }
  async function choosePlan(plan) {
    if (plan.id === "free") {
      setCheckoutMessage(
        "The free plan is ready to explore. Open any public tutorial to start learning.",
      );
      return;
    }
    setPending(plan.id);
    setCheckoutMessage("");
    try {
      const response = await apiFetch(`${API_BASE}/api/payments/create`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: plan.id }),
      });
      const data = await response.json().catch(() => ({}));
      if (response.status === 401) {
        navigate(`/login?next=${encodeURIComponent("/plans")}`);
        return;
      }
      if (!response.ok)
        throw new Error(data.detail || "Payment setup is not configured yet.");
      await loadRazorpayCheckout();
      if (data.kind === "order") {
        const checkout = new window.Razorpay({
          key: data.key_id,
          amount: data.amount,
          currency: data.currency,
          name: data.name,
          description: data.description,
          order_id: data.order_id,
          prefill: data.prefill,
          theme: { color: "#13b981" },
          handler: async (result) => {
            try {
              const verify = await apiFetch(`${API_BASE}/api/payments/verify`, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  plan_id: "full_access",
                  razorpay_order_id: result.razorpay_order_id,
                  razorpay_payment_id: result.razorpay_payment_id,
                  razorpay_signature: result.razorpay_signature,
                }),
              });
              const verified = await verify.json().catch(() => ({}));
              if (!verify.ok)
                throw new Error(
                  verified.detail || "Payment verification failed.",
                );
              setCheckoutMessage(
                "Payment verified. Full Access is enabled on your account.",
              );
              await refreshBilling();
            } catch (error) {
              setCheckoutMessage(
                `${error.message || "Verification is pending."} Your payment will be reconciled through the signed provider webhook.`,
              );
            }
          },
          modal: {
            ondismiss: () =>
              setCheckoutMessage(
                "Checkout closed. No access is granted unless payment is verified.",
              ),
          },
        });
        checkout.on("payment.failed", (event) =>
          setCheckoutMessage(
            event?.error?.description ||
              "Payment failed. No plan access was granted.",
          ),
        );
        checkout.open();
      } else if (data.kind === "subscription") {
        const checkout = new window.Razorpay({
          key: data.key_id,
          subscription_id: data.subscription_id,
          name: data.name,
          description: data.description,
          prefill: data.prefill,
          theme: { color: plan.id === "max" ? "#9164f5" : "#13b981" },
          handler: async (result) => {
            try {
              const verify = await apiFetch(
                `${API_BASE}/api/payments/verify-subscription`,
                {
                  method: "POST",
                  credentials: "include",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify(result),
                },
              );
              const verified = await verify.json().catch(() => ({}));
              if (!verify.ok)
                throw new Error(
                  verified.detail || "Subscription verification is pending.",
                );
              setCheckoutMessage(
                `${plan.title} subscription payment verified. Account access is being reconciled with Razorpay.`,
              );
              await refreshBilling();
            } catch (error) {
              setCheckoutMessage(
                `${error.message || "Verification is pending."} Access will only be enabled by verified provider events.`,
              );
            }
          },
          modal: {
            ondismiss: () =>
              setCheckoutMessage(
                "Checkout closed. No subscription access is granted unless payment is verified.",
              ),
          },
        });
        checkout.on("payment.failed", (event) =>
          setCheckoutMessage(
            event?.error?.description || "Subscription payment failed.",
          ),
        );
        checkout.open();
      }
    } catch (error) {
      setCheckoutMessage(
        error.message ||
          "The payment service is not configured. Plans remain visible in demo mode.",
      );
    } finally {
      setPending("");
    }
  }
  return (
    <PageShell>
      <div className="plans-page-head">
        <div className="eyebrow">PICK YOUR PACE</div>
        <h1>A plan for every kind of learner.</h1>
        <p>Start free, build a habit, and unlock more when you're ready.</p>
        <div className="pricing-units">
          <span>Prices in INR</span>
          <span>Monthly membership or one-time lifetime access</span>
        </div>
      </div>
      <div className="plan-grid">
        {PLANS.map((basePlan) => {
          const serverPlan = planById.get(basePlan.id);
          const p = serverPlan ? {
            ...basePlan,
            title: serverPlan.title || basePlan.title,
            price: money(serverPlan.amount_paise),
            billing: serverPlan.billing === "monthly" ? "per month" : serverPlan.billing === "lifetime" ? "one-time · lifetime access" : "Free forever",
          } : basePlan;
          const isCurrent = currentPlanId === p.id;
          const includedInCurrent = Boolean(currentPlanId && (planPriority[currentPlanId] ?? -1) > (planPriority[p.id] ?? -1));
          const lifetimeActive = currentPlanId === "full_access";
          return (
          <div
            key={p.id}
            className={`plan-card plan-${p.tone} panel ${p.popular ? "plan-popular" : ""}`}
          >
            <div className="plan-card-ribbon">
              {p.popular ? (
                <>
                  <Sparkles size={12} /> RECOMMENDED
                </>
              ) : p.id === "full_access" ? (
                <>
                  <Star size={12} /> LIFETIME
                </>
              ) : p.id === "pro" ? (
                <>
                  <Zap size={12} /> FOR REGULAR LEARNERS
                </>
              ) : (
                <>
                  <Compass size={12} /> GET STARTED
                </>
              )}
            </div>
            <div className="plan-card-title-row">
              <h2>{p.title}</h2>
              {isCurrent && (
                <span className="plan-current">CURRENT PLAN</span>
              )}
            </div>
            <p className="plan-note">{p.note}</p>
            <div className="plan-price">
              <strong>{p.price}</strong>
              <span>{p.billing}</span>
            </div>
            <div className="plan-divider" />
            <ul>
              {p.features.map((f) => (
                <li key={f}>
                  <Check size={16} />
                  {f}
                </li>
              ))}
            </ul>
            <button
              className={`button ${p.id === "max" ? "button-violet" : p.id === "full_access" ? "button-dark" : "button-primary"} button-wide`}
              disabled={pending === p.id || isCurrent || includedInCurrent || lifetimeActive}
              onClick={() => choosePlan(p)}
            >
              {pending === p.id ? "Preparing..." : isCurrent ? "Current plan" : includedInCurrent ? `Included with ${PLANS.find((item) => item.id === currentPlanId)?.title || currentPlanId}` : lifetimeActive ? "Lifetime access active" : p.action}{" "}
              <ArrowRight size={15} />
            </button>
            {p.id !== "full_access" && p.id !== "free" && (
              <small className="plan-footnote">
                Monthly renewal; you can cancel auto-renewal any time.
              </small>
            )}
            {p.id === "full_access" && (
              <small className="plan-footnote">
                One payment; lifetime access is subject to published platform
                terms.
              </small>
            )}
          </div>
          );
        })}
      </div>
      <section className="lifetime-terms panel" aria-labelledby="lifetime-access-terms-title">
        <div className="eyebrow">FULL ACCESS · LIFETIME TERMS</div>
        <h2 id="lifetime-access-terms-title">One payment, while CodeLeaf continues to operate</h2>
        <p>Full Access is a ₹49,999 one-time purchase and does not renew monthly. “Lifetime” means the lifetime of CodeLeaf’s standard individual learning service; it cannot guarantee service if CodeLeaf permanently discontinues that product.</p>
        <p>Fair-use limits still apply: up to 100 GB of project storage, 200 saved workspaces, 500 MB per ZIP, and 1,500 supported code executions per UTC day. The allowance of up to 150 AI requests per UTC day applies only while a supported AI provider is configured and available. Provider outages, supported-runtime limits, and reasonable abuse-prevention controls still apply; third-party API access is not promised as unlimited.</p>
        <p>Earned certificates and existing learner work are retained if a monthly subscription expires. Full Access remains independent of monthly subscription renewal.</p>
      </section>
      <section className="plan-comparison panel">
        <div className="section-title-row">
          <div>
            <div className="eyebrow">COMPARE PLANS</div>
            <h2>Know exactly what changes</h2>
            <p>{catalogStatus === "live" ? "Prices and allowances come from CodeLeaf's server-side plan catalog." : "Plan inclusions are shown from CodeLeaf's configured defaults until the live catalog is available."}</p>
          </div>
        </div>
        <div className="plan-comparison-scroll">
          <table className="plan-comparison-table">
            <thead><tr><th scope="col">Feature or allowance</th>{PLANS.map((p) => <th key={p.id} scope="col">{p.title}</th>)}</tr></thead>
            <tbody>
              <tr className="plan-comparison-price-row"><th scope="row">Price</th>{PLANS.map((p) => { const serverPlan = planById.get(p.id); return <td key={p.id}>{serverPlan ? money(serverPlan.amount_paise) : p.price}<small>{p.id === "pro" || p.id === "max" ? "/month" : p.id === "full_access" ? "one-time" : "forever"}</small></td>; })}</tr>
              {comparisonRows.map((row) => <tr key={row.label}><th scope="row">{row.label}</th>{PLANS.map((p) => {
                const plan = planById.get(p.id);
                const value = row.kind === "feature" ? plan?.features?.[row.key] : plan?.limits?.[row.key];
                let shown;
                if (row.kind === "feature") {
                  if (value === true && row.key === "ai_tutor" && !integrations.ai_available) shown = "Included · provider unavailable";
                  else shown = value === true ? "Included" : "Not included";
                }
                else if (row.kind === "support") shown = p.id === "max" || p.id === "full_access" ? "Priority" : p.id === "pro" ? "Standard" : "No priority queue";
                else if (row.kind === "lifetime") shown = p.id === "full_access" ? "Yes · one-time" : "No";
                else if (row.kind === "retained_data") shown = "Yes";
                else shown = row.format ? row.format(value ?? (row.key === "max_single_zip_bytes" ? 500 * 1024 * 1024 : 0)) : new Intl.NumberFormat("en-IN").format(Number(value) || 0);
                const included = (row.kind === "feature" && value === true) || (row.kind === "support" && p.id !== "free") || (row.kind === "lifetime" && p.id === "full_access") || row.kind === "retained_data";
                return <td key={p.id} className={included ? "plan-cell-included" : ""}>{shown}</td>;
              })}</tr>)}
            </tbody>
          </table>
        </div>
        {catalogStatus !== "live" && <p className="plan-catalog-fallback" role="status">The live plan catalog is unavailable or incomplete, so this table is using CodeLeaf's configured plan defaults. These display values do not grant access; the backend still enforces account entitlements. Refresh the page or check the Render API deployment if this message persists.</p>}
        <p className="plan-comparison-note">Daily usage windows reset at 00:00 UTC. The execution quota applies only to the configured runtimes ({(integrations.supported_runner_languages || ["python", "javascript"]).join(" and ")}). {integrations.ai_available ? "An AI provider is configured; service availability and daily allowances still apply." : "AI is currently unavailable because the backend has no complete AI provider configuration. No simulated responses are supplied."}</p>
      </section>
      {entitlements?.current_plan && (
        <section className="membership-usage-panel panel">
          <div className="section-title-row">
            <div><div className="eyebrow">ACCOUNT OVERVIEW</div><h2>{entitlements.current_plan.title} membership</h2><p>{entitlements.current_plan.lifetime ? "Lifetime individual access · no recurring renewal." : entitlements.current_plan.period_ends_at ? `Current paid period ends ${new Date(entitlements.current_plan.period_ends_at).toLocaleDateString("en-IN")}.` : entitlements.current_plan.id === "free" ? "Free access remains available after any paid period ends." : "Membership status is derived from verified account records."}</p></div>
            <button className="button button-secondary button-small" onClick={() => void refreshBilling()}>Refresh status</button>
          </div>
          <div className="usage-grid">
            {[
              { key: "workspaces", title: "Saved workspaces", format: (v) => `${v.used} / ${v.limit}` },
              { key: "saved_snippets", title: "Saved snippets", format: (v) => `${v.used} / ${v.limit}` },
              { key: "project_storage_bytes", title: "Project storage", format: (v) => `${formatBytes(v.used)} / ${formatBytes(v.limit)}` },
              { key: "code_executions_per_day", title: "Code runs today", format: (v) => `${v.used} / ${v.limit}` },
              { key: "ai_requests_per_day", title: "AI requests today", format: (v) => `${v.used} / ${v.limit}` },
            ].map((item) => {
              const usage = entitlements.usage?.[item.key] || { used: 0, limit: 0 };
              const percent = Number(usage.limit) > 0 ? Math.min(100, Math.max(0, Number(usage.used) / Number(usage.limit) * 100)) : 0;
              return <div className="usage-meter" key={item.key}><div className="usage-meter-top"><strong>{item.title}</strong><span>{item.format(usage)}</span></div><div className="usage-meter-track" aria-label={`${item.title}: ${item.format(usage)}`}><span style={{ width: `${percent}%` }} /></div></div>;
            })}
          </div>
          <small className="usage-timezone">Usage date: {entitlements.usage?.date || "—"} · timezone: {entitlements.usage?.timezone || "UTC"}</small>
        </section>
      )}
      {billing &&
        ((billing.entitlements || []).length > 0 ||
          (billing.subscriptions || []).length > 0) && (
          <section className="billing-panel panel">
            <div className="section-title-row">
              <div>
                <div className="eyebrow">YOUR MEMBERSHIP</div>
                <h2>Plans on this account</h2>
              </div>
              <button
                className="button button-secondary button-small"
                onClick={refreshBilling}
              >
                Refresh status
              </button>
            </div>
            {(billing.entitlements || []).map((ent, index) => (
              <div
                className="billing-entitlement"
                key={`${ent.plan_id}-${index}`}
              >
                <span className="billing-entitlement-icon">
                  <CheckCircle2 size={17} />
                </span>
                <div>
                  <strong>
                    {PLANS.find((x) => x.id === ent.plan_id)?.title ||
                      ent.plan_id}
                  </strong>
                  <small>
                    {ent.ends_at
                      ? `Access until ${new Date(ent.ends_at).toLocaleDateString("en-IN")}`
                      : "Active access"}
                  </small>
                </div>
                <span className="pill pill-mint">ACTIVE</span>
              </div>
            ))}
            {(billing.subscriptions || []).map((subscription) => (
              <div
                className="billing-subscription"
                key={subscription.subscription_id}
              >
                <div>
                  <strong>
                    {PLANS.find((x) => x.id === subscription.plan_id)?.title ||
                      subscription.plan_id}{" "}
                    renewal
                  </strong>
                  <small>
                    Status: {subscription.status}
                    {subscription.ends_at
                      ? ` · Current period ends ${new Date(subscription.ends_at).toLocaleDateString("en-IN")}`
                      : ""}
                  </small>
                  {subscription.cancellation_scheduled && <small className="billing-warning">Auto-renewal cancellation is scheduled. Current verified access remains subject to the provider period end.</small>}
                  {subscription.cancellation_required && <small className="billing-warning">Action required: CodeLeaf could not confirm cancellation of this older subscription. Contact support and check Razorpay to avoid overlapping renewals.</small>}
                </div>
                {subscription.cancelable && (
                  <button
                    className="button button-secondary button-small"
                    disabled={cancelPending === subscription.subscription_id}
                    onClick={() => cancelSubscription(subscription)}
                  >
                    {cancelPending === subscription.subscription_id
                      ? "Requesting…"
                      : "Cancel renewal"}
                  </button>
                )}
              </div>
            ))}
          </section>
        )}
      {checkoutMessage && (
        <div role="status" className="checkout-message panel">
          <CircleHelp size={17} />
          {checkoutMessage}
        </div>
      )}
      <div className="pricing-notes">
        <div>
          <ShieldCheck size={19} />
          <span>
            <strong>Secure payment flow</strong>
            <small>Razorpay credentials stay on the backend.</small>
          </span>
        </div>
        <div>
          <BookOpen size={19} />
          <span>
            <strong>Learn on your terms</strong>
            <small>Start with the free course catalog.</small>
          </span>
        </div>
        <div>
          <Settings size={19} />
          <span>
            <strong>Clear entitlements</strong>
            <small>Plan features are enforced server-side.</small>
          </span>
        </div>
      </div>
      <div className="pricing-disclaimer">
        Final production checkout requires an authenticated account, verified
        Razorpay payment callbacks, signed webhooks, billing terms and
        successful test-mode reconciliation.
        <p>Need account or billing help? <a href="/support">Open a CodeLeaf support request</a>. Max and Full Access requests enter the priority queue; Pro requests enter the standard queue.</p>
      </div>
    </PageShell>
  );
}
