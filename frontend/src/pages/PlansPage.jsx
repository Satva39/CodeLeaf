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
  const [cancelPending, setCancelPending] = useState("");
  const navigate = useNavigate();
  async function refreshBilling() {
    try {
      const response = await apiFetch(`${API_BASE}/api/me/billing`, {
        credentials: "include",
      });
      if (!response.ok) {
        if (response.status === 401) setBilling(null);
        return;
      }
      setBilling(await response.json());
    } catch {
      /* Public pricing remains available when the account API is offline. */
    }
  }
  useEffect(() => {
    refreshBilling();
  }, []);
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
        {PLANS.map((p) => (
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
              {p.id === "free" && (
                <span className="plan-current">START HERE</span>
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
              disabled={pending === p.id}
              onClick={() => choosePlan(p)}
            >
              {pending === p.id ? "Preparing..." : p.action}{" "}
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
        ))}
      </div>
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
      </div>
    </PageShell>
  );
}
