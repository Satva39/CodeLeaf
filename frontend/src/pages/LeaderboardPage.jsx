import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  Clock3,
  Flame,
  ShieldCheck,
  Star,
  Trophy,
  Zap,
  Users,
} from "lucide-react";
import { API_BASE, formatNumber } from "../lib/demoState.js";
import {
  PageShell,
  SectionHeading,
  LockIcon,
  EmptyState,
} from "../components/common.jsx";
import { Avatar } from "../components/layout/Header.jsx";

export default function LeaderboardPage() {
  const [period, setPeriod] = useState("week");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [planLocked, setPlanLocked] = useState(false);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    setPlanLocked(false);
    apiFetch(`${API_BASE}/api/leaderboard?period=${period}&limit=50`)
      .then(async (response) => {
        if (response.status === 403) {
          if (active) setPlanLocked(true);
          return { items: [] };
        }
        if (!response.ok)
          throw new Error(response.status === 401 ? "Sign in and choose Pro or above to view the leaderboard." : "The leaderboard could not be loaded.");
        return response.json();
      })
      .then((data) => {
        if (active) setRows(data.items || []);
      })
      .catch((err) => {
        if (active)
          setError(err.message || "The leaderboard could not be loaded.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [period]);

  return (
    <PageShell>
      <SectionHeading
        eyebrow="LEARN TOGETHER"
        title={period === "week" ? "Weekly league" : "All-time leaderboard"}
        detail="Rankings come from XP events recorded by the CodeLeaf backend."
        action={
          <button
            className="button button-secondary"
            onClick={() =>
              setPeriod((current) => (current === "week" ? "all_time" : "week"))
            }
          >
            {period === "week" ? "View all time" : "View this week"}
          </button>
        }
      />
      <div className="league-hero panel">
        <div className="league-emblems">
          <span className="emblem emblem-gold">
            <Trophy size={24} />
          </span>
          <span className="emblem emblem-silver">
            <Star size={22} />
          </span>
          <span className="emblem emblem-cyan">
            <Zap size={28} />
          </span>
          <span className="emblem emblem-muted">
            <LockIcon />
          </span>
          <span className="emblem emblem-muted">
            <LockIcon />
          </span>
        </div>
        <h2>{period === "week" ? "Grow your skills" : "Hall of progress"}</h2>
        <p>
          {period === "week"
            ? "Weekly XP totals are calculated from activity in the last seven days."
            : "All-time XP reflects verified learning activity recorded by CodeLeaf."}
        </p>
        <span className="league-time">
          <Clock3 size={14} />{" "}
          {period === "week" ? "Rolling 7-day window" : "All recorded activity"}
        </span>
      </div>
      <div className="leaderboard-card panel">
        <div className="leaderboard-tabs">
          <button
            className={period === "week" ? "active" : ""}
            onClick={() => setPeriod("week")}
          >
            Weekly League
          </button>
          <button
            className={period === "all_time" ? "active" : ""}
            onClick={() => setPeriod("all_time")}
          >
            All-time
          </button>
          <span className="leaderboard-current">
            <Flame size={15} /> {rows.length} learner
            {rows.length === 1 ? "" : "s"}
          </span>
        </div>
        <div className="xp-booster">
          <span className="booster-icon">
            <Zap size={17} />
          </span>
          <div>
            <strong>Earn XP through learning</strong>
            <small>
              Each completed lesson and correctly completed exercise earns base
              XP once.
            </small>
          </div>
          <Link
            to="/challenges"
            className="button button-small button-secondary"
          >
            Practise now <ArrowRight size={13} />
          </Link>
        </div>
        {loading ? (
          <div className="empty-state">
            <p>Loading rankings…</p>
          </div>
        ) : planLocked ? (
          <div className="empty-state">
            <h3>Leaderboards are included with Pro and above</h3>
            <p>Free learners can keep earning XP through standard lessons and exercises. Upgrade to join the weekly and all-time learning leagues.</p>
            <Link className="button button-primary" to="/plans">Compare plans <ArrowRight size={14} /></Link>
          </div>
        ) : error ? (
          <div className="empty-state">
            <p>{error}</p>
            {error.startsWith("Sign in") && <Link className="button button-primary" to={`/login?next=${encodeURIComponent("/leaderboard")}`}>Sign in</Link>}
          </div>
        ) : rows.length ? (
          rows.map((row) => (
            <div key={row.username} className="leader-row">
              <span className="leader-rank">{row.rank}</span>
              <Avatar size="sm" variant={row.avatar?.variant || "spark"} />
              <div className="leader-user">
                <strong>{row.display_name || row.username}</strong>
                <small>@{row.username}</small>
              </div>
              <strong className="leader-xp">{formatNumber(row.xp)} XP</strong>
            </div>
          ))
        ) : (
          <EmptyState
            icon={Users}
            title="The leaderboard is waiting for learners"
            detail="Once accounts complete published lessons or verified exercises, their earned XP will appear here."
            action={
              <Link to="/tutorials" className="button button-primary">
                Start learning <ArrowRight size={15} />
              </Link>
            }
          />
        )}
        <div className="leaderboard-footnote">
          <ShieldCheck size={14} /> Only XP recorded by the backend affects live
          rankings. Avoid sharing private account information in public profile
          fields.
        </div>
      </div>
    </PageShell>
  );
}
