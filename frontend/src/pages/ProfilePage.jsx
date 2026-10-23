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
  Settings,
  ShieldCheck,
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
  const [profile, setProfile] = useState(getProfile());
  const [name, setName] = useState(profile.nickname);
  const [handle, setHandle] = useState(profile.handle);
  const [saved, setSaved] = useState(false);
  const [accountMode, setAccountMode] = useState("loading");
  const [feedback, setFeedback] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saving, setSaving] = useState(false);
  const [avatarPick, setAvatarPick] = useState(profile.avatar || "spark");
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
          <div className="profile-section profile-toggles">
            <div className="eyebrow">PRIVACY & VISIBILITY</div>
            <h2>Privacy preferences</h2>
            <p>Manage optional product analytics consent and your learning-review preferences. These settings are saved to your account and apply when you are signed in.</p>
            <Link to="/learning-hub#privacy-preferences" className="button button-secondary profile-privacy-link">
              Manage privacy settings <ArrowRight size={14} />
            </Link>
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
            <Link to="/learning-hub#privacy-preferences" aria-label="Manage privacy and learning preferences">
              <span><ShieldCheck size={16} /> Privacy & learning preferences</span>
              <ChevronRight size={15} />
            </Link>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
