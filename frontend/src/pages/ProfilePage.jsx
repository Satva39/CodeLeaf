import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  Check,
  ChevronRight,
  Code2,
  Compass,
  Crown,
  ExternalLink,
  Flame,
  LogOut,
  Settings,
  Sparkles,
  UserRound,
  Zap,
} from "lucide-react";

import {
  API_BASE,
  writeDemo,
  getProfile,
  formatNumber,
} from "../lib/demoState.js";
import { useGamificationStats } from "../lib/useGamificationStats.js";
import { PageShell } from "../components/common.jsx";
import { Avatar } from "../components/layout/Header.jsx";
import { apiGetJson, invalidateApiCache } from "../lib/apiCache.js";
import "../styles/phase3c-personal-learning.css";

export default function ProfilePage() {
  const stats = useGamificationStats();
  const navigate = useNavigate();
  const [accountEmail, setAccountEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [currentEmailPassword, setCurrentEmailPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [securityFeedback, setSecurityFeedback] = useState("");
  const [securityTestUrl, setSecurityTestUrl] = useState("");
  const [securityBusy, setSecurityBusy] = useState(false);
  const [logoutBusy, setLogoutBusy] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const [profile, setProfile] = useState(getProfile());
  const [name, setName] = useState(profile.nickname);
  const [handle, setHandle] = useState(profile.handle);
  const [saved, setSaved] = useState(false);
  const [accountMode, setAccountMode] = useState("loading");
  const [feedback, setFeedback] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const [avatarPick, setAvatarPick] = useState(profile.avatar || "spark");
  const browserTimeZone = (() => {
    try { return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"; } catch { return "UTC"; }
  })();
  const [learningPreferences, setLearningPreferences] = useState({
    timezone_name: browserTimeZone,
    review_frequency_days: 1,
    daily_review_limit: 10,
    analytics_enabled: false,
  });
  const [preferencesMode, setPreferencesMode] = useState("idle");
  const [preferencesSaving, setPreferencesSaving] = useState(false);
  const [preferencesMessage, setPreferencesMessage] = useState("");
  const [preferencesError, setPreferencesError] = useState("");
  const [preferencesReload, setPreferencesReload] = useState(0);
  const avatars = [
    { id: "spark", label: "Spark", Icon: Sparkles },
    { id: "orbit", label: "Orbit", Icon: Compass },
    { id: "code", label: "Code", Icon: Code2 },
    { id: "user", label: "Classic", Icon: UserRound },
  ];
  useEffect(() => {
    let mounted = true;
    apiGetJson(`${API_BASE}/api/me`, { credentials: "include", ttlMs: 10_000 })
      .then((data) => {
        if (!mounted || !data.user) return;
        const user = data.user;
        setAccountEmail(user.email || "");
        const avatar = user.avatar?.variant || "spark";
        const next = {
          ...getProfile(),
          nickname: user.display_name || "Learner",
          handle: `@${user.username || "learner"}`,
          avatar,
          theme: user.theme || "dark",
        };
        setProfile(next);
        setName(next.nickname);
        setHandle(next.handle);
        setAvatarPick(avatar);
        setAccountMode("remote");
      })
      .catch((error) => {
        if (!mounted) return;
        if (error?.status === 401) {
          setAccountMode("guest");
          return;
        }
        setAccountMode("unavailable");
        setFeedback("Account details could not be checked. Your account profile was not changed.");
      });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (accountMode !== "remote") return undefined;
    let mounted = true;
    setPreferencesMode("loading");
    setPreferencesError("");
    apiGetJson(`${API_BASE}/api/me/learning-preferences`, { credentials: "include", ttlMs: 0 })
      .then((payload) => {
        if (!mounted) return;
        const value = payload?.preferences;
        if (!value || typeof value !== "object") throw new Error("Learning preferences were not returned by the server.");
        setLearningPreferences({
          timezone_name: String(value.timezone_name || browserTimeZone),
          review_frequency_days: Math.min(30, Math.max(1, Number(value.review_frequency_days) || 1)),
          daily_review_limit: Math.min(50, Math.max(1, Number(value.daily_review_limit) || 10)),
          analytics_enabled: value.analytics_enabled === true,
        });
        setPreferencesMode("ready");
      })
      .catch((error) => {
        if (!mounted) return;
        setPreferencesMode("unavailable");
        setPreferencesError(error?.status === 401
          ? "Sign in again to manage account-wide learning preferences."
          : "Learning preferences could not be loaded. Your existing settings were not changed.");
      });
    return () => { mounted = false; };
  }, [accountMode, browserTimeZone, preferencesReload]);

  const saveLearningPreferences = async (event) => {
    event.preventDefault();
    if (accountMode !== "remote" || preferencesSaving) return;
    setPreferencesSaving(true);
    setPreferencesMessage("");
    setPreferencesError("");
    try {
      const response = await apiFetch(`${API_BASE}/api/me/learning-preferences`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          timezone_name: learningPreferences.timezone_name.trim(),
          review_frequency_days: Number(learningPreferences.review_frequency_days),
          daily_review_limit: Number(learningPreferences.daily_review_limit),
          analytics_enabled: learningPreferences.analytics_enabled === true,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Learning preferences could not be saved.");
      const value = payload.preferences;
      if (value) setLearningPreferences({
        timezone_name: String(value.timezone_name || browserTimeZone),
        review_frequency_days: Number(value.review_frequency_days) || 1,
        daily_review_limit: Number(value.daily_review_limit) || 10,
        analytics_enabled: value.analytics_enabled === true,
      });
      invalidateApiCache("/api/me/learning-preferences");
      invalidateApiCache("/api/me/reviews");
      setPreferencesMode("ready");
      setPreferencesMessage("Your learning preferences are saved to your account.");
    } catch (error) {
      setPreferencesError(error?.message || "Learning preferences could not be saved. Please try again.");
    } finally {
      setPreferencesSaving(false);
    }
  };

  const changeEmail = async (event) => {
    event.preventDefault();
    setSecurityBusy(true); setSecurityFeedback(""); setSecurityTestUrl("");
    try {
      const response = await apiFetch(`${API_BASE}/api/auth/change-email`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentEmailPassword, new_email: newEmail }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "The email change could not be requested.");
      setSecurityFeedback(payload.message || "If this address can be used, a verification link will be sent.");
      setSecurityTestUrl(payload.test_url || "");
      setCurrentEmailPassword(""); setNewEmail("");
    } catch (error) { setSecurityFeedback(error.message || "The email change could not be requested."); }
    finally { setSecurityBusy(false); }
  };

  const changePassword = async (event) => {
    event.preventDefault();
    setSecurityBusy(true); setSecurityFeedback("");
    try {
      const response = await apiFetch(`${API_BASE}/api/auth/change-password`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "The password could not be changed.");
      setCurrentPassword(""); setNewPassword("");
      window.dispatchEvent(new CustomEvent("codeleaf:auth-changed", { detail: { authenticated: false } }));
      navigate("/login");
    } catch (error) { setSecurityFeedback(error.message || "The password could not be changed."); }
    finally { setSecurityBusy(false); }
  };

  const handleLogout = async () => {
    if (logoutBusy || accountMode !== "remote") return;
    setLogoutBusy(true);
    setLogoutError("");
    try {
      const response = await apiFetch(`${API_BASE}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || payload?.ok === false) {
        throw new Error(payload?.detail || "Logout could not be completed. Please try again.");
      }

      // Clear cached user-scoped API responses and ask the shared header to
      // re-check the now-revoked server session before rendering signed-out UI.
      invalidateApiCache();
      window.dispatchEvent(new CustomEvent("codeleaf:auth-changed", {
        detail: { authenticated: false },
      }));
      navigate("/login", { replace: true });
    } catch (error) {
      // Stay on the account page if the server did not confirm the logout.
      setLogoutError(error?.message || "Logout could not be completed. Please try again.");
    } finally {
      setLogoutBusy(false);
    }
  };

  const save = async () => {
    if (saving) return;
    const cleanName = name.trim() || "Learner";
    const cleanHandle = (handle.startsWith("@") ? handle.slice(1) : handle).trim();
    const next = { ...profile, nickname: cleanName, handle: `@${cleanHandle}`, avatar: avatarPick };
    setSaving(true);
    setSaveError("");
    setFeedback("");
    setSaved(false);
    try {
      if (accountMode === "remote") {
        const response = await apiFetch(`${API_BASE}/api/me/profile`, {
          method: "PATCH",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            display_name: cleanName,
            username: cleanHandle,
            avatar: { variant: avatarPick },
            theme: profile.theme === "light" ? "light" : "dark",
          }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "Your account profile could not be saved.");
        const user = payload.user || {};
        const confirmed = {
          ...next,
          nickname: user.display_name || cleanName,
          handle: `@${user.username || cleanHandle}`,
          avatar: user.avatar?.variant || avatarPick,
          theme: user.theme || next.theme,
        };
        setProfile(confirmed);
        setName(confirmed.nickname);
        setHandle(confirmed.handle);
        setAvatarPick(confirmed.avatar);
        invalidateApiCache("/api/me");
        setFeedback("Profile changes synced to your account.");
      } else if (accountMode === "guest") {
        writeDemo({ profile: next });
        setProfile(next);
        setFeedback("Saved on this device. Sign in to sync profile details across devices.");
      } else {
        throw new Error("Account status is unavailable, so the profile was not saved. Retry when the account service is available.");
      }
      setSaved(true);
    } catch (error) {
      setSaveError(error?.message || "Profile could not be saved. Please try again.");
    } finally {
      setSaving(false);
    }
  };
  return (
    <PageShell>
      <div className="profile-layout">
        <div className="panel profile-main-card">
          <div className="profile-header">
            <div className="profile-avatar-wrap">
              <Avatar size="xl" variant={avatarPick} />
            </div>
            <div className="profile-identity">
              <div className="profile-title-line">
                <h1>{profile.nickname || "Learner"}</h1>
                <span className="pill pill-cyan">PATHFINDER</span>
              </div>
              <p>{profile.handle || "@learner"} · Learning profile</p>
              <span className="profile-public-link">
                <ExternalLink size={13} /> Public profile link will appear here
                when enabled
              </span>
            </div>
            <button
              type="button"
              className="button button-secondary button-small"
              onClick={save}
              disabled={saving || accountMode === "loading"}
            >
              {saved ? <Check size={14} /> : <Settings size={14} />}
              {saving ? "Saving…" : saved ? "Saved" : "Save changes"}
            </button>
          </div>
          {accountMode === "guest" && <p className="profile-save-note" role="status">You are in guest mode. Profile details save only in this browser.</p>}
          {accountMode === "unavailable" && <p className="profile-save-note" role="status">Account status could not be verified.</p>}
          {feedback && <p className="profile-save-note" role="status">{feedback}</p>}
          {saveError && <p className="profile-save-error" role="alert">{saveError}</p>}
          <div className="profile-section">
            <div className="eyebrow">PERSONAL DETAILS</div>
            <h2>Make this profile yours</h2>
            <div className="form-grid">
              <label>
                Display name
                <input
                  value={name}
                  onChange={(e) => { setName(e.target.value); setSaved(false); }}
                  maxLength={50}
                />
              </label>
              <label>
                Public handle
                <input
                  value={handle}
                  onChange={(e) => { setHandle(e.target.value); setSaved(false); }}
                  maxLength={30}
                />
              </label>
            </div>
          </div>
          <div className="profile-section avatar-customizer">
            <div className="eyebrow">AVATAR STUDIO</div>
            <h2>Choose your learning identity</h2>
            <p>
              Select a simple base style. More outfits, colors and accessories
              can become unlockable items later.
            </p>
            <div className="avatar-options">
              {avatars.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  className={avatarPick === id ? "selected" : ""}
                  onClick={() => { setAvatarPick(id); setSaved(false); }}
                >
                  <span className={`avatar avatar-lg avatar-${id}`}>
                    <Icon size={21} />
                  </span>
                  <strong>{label}</strong>
                  {avatarPick === id && (
                    <span className="avatar-selected-check">
                      <Check size={12} />
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
          <div className="profile-section phase3c-preferences-section">
            <div className="eyebrow">LEARNING PREFERENCES</div>
            <h2>Set a pace that works for you</h2>
            <p>Choose a comfortable revision rhythm and how many reviews to show per day. These settings guide the review queue; they do not claim mastery or award XP.</p>
            {accountMode === "guest" ? (
              <div className="phase3c-preferences-note" role="status">Sign in to save learning preferences across devices. Guest settings have not been sent to the server.</div>
            ) : accountMode !== "remote" ? (
              <div className="phase3c-preferences-note" role="status">{preferencesMode === "loading" ? "Loading your learning preferences…" : "Learning preferences are available after your account status is confirmed."}</div>
            ) : preferencesMode === "loading" || preferencesMode === "idle" ? (
              <div className="phase3c-preferences-note" role="status">Loading account preferences…</div>
            ) : preferencesMode === "unavailable" ? (
              <div className="phase3c-preferences-note" role="status">{preferencesError || "Preferences are temporarily unavailable."} <button type="button" className="text-link phase3c-inline-retry" onClick={() => setPreferencesReload((value) => value + 1)} >Retry preferences</button></div>
            ) : (
              <form className="phase3c-preferences-form" onSubmit={saveLearningPreferences}>
                <label>
                  Revision interval
                  <select value={learningPreferences.review_frequency_days} onChange={(event) => setLearningPreferences((current) => ({ ...current, review_frequency_days: Number(event.target.value) }))}>
                    <option value={1}>Daily</option>
                    <option value={2}>Every 2 days</option>
                    <option value={3}>Every 3 days</option>
                    <option value={7}>Weekly</option>
                    <option value={14}>Every 2 weeks</option>
                    <option value={30}>Monthly</option>
                  </select>
                </label>
                <label>
                  Daily review limit
                  <select value={learningPreferences.daily_review_limit} onChange={(event) => setLearningPreferences((current) => ({ ...current, daily_review_limit: Number(event.target.value) }))}>
                    {[5, 10, 15, 20, 30, 50].map((value) => <option key={value} value={value}>{value} reviews per day</option>)}
                  </select>
                </label>
                <label className="phase3c-timezone-field">
                  Time zone (IANA name)
                  <input value={learningPreferences.timezone_name} onChange={(event) => setLearningPreferences((current) => ({ ...current, timezone_name: event.target.value }))} maxLength={80} required placeholder="Asia/Kolkata" aria-describedby="phase3c-timezone-help" />
                  <small id="phase3c-timezone-help">Used to interpret your learning-day preferences. Example: Asia/Kolkata.</small>
                </label>
                <label className="phase3c-analytics-toggle">
                  <input type="checkbox" checked={learningPreferences.analytics_enabled} onChange={(event) => setLearningPreferences((current) => ({ ...current, analytics_enabled: event.target.checked }))} />
                  <span><strong>Share optional product analytics</strong><small>Allow limited usage events to help improve CodeLeaf. This does not share your passwords or code submissions.</small></span>
                </label>
                {preferencesError && <p className="phase3c-preferences-error" role="alert">{preferencesError}</p>}
                {preferencesMessage && <p className="phase3c-preferences-success" role="status">{preferencesMessage}</p>}
                <div className="phase3c-preferences-actions"><button type="submit" className="button button-primary" disabled={preferencesSaving}>{preferencesSaving ? "Saving…" : "Save learning preferences"}</button></div>
              </form>
            )}
          </div>
          {accountMode === "remote" && <div className="profile-section">
            <div className="eyebrow">ACCOUNT SECURITY</div>
            <h2>Protect your account</h2>
            <p>Signed in as <strong>{accountEmail || "your account"}</strong>. Email changes take effect only after confirming the one-time link.</p>
            <form className="auth-form" onSubmit={changeEmail}>
              <label>New email address<input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} required maxLength={320} autoComplete="email" /></label>
              <label>Current password<input type="password" value={currentEmailPassword} onChange={(e) => setCurrentEmailPassword(e.target.value)} required maxLength={128} autoComplete="current-password" /></label>
              <button type="submit" className="button button-secondary" disabled={securityBusy}>Request email change</button>
            </form>
            <form className="auth-form" onSubmit={changePassword}>
              <label>Current password<input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required maxLength={128} autoComplete="current-password" /></label>
              <label>New password<input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={10} maxLength={128} autoComplete="new-password" /><small>Use at least 10 characters. Changing it signs out your other sessions.</small></label>
              <button type="submit" className="button button-secondary" disabled={securityBusy}>Change password</button>
            </form>
            {securityFeedback && <p className="profile-save-note" role="status">{securityFeedback}</p>}
            {securityTestUrl && <p className="profile-save-note" role="status">Local test mode only; no email was sent. <a href={securityTestUrl}>Open confirmation link</a>.</p>}
          </div>}
        </div>
        <div className="profile-side-stack">
          <div className="panel profile-summary-card">
            <Avatar size="lg" variant={avatarPick} />
            <h3>{name || "Learner"}</h3>
            <p>{handle || "@learner"}</p>
            <div className="profile-summary-stats">
              <span>
                <Zap size={15} /> {formatNumber(stats.totalXp)} XP
              </span>
              <span>
                <Flame size={15} /> {stats.currentStreak} day streak
              </span>
            </div>
            <Link to="/progress" className="text-link">
              View progress <ArrowRight size={14} />
            </Link>
          </div>
          <div className="panel account-info-card">
            <h3>Account settings</h3>
            <Link to="/plans">
              <span>
                <Crown size={16} /> Plan and billing
              </span>
              <ChevronRight size={15} />
            </Link>
            <Link to="/progress">
              <span>
                <Activity size={16} /> Learning history
              </span>
              <ChevronRight size={15} />
            </Link>
            {accountMode === "remote" && (
              <button
                type="button"
                className="account-logout-button"
                onClick={handleLogout}
                disabled={logoutBusy}
                aria-label="Log out of CodeLeaf"
                aria-busy={logoutBusy}
              >
                <span><LogOut size={16} /> {logoutBusy ? "Logging out…" : "Log out"}</span>
              </button>
            )}
            {logoutError && <p className="account-logout-feedback" role="alert">{logoutError}</p>}
          </div>
        </div>
      </div>
    </PageShell>
  );
}
