import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ArrowRight, CircleHelp, Code2, Eye, EyeOff, RefreshCw, ShieldCheck } from "lucide-react";

import { API_BASE } from "../lib/demoState.js";
import { apiFetch } from "../lib/apiClient.js";
import { PageShell } from "../components/common.jsx";

export default function AuthPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const path = location.pathname;
  const isRegister = path === "/register";
  const isForgot = path === "/forgot-password";
  const isVerify = path === "/verify-email";
  const isVerifyEmailChange = path === "/verify-email-change";
  const isReset = path === "/reset-password";
  const isActionLink = isVerify || isVerifyEmailChange;
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [resending, setResending] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [testUrl, setTestUrl] = useState("");

  useEffect(() => {
    const hint = new URLSearchParams(location.search).get("email");
    if (hint && !email) setEmail(hint);
  }, [location.search]);

  useEffect(() => {
    setShowPassword(false);
    setResending(false);
  }, [path]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    setTestUrl("");
    try {
      let endpoint = "";
      let payload = {};
      if (isActionLink) {
        endpoint = isVerifyEmailChange ? "/api/auth/verify-email-change" : "/api/auth/verify-email";
        payload = { token: new URLSearchParams(location.search).get("token") || "" };
      } else if (isReset) {
        endpoint = "/api/auth/reset-password";
        payload = { token: new URLSearchParams(location.search).get("token") || "", password };
      } else if (isForgot) {
        endpoint = "/api/auth/forgot-password";
        payload = { email };
      } else {
        endpoint = `/api/auth/${isRegister ? "register" : "login"}`;
        payload = isRegister ? { display_name: name, username, email, password } : { email, password };
      }
      const response = await apiFetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Account service is unavailable.");
      if (data.test_url) setTestUrl(data.test_url);

      if (isActionLink) {
        setMessage(isVerifyEmailChange
          ? "Your email address is verified. Sign in again with the new address."
          : "Email verified. You can now sign in to CodeLeaf.");
        if (isVerifyEmailChange) window.dispatchEvent(new CustomEvent("codeleaf:auth-changed", { detail: { authenticated: false } }));
      } else if (isReset) {
        setMessage("Password updated. Sign in with your new password.");
        window.dispatchEvent(new CustomEvent("codeleaf:auth-changed", { detail: { authenticated: false } }));
      } else if (isForgot || isRegister) {
        setMessage(data.message || (isForgot ? "If an eligible account exists, reset instructions will be sent." : "Check your email for a verification link."));
      } else {
        window.dispatchEvent(new CustomEvent("codeleaf:auth-changed", { detail: { authenticated: true } }));
        const next = new URLSearchParams(location.search).get("next") || "/profile";
        navigate(next.startsWith("/") && !next.startsWith("//") ? next : "/profile");
      }
    } catch (error) {
      setMessage(error.message || "Could not complete the account request.");
    } finally {
      setBusy(false);
    }
  }

  async function resendVerification() {
    setBusy(true);
    setResending(true);
    setMessage("");
    setTestUrl("");
    try {
      const response = await apiFetch(`${API_BASE}/api/auth/verification/resend`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Could not request another verification link.");
      setMessage(data.message || "If the account needs verification, an email will be sent.");
      setTestUrl(data.test_url || "");
    } catch (error) {
      setMessage(error.message || "Could not request another verification link.");
    } finally {
      setBusy(false);
      setResending(false);
    }
  }

  const title = isActionLink
    ? (isVerifyEmailChange ? "Confirm your new email" : "Verify your email")
    : isReset ? "Choose a new password"
    : isForgot ? "Reset your password"
    : isRegister ? "Create your account" : "Welcome back";

  return (
    <PageShell className="auth-page">
      <div className="auth-card panel">
        <div className="auth-mark"><Code2 size={24} /></div>
        <div className="eyebrow">YOUR LEARNING SPACE</div>
        <h1>{title}</h1>
        <p>
          {isActionLink ? "Confirm the one-time link to finish the account change."
            : isReset ? "Use a new password of at least 10 characters."
            : isForgot ? "Enter your account email. If it is eligible, reset instructions will be sent."
            : isRegister ? "Verify your email to protect your account and keep your learning progress together."
            : "Sign in to continue your learning journey and access your account."}
        </p>

        {!isActionLink && (
          <form onSubmit={submit} className="auth-form">
            {isRegister && <>
              <label>Display name<input value={name} onChange={(e) => setName(e.target.value)} required minLength={2} maxLength={80} autoComplete="name" /></label>
              <label>Username<input value={username} onChange={(e) => setUsername(e.target.value.replace(/[^a-zA-Z0-9_]/g, "").slice(0, 40))} required minLength={3} maxLength={40} autoComplete="username" /></label>
            </>}
            {!isReset && <label>Email address<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required maxLength={320} autoComplete="email" /></label>}
            {!isForgot && <div className="auth-password-field">
              <label htmlFor="auth-password">Password</label>
              <div className="auth-password-control">
                <input id="auth-password" type={showPassword ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} required minLength={isRegister || isReset ? 10 : 1} maxLength={128} autoComplete={isRegister || isReset ? "new-password" : "current-password"} />
                <button
                  type="button"
                  className="auth-password-toggle"
                  onClick={() => setShowPassword((visible) => !visible)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  aria-pressed={showPassword}
                  aria-controls="auth-password"
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}
                </button>
              </div>
              {(isRegister || isReset) && <small>Use at least 10 characters.</small>}
            </div>}
            <button className="button button-primary button-wide" disabled={busy}>
              {busy ? "Please wait…" : isReset ? "Update password" : isForgot ? "Send reset link" : isRegister ? "Create account" : "Sign in"} <ArrowRight size={15} />
            </button>
          </form>
        )}

        {isActionLink && <button type="button" className="button button-primary button-wide" disabled={busy || !new URLSearchParams(location.search).get("token")} onClick={submit}>{busy ? "Please wait…" : "Confirm"} <ArrowRight size={15} /></button>}
        {message && <div className="checkout-message" role="status"><CircleHelp size={16} />{message}</div>}
        {testUrl && <p className="profile-save-note" role="status">Local test mode only: no email was sent. <a href={testUrl}>Open the one-time action link</a>.</p>}
        {isRegister && (message || resending) && <button
          type="button"
          className="button button-secondary button-wide auth-resend-button"
          onClick={resendVerification}
          disabled={busy || !email}
          aria-busy={resending}
        >
          <RefreshCw size={16} className={resending ? "auth-resend-icon is-spinning" : "auth-resend-icon"} aria-hidden="true" />
          <span>{resending ? "Sending verification link…" : "Resend verification link"}</span>
          <ArrowRight size={15} className="auth-resend-arrow" aria-hidden="true" />
        </button>}
        {isActionLink && message && <p><Link to="/login">Go to sign in</Link></p>}
        {isReset && message && <p><Link to="/login">Go to sign in</Link></p>}
        {isForgot && <div className="auth-switch"><Link to="/login">Back to sign in</Link></div>}
        {!isForgot && !isActionLink && !isReset && <div className="auth-switch">{isRegister ? "Already have an account?" : "New to CodeLeaf?"} <Link to={isRegister ? `/login${location.search}` : `/register${location.search}`}>{isRegister ? "Sign in" : "Create account"}</Link></div>}
        {!isForgot && !isRegister && !isReset && !isActionLink && <div className="auth-switch"><Link to={`/forgot-password${location.search}`}>Forgot password?</Link></div>}
        <div className="auth-note"><ShieldCheck size={15} /> Account storage requires the Python API and PostgreSQL to be configured.</div>
      </div>
    </PageShell>
  );
}
