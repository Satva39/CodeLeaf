import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  ChevronRight,
  Copy,
  Crown,
  ExternalLink,
  Flame,
  Globe2,
  LockKeyhole,
  ShieldCheck,
  LogOut,
  Settings,
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
import DogAvatarEditor from "../components/avatar/DogAvatarEditor.jsx";
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
  const [profileReload, setProfileReload] = useState(0);
  const [emailVerified, setEmailVerified] = useState(false);
  const [publicProfileSettings, setPublicProfileSettings] = useState({
    is_public: false, show_xp: false, show_streak: false, show_certificates: false,
    show_achievements: false, show_progress: false,
  });
  const [publicProfileMode, setPublicProfileMode] = useState("idle");
  const [publicProfileBusy, setPublicProfileBusy] = useState(false);
  const [publicProfileFeedback, setPublicProfileFeedback] = useState("");
  const [publicProfileError, setPublicProfileError] = useState("");
  const [publicProfileReload, setPublicProfileReload] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const [editingProfile, setEditingProfile] = useState(() => new URLSearchParams(window.location.search).get("edit") === "1");
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
  useEffect(() => {
    let mounted = true;
    apiGetJson(`${API_BASE}/api/me`, { credentials: "include", ttlMs: 10_000, timeoutMs: 8_000 })
      .then((data) => {
        if (!mounted) return;
        if (!data?.user || typeof data.user !== "object") {
          setAccountMode("unavailable");
          setFeedback("The account service returned an incomplete profile response. Please retry.");
          return;
        }
        const user = data.user;
        setAccountEmail(user.email || "");
        setEmailVerified(user.email_verified === true);
        const next = {
          ...getProfile(),
          nickname: user.display_name || "Learner",
          handle: `@${user.username || "learner"}`,
          avatar: user.avatar && typeof user.avatar === "object" ? user.avatar : {},
          theme: user.theme || "dark",
        };
        setProfile(next);
        setName(next.nickname);
        setHandle(next.handle);
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
  }, [profileReload]);

  useEffect(() => {
    if (accountMode !== "remote") return undefined;
    let mounted = true;
    setPublicProfileMode("loading");
    setPublicProfileError("");
    apiGetJson(`${API_BASE}/api/me/public-profile`, { credentials: "include", ttlMs: 0, timeoutMs: 8_000 })
      .then((payload) => {
        if (!mounted) return;
        const settings = payload?.settings;
        if (!settings || typeof settings !== "object") throw new Error("Public-profile settings were not returned by the server.");
        setPublicProfileSettings({
          is_public: settings.is_public === true,
          show_xp: settings.show_xp === true,
          show_streak: settings.show_streak === true,
          show_certificates: settings.show_certificates === true,
          show_achievements: settings.show_achievements === true,
          show_progress: settings.show_progress === true,
        });
        setEmailVerified(payload.email_verified === true);
        setPublicProfileMode("ready");
      })
      .catch((error) => {
        if (!mounted) return;
        setPublicProfileMode("unavailable");
        setPublicProfileError(error?.message || "Public-profile settings could not be loaded.");
      });
    return () => { mounted = false; };
  }, [accountMode, publicProfileReload]);

  useEffect(() => {
    if (accountMode !== "remote") return undefined;
    let mounted = true;
    setPreferencesMode("loading");
    setPreferencesError("");
    apiGetJson(`${API_BASE}/api/me/learning-preferences`, { credentials: "include", ttlMs: 0, timeoutMs: 8_000 })
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

  const savePublicProfileSettings = async (patch) => {
    if (accountMode !== "remote" || publicProfileBusy) return;
    setPublicProfileBusy(true);
    setPublicProfileError("");
    setPublicProfileFeedback("");
    try {
      const response = await apiFetch(`${API_BASE}/api/me/public-profile`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(patch),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Public-profile settings could not be saved.");
      const settings = payload.settings || {};
      setPublicProfileSettings({
        is_public: settings.is_public === true,
        show_xp: settings.show_xp === true,
        show_streak: settings.show_streak === true,
        show_certificates: settings.show_certificates === true,
        show_achievements: settings.show_achievements === true,
        show_progress: settings.show_progress === true,
      });
      setEmailVerified(payload.email_verified === true);
      setPublicProfileMode("ready");
      setPublicProfileFeedback(settings.is_public ? "Your public profile is live." : "Your public profile is private.");
      invalidateApiCache("/api/me/public-profile");
    } catch (error) {
      setPublicProfileError(error?.message || "Public-profile settings could not be saved.");
    } finally {
      setPublicProfileBusy(false);
    }
  };

  const copyPublicProfileLink = async (url) => {
    if (!url) return;
    setPublicProfileError("");
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
      } else {
        const input = document.createElement("textarea");
        input.value = url;
        input.setAttribute("readonly", "true");
        input.style.position = "fixed";
        input.style.opacity = "0";
        document.body.appendChild(input);
        input.select();
        const copied = document.execCommand("copy");
        input.remove();
        if (!copied) throw new Error("Clipboard access is unavailable in this browser.");
      }
      setPublicProfileFeedback("Public profile link copied.");
    } catch (error) {
      setPublicProfileError(error?.message || "The link could not be copied. Select the URL and copy it manually.");
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

  const exportAccount = async () => {
    setSecurityBusy(true); setSecurityFeedback("");
    try {
      const response = await apiFetch(`${API_BASE}/api/me/export`);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Account export could not be prepared.");
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url; link.download = "codeleaf-account-export.json";
      document.body.appendChild(link); link.click(); link.remove(); window.URL.revokeObjectURL(url);
      setSecurityFeedback("Your account export has been downloaded.");
    } catch (error) { setSecurityFeedback(error.message || "Account export could not be prepared."); }
    finally { setSecurityBusy(false); }
  };

  const deleteAccount = async () => {
    const confirmed = window.confirm("Delete your CodeLeaf account? Learning progress and public identity will be removed. Payment/audit records may be retained in anonymized form where required.");
    if (!confirmed) return;
    const passwordValue = window.prompt("Enter your current password to confirm account deletion:");
    if (passwordValue === null) return;
    setSecurityBusy(true); setSecurityFeedback("");
    try {
      const response = await apiFetch(`${API_BASE}/api/me/delete`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: passwordValue }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Account deletion could not be completed.");
      window.dispatchEvent(new CustomEvent("codeleaf:auth-changed", { detail: { authenticated: false } }));
      navigate("/");
    } catch (error) { setSecurityFeedback(error.message || "Account deletion could not be completed."); }
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
    const next = { ...profile, nickname: cleanName, handle: `@${cleanHandle}` };
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
            avatar: profile.avatar && typeof profile.avatar === "object" ? profile.avatar : {},
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
          avatar: user.avatar && typeof user.avatar === "object" ? user.avatar : next.avatar,
          theme: user.theme || next.theme,
        };
        setProfile(confirmed);
        setName(confirmed.nickname);
        setHandle(confirmed.handle);
        invalidateApiCache("/api/me");
        setFeedback("Your profile details have been saved. Your dog avatar is saved separately as you customize it.");
      } else if (accountMode === "guest") {
        writeDemo({ profile: next });
        setProfile(next);
        setFeedback("Saved on this device. Sign in to sync profile details across devices.");
      } else {
        throw new Error("Account status is unavailable, so the profile was not saved. Retry when the account service is available.");
      }
      setSaved(true);
      setEditingProfile(false);
    } catch (error) {
      setSaveError(error?.message || "Profile could not be saved. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const cancelProfileEdit = () => {
    setName(profile.nickname || "Learner");
    setHandle(profile.handle || "@learner");
    setSaveError("");
    setEditingProfile(false);
  };

  const publicUsername = String(handle || "").replace(/^@/, "").trim().toLowerCase();
  const validPublicUsername = /^[a-z0-9_]{3,40}$/.test(publicUsername);
  const publicProfileUrl = accountMode === "remote" && validPublicUsername
    ? `${window.location.origin}/u/${encodeURIComponent(publicUsername)}`
    : "";
  const saveVisibilitySettings = () => savePublicProfileSettings({
    show_xp: publicProfileSettings.show_xp,
    show_streak: publicProfileSettings.show_streak,
    show_certificates: publicProfileSettings.show_certificates,
    show_achievements: publicProfileSettings.show_achievements,
    show_progress: publicProfileSettings.show_progress,
  });

  return (
    <PageShell>
      <div className="profile-layout">
        <div className="panel profile-main-card">
          <div className="profile-header">
            <div className="profile-avatar-wrap">
              <Avatar size="xl" />
            </div>
            <div className="profile-identity">
              <div className="profile-title-line">
                <h1>{profile.nickname || "Learner"}</h1>
                <span className="pill pill-cyan">PATHFINDER</span>
              </div>
              <p>{profile.handle || "@learner"} · Learning profile</p>
              {publicProfileUrl ? (
                <a className="profile-public-link" href={publicProfileUrl} target="_blank" rel="noreferrer">
                  <ExternalLink size={13} /> {publicProfileUrl}
                </a>
              ) : (
                <span className="profile-public-link">{accountMode === "remote" ? "Choose a valid username to create your profile link." : "Sign in to view your public profile link."}</span>
              )}
            </div>
            <button
              type="button"
              className="button button-secondary button-small"
              onClick={() => setEditingProfile(true)}
            >
              <Settings size={14} />
              Edit profile
            </button>
          </div>
          {accountMode === "guest" && <p className="profile-save-note" role="status">You are in guest mode. Profile details save only in this browser.</p>}
          {accountMode === "unavailable" && <p className="profile-save-note" role="status">
            Account status could not be verified. Your profile data has not been changed.
            <button type="button" className="text-link" onClick={() => { setAccountMode("loading"); setProfileReload((value) => value + 1); }}>
              Retry account loading
            </button>
          </p>}
          {feedback && <p className="profile-save-note" role="status">{feedback}</p>}
          {saveError && <p className="profile-save-error" role="alert">{saveError}</p>}
          <section className="profile-section profile-public-settings-card" aria-labelledby="public-profile-heading">
            <div className="profile-public-settings-heading">
              <span><Globe2 size={17} /></span>
              <div><div className="eyebrow">SHARE YOUR LEARNING JOURNEY</div><h2 id="public-profile-heading">Public profile</h2><p>Your profile link stays visible even while the page is private.</p></div>
              <span className={`profile-public-status ${publicProfileSettings.is_public ? "is-live" : "is-private"}`}>
                {publicProfileSettings.is_public ? <ShieldCheck size={13} /> : <LockKeyhole size={13} />}
                {publicProfileSettings.is_public ? "Live" : "Private"}
              </span>
            </div>
            {publicProfileUrl ? (
              <div className="profile-public-url-row">
                <input aria-label="Public profile URL" value={publicProfileUrl} readOnly onFocus={(event) => event.target.select()} />
                <button type="button" className="button button-secondary button-small" onClick={() => copyPublicProfileLink(publicProfileUrl)}><Copy size={13} /> Copy link</button>
                <a className="button button-secondary button-small" href={publicProfileUrl} target="_blank" rel="noreferrer"><ExternalLink size={13} /> Open</a>
              </div>
            ) : (
              <p className="profile-public-settings-note">{accountMode === "remote" ? "A public URL will be available after you set a username with 3–40 letters, numbers or underscores in Edit profile." : "Sign in to manage publication settings and view your account's public URL."}</p>
            )}
            {publicProfileMode === "loading" && <p className="profile-public-settings-note" role="status">Loading your publication settings…</p>}
            {publicProfileMode === "unavailable" && <p className="profile-public-settings-error" role="alert">{publicProfileError} <button type="button" className="text-link" onClick={() => setPublicProfileReload((value) => value + 1)}>Retry</button></p>}
            {publicProfileMode === "ready" && (
              <>
                <div className="profile-public-control-row">
                  <div><strong>{publicProfileSettings.is_public ? "Your public profile is live." : "Your public profile is currently private."}</strong><small>{publicProfileSettings.is_public ? "Anyone with your link can see only the sections you enable below." : "Only you can see your account profile. Publishing is optional."}</small></div>
                  <button type="button" className={`button ${publicProfileSettings.is_public ? "button-secondary" : "button-primary"} button-small`} disabled={publicProfileBusy || !validPublicUsername} onClick={() => savePublicProfileSettings({ is_public: !publicProfileSettings.is_public })}>
                    {publicProfileBusy ? "Saving…" : publicProfileSettings.is_public ? "Make profile private" : "Publish profile"}
                  </button>
                </div>
                {!emailVerified && !publicProfileSettings.is_public && <p className="profile-public-settings-note">Verify your email address before publishing. <Link to="/verify-email">Open email verification</Link>.</p>}
                <div className="profile-public-visibility">
                  <div className="eyebrow">SHOW ON YOUR PUBLIC PROFILE</div>
                  <div className="profile-public-visibility-grid">
                    {[
                      ["show_xp", "Total XP", "Display your earned XP."],
                      ["show_streak", "Current streak", "Display your active learning streak."],
                      ["show_certificates", "Certificates", "Show issued, non-revoked certificates."],
                      ["show_achievements", "Achievements", "Show unlocked CodeLeaf achievements."],
                      ["show_progress", "Learning progress", "Show course-level progress for published courses."],
                    ].map(([key, label, description]) => <label key={key}>
                      <input type="checkbox" checked={publicProfileSettings[key]} disabled={publicProfileBusy} onChange={(event) => setPublicProfileSettings((current) => ({ ...current, [key]: event.target.checked }))} />
                      <span><strong>{label}</strong><small>{description}</small></span>
                    </label>)}
                  </div>
                  <div className="profile-public-visibility-actions">
                    <button type="button" className="button button-secondary button-small" onClick={saveVisibilitySettings} disabled={publicProfileBusy || publicProfileMode !== "ready"}>Save visibility settings</button>
                    {publicProfileFeedback && <span role="status">{publicProfileFeedback}</span>}
                  </div>
                </div>
              </>
            )}
            {publicProfileError && publicProfileMode !== "unavailable" && <p className="profile-public-settings-error" role="alert">{publicProfileError}</p>}
          </section>
          {editingProfile && <div className="profile-edit-backdrop" role="presentation">
            <section className="profile-edit-dialog panel" role="dialog" aria-modal="true" aria-labelledby="profile-edit-title">
              <div className="profile-edit-dialog-header">
                <div><div className="eyebrow">YOUR CODELEAF IDENTITY</div><h2 id="profile-edit-title">Edit profile</h2><p>Update your public details and customize the dog that represents you across CodeLeaf.</p></div>
                <button type="button" className="icon-button" onClick={cancelProfileEdit} aria-label="Close profile editor">×</button>
              </div>
              <div className="profile-edit-details form-grid">
                <label>Display name<input value={name} onChange={(event) => { setName(event.target.value); setSaved(false); }} maxLength={50} /></label>
                <label>Public handle<input value={handle} onChange={(event) => { setHandle(event.target.value); setSaved(false); }} maxLength={30} /></label>
              </div>
              <div className="profile-edit-dog-heading"><div className="eyebrow">YOUR PROFILE PICTURE</div><h3>Customize your dog</h3><p>Choose its breed, fur and eye colors, then preview accessories you own. Save your changes to apply the new dog across CodeLeaf.</p></div>
              {accountMode === "remote" || accountMode === "loading" ? <DogAvatarEditor compact /> : <div className="phase3c-preferences-note" role="status">Sign in again or retry account verification to customize and save your profile dog across devices.</div>}
              {saveError && <p className="profile-save-error" role="alert">{saveError}</p>}
              <div className="profile-edit-dialog-actions">
                <button type="button" className="button button-secondary" onClick={cancelProfileEdit} disabled={saving}>Close</button>
                <button type="button" className="button button-primary" onClick={save} disabled={saving || accountMode === "loading"}>{saving ? "Saving profile…" : "Save profile details"}</button>
              </div>
            </section>
          </div>}
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
            <div className="form-grid profile-account-actions">
              <button type="button" className="button button-secondary" onClick={exportAccount} disabled={securityBusy}>Download my data</button>
              <button type="button" className="button button-secondary" onClick={deleteAccount} disabled={securityBusy}>Delete account</button>
            </div>
            {securityFeedback && <p className="profile-save-note" role="status">{securityFeedback}</p>}
            {securityTestUrl && <p className="profile-save-note" role="status">Local test mode only; no email was sent. <a href={securityTestUrl}>Open confirmation link</a>.</p>}
          </div>}
        </div>
        <div className="profile-side-stack">
          <div className="panel profile-summary-card">
            <Avatar size="lg" />
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
