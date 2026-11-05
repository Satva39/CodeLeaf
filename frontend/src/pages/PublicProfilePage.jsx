import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Award, BookOpen, Flame, GraduationCap, ShieldCheck, Sparkles, Zap } from "lucide-react";
import { PageShell } from "../components/common.jsx";
import DogAvatar from "../components/avatar/DogAvatar.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE, formatNumber } from "../lib/demoState.js";
import "../styles/public-profile.css";

export default function PublicProfilePage() {
  const { username = "" } = useParams();
  const [profile, setProfile] = useState(null);
  const [mode, setMode] = useState("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    let mounted = true;
    setMode("loading");
    setProfile(null);
    setError("");

    apiFetch(`${API_BASE}/api/public-profiles/${encodeURIComponent(username)}`, {
      method: "GET",
      credentials: "omit",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    }).then(async (response) => {
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const err = new Error(typeof payload.detail === "string" ? payload.detail : "This public profile is unavailable or private.");
        err.status = response.status;
        throw err;
      }
      if (!mounted) return;
      setProfile(payload);
      setMode("ready");
    }).catch((err) => {
      if (!mounted || controller.signal.aborted) return;
      setError(err.status === 404
        ? "This profile is private or does not exist. Ask the owner to publish it before opening this link."
        : err.message || "The public profile could not be loaded.");
      setMode("unavailable");
    });

    return () => {
      mounted = false;
      controller.abort();
    };
  }, [username]);

  if (mode === "loading") {
    return <PageShell><div className="public-profile-state" role="status">Loading public profile…</div></PageShell>;
  }
  if (mode === "unavailable" || !profile) {
    return <PageShell>
      <div className="public-profile-state public-profile-unavailable">
        <span><ShieldCheck size={22} /></span>
        <h1>Profile unavailable</h1>
        <p>{error || "This public profile is private or does not exist."}</p>
        <Link to="/" className="button button-primary">Go to CodeLeaf</Link>
      </div>
    </PageShell>;
  }

  const dog = profile.dog_avatar || {};
  const stats = profile.stats || {};
  const visibility = profile.visibility || {};
  const hasStats = Object.keys(stats).length > 0;

  return (
    <PageShell>
      <main className="public-profile-page">
        <section className="public-profile-hero panel">
          <div className="public-profile-hero-glow" aria-hidden="true" />
          <div className="public-profile-dog-wrap">
            <DogAvatar
              appearance={dog.appearance || { breed: "classic", fur_color: "golden", eye_color: "brown" }}
              equipment={dog.equipment || {}}
              size={260}
              title={`${profile.display_name || profile.username}'s CodeLeaf dog avatar`}
            />
          </div>
          <div className="public-profile-identity">
            <span className="eyebrow"><ShieldCheck size={13} /> CODELEAF PUBLIC PROFILE</span>
            <h1>{profile.display_name || "CodeLeaf learner"}</h1>
            <p>@{profile.username}</p>
            <span className="public-profile-tagline">Learning, building and growing with CodeLeaf.</span>
          </div>
          <div className="public-profile-brand-mark"><Sparkles size={16} /> CodeLeaf</div>
          {hasStats && <div className="public-profile-stats">
            {visibility.xp && typeof stats.total_xp !== "undefined" && <div><span><Zap size={15} /></span><strong>{formatNumber(stats.total_xp)}</strong><small>XP earned</small></div>}
            {visibility.streak && typeof stats.current_streak !== "undefined" && <div><span><Flame size={15} /></span><strong>{formatNumber(stats.current_streak)}</strong><small>Day streak</small></div>}
          </div>}
        </section>

        {visibility.progress && profile.progress?.length > 0 && <section className="public-profile-section panel">
          <div className="public-profile-section-heading"><span><BookOpen size={17} /></span><div><h2>Learning progress</h2><p>Progress across published CodeLeaf courses.</p></div></div>
          <div className="public-profile-progress-list">
            {profile.progress.map((course) => <article key={course.course_slug}>
              <div><strong>{course.course_title}</strong><small>{course.completed_lessons} of {course.total_lessons} lessons</small></div>
              <span className="public-profile-progress-track"><i style={{ width: `${Math.max(0, Math.min(100, Number(course.percent) || 0))}%` }} /></span>
              <b>{course.percent}%</b>
            </article>)}
          </div>
        </section>}

        <div className="public-profile-lower-grid">
          {visibility.certificates && <section className="public-profile-section panel">
            <div className="public-profile-section-heading"><span><GraduationCap size={17} /></span><div><h2>Certificates</h2><p>Certificates shared by this learner.</p></div></div>
            {profile.certificates?.length ? <div className="public-profile-certificate-list">
              {profile.certificates.map((certificate) => <Link to={certificate.path} key={certificate.public_id}>
                <span><Award size={16} /></span><div><strong>{certificate.course_title}</strong><small>{certificate.issued_at ? new Date(certificate.issued_at).toLocaleDateString() : "Issued certificate"}</small></div>
              </Link>)}
            </div> : <p className="public-profile-empty-note">No certificates have been shared yet.</p>}
          </section>}

          {visibility.achievements && <section className="public-profile-section panel">
            <div className="public-profile-section-heading"><span><Award size={17} /></span><div><h2>Achievements</h2><p>Milestones earned on CodeLeaf.</p></div></div>
            {profile.achievements?.length ? <div className="public-profile-achievements">
              {profile.achievements.map((achievement) => <article key={achievement.id}>
                <span><Award size={15} /></span><div><strong>{achievement.name}</strong><p>{achievement.description}</p></div>
              </article>)}
            </div> : <p className="public-profile-empty-note">No achievements have been shared yet.</p>}
          </section>}
        </div>
        <footer className="public-profile-footer"><span>Powered by CodeLeaf</span><Link to="/register">Start learning <Sparkles size={13} /></Link></footer>
      </main>
    </PageShell>
  );
}
