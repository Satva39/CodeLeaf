import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Clock3, Code2, Crown, Play, RotateCcw, ShieldCheck, Swords, TerminalSquare, Trophy, UserRound, XCircle } from "lucide-react";
import { PageShell } from "../components/common.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import DogAvatar from "../components/avatar/DogAvatar.jsx";
import AchievementRewardNotice from "../components/avatar/AchievementRewardNotice.jsx";
import "../styles/games.css";

async function readPayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : payload.message || `Request failed (${response.status})`);
  return payload;
}
function makeKey() { return globalThis.crypto?.randomUUID?.() || `battle-${Date.now()}-${Math.random().toString(36).slice(2)}`; }
function starterFor(language) {
  return language === "python"
    ? "import sys\n\ndata = sys.stdin.read().split()\n# TODO: Read the input and print the required output.\n"
    : "const fs = require('fs');\nconst input = fs.readFileSync(0, 'utf8').trim();\nconst data = input.split(/\\s+/).filter(Boolean);\n// TODO: Read the input and print the required output.\n";
}
function secondsLeft(expiresAt, now) {
  if (!expiresAt) return null;
  return Math.max(0, Math.ceil((new Date(expiresAt).getTime() - now) / 1000));
}
function formatTime(value) {
  if (value === null) return "--:--";
  return `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
}

export default function BattlesPage() {
  const [language, setLanguage] = useState("python");
  const [difficulty, setDifficulty] = useState("easy");
  const [battle, setBattle] = useState(null);
  const [source, setSource] = useState(starterFor("python"));
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [sampleResult, setSampleResult] = useState(null);
  const [achievementRewards, setAchievementRewards] = useState([]);
  const [achievementXpEarned, setAchievementXpEarned] = useState(0);
  const [clock, setClock] = useState(Date.now());
  const [supportedLanguages, setSupportedLanguages] = useState([]);

  async function refreshBattle(id) {
    const data = await readPayload(await apiFetch(`${API_BASE}/api/battles/${encodeURIComponent(id)}`, { credentials: "include" }));
    setBattle(data.battle);
    if (data.battle?.challenge?.id && !source.trim()) setSource(starterFor(data.battle.language));
    return data.battle;
  }

  useEffect(() => {
    let active = true;
    apiFetch(`${API_BASE}/api/me/battles/current`, { credentials: "include" })
      .then((response) => readPayload(response))
      .then((data) => { if (active && data.battle) { setBattle(data.battle); setLanguage(data.battle.language); setDifficulty(data.battle.difficulty); setSource(starterFor(data.battle.language)); } })
      .catch(() => {});
    apiFetch(`${API_BASE}/api/runner/status`, { credentials: "include" }).then((response) => readPayload(response)).then((data) => {
      if (active) {
        const runnerLanguages = (data.supported_languages || []).filter((name) => {
          const key = String(name).toLowerCase();
          return ["python", "javascript"].includes(key)
            && ["onlinecompiler", "codeleaf-runner"].includes(data.providers_by_language?.[key]);
        });
        setSupportedLanguages(runnerLanguages);
      }
    }).catch(() => { if (active) setSupportedLanguages([]); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!battle?.id || !["waiting", "active"].includes(battle.status)) return undefined;
    let active = true;
    const timer = window.setInterval(async () => {
      try { const next = await refreshBattle(battle.id); if (!active || !["waiting", "active"].includes(next.status)) window.clearInterval(timer); }
      catch (err) { if (active) setError(err.message || "Battle status could not be refreshed."); }
    }, 2500);
    return () => { active = false; window.clearInterval(timer); };
  }, [battle?.id, battle?.status]);

  const remaining = useMemo(() => secondsLeft(battle?.expires_at, clock), [battle?.expires_at, clock]);

  async function findOpponent() {
    if (loading) return;
    setLoading(true); setError(""); setNotice(""); setBattle(null); setSampleResult(null); setAchievementRewards([]); setAchievementXpEarned(0); setSource(starterFor(language));
    try {
      const data = await readPayload(await apiFetch(`${API_BASE}/api/battles/matchmake`, {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ language, difficulty }),
      }));
      setBattle(data.battle);
      setNotice(data.message || "Battle matchmaking started.");
    } catch (err) { setError(err.message || "Could not start matchmaking."); }
    finally { setLoading(false); }
  }

  async function runSample() {
    if (!battle?.id || submitting) return;
    setSubmitting(true); setError(""); setSampleResult(null);
    try {
      const data = await readPayload(await apiFetch(`${API_BASE}/api/battles/${battle.id}/run`, {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_code: source, request_key: makeKey() }),
      }));
      setSampleResult(data);
    } catch (err) { setError(err.message || "The sample could not run."); }
    finally { setSubmitting(false); }
  }

  async function submitSolution() {
    if (!battle?.id || submitting) return;
    setSubmitting(true); setError(""); setSampleResult(null);
    try {
      const data = await readPayload(await apiFetch(`${API_BASE}/api/battles/${battle.id}/submit`, {
        method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_code: source, request_key: makeKey() }),
      }));
      setBattle(data.battle || battle);
      const result = data.submission?.result || {};
      const rewards = Array.isArray(result.new_rewards) ? result.new_rewards : [];
      setAchievementRewards(rewards);
      setAchievementXpEarned(Number(result.xp_awarded || 0) + rewards.reduce((sum, reward) => sum + Number(reward.xp_awarded || 0), 0));
      setSampleResult({ message: result.message || "Submission evaluated.", passed_sample: data.submission?.passed, status: data.submission?.status, submission: true });
    } catch (err) { setError(err.message || "Submission could not be evaluated."); }
    finally { setSubmitting(false); }
  }

  async function leaveBattle() {
    if (!battle?.id || loading) return;
    setLoading(true); setError("");
    try { await readPayload(await apiFetch(`${API_BASE}/api/battles/${battle.id}/leave`, { method: "POST", credentials: "include" })); setBattle(null); setNotice("You left the battle queue."); }
    catch (err) { setError(err.message || "Could not leave this battle."); }
    finally { setLoading(false); }
  }

  const active = battle?.status === "active";
  const waiting = battle?.status === "waiting";
  const finished = ["completed", "expired", "cancelled"].includes(battle?.status);
  return (
    <PageShell className="game-page battles-page">
      <div className="game-page-heading"><div><div className="eyebrow">CODELEAF ARENA</div><h1>Coding Battles</h1><p>Face another learner on the same beginner-friendly problem. CodeLeaf's server-side execution provider checks both solutions and the server decides the winner.</p></div><Link to="/playground" className="game-secondary-link">Open Playground</Link></div>
      {error && <div className="game-alert game-alert-error" role="alert">{error} {error.toLowerCase().includes("sign in") && <Link to="/login">Sign in</Link>}</div>}
      {notice && <div className="game-alert" role="status">{notice}</div>}
      <AchievementRewardNotice rewards={achievementRewards} xpEarned={achievementXpEarned} onDismiss={() => setAchievementRewards([])} />

      {!battle && <section className="battle-match-card panel"><div className="battle-match-icon"><Swords size={30} /></div><div className="eyebrow">FIND YOUR OPPONENT</div><h2>Ready for a quick coding duel?</h2><p>Choose a language and difficulty. Matchmaking pairs you with another learner using the same challenge and runtime.</p><div className="battle-match-controls"><label>Language<select value={language} onChange={(event) => { const next = event.target.value; setLanguage(next); setSource(starterFor(next)); }}>{supportedLanguages.includes("python") && <option value="python">Python</option>}{supportedLanguages.includes("javascript") && <option value="javascript">JavaScript</option>}</select></label><label>Difficulty<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option></select></label></div>{!supportedLanguages.length && <p className="battle-runtime-warning">Python and JavaScript battles are unavailable because no execution provider has confirmed those runtimes. Check provider availability before matchmaking.</p>}<button type="button" className="game-button game-button-primary" onClick={findOpponent} disabled={loading || !supportedLanguages.length}><Swords size={16} /> {loading ? "Finding opponent…" : "Find opponent"}</button><small>20-minute battle · 2 solution attempts · 10 XP for the winner</small></section>}

      {waiting && <section className="battle-waiting-card panel"><div className="battle-waiting-pulse"><span /><Swords size={22} /></div><div className="eyebrow">MATCHMAKING</div><h2>Waiting for another learner…</h2><p>Your challenge is selected. The battle starts as soon as someone joins the same language and difficulty queue.</p><div className="battle-waiting-meta"><span>{battle.language}</span><span>{battle.difficulty}</span><span>Challenge: {battle.challenge?.title || "Selected"}</span></div><button type="button" className="game-button game-button-quiet" onClick={leaveBattle} disabled={loading}><XCircle size={15} /> Leave queue</button></section>}

      {active && <>
        <div className="battle-statusbar panel"><div className="battle-player"><span className="battle-player-icon">{battle.my_avatar ? <DogAvatar appearance={battle.my_avatar} equipment={battle.my_avatar.equipment} size={46} /> : <UserRound size={18} />}</span><div><strong>You</strong><small>Challenge participant</small></div><span className="battle-pill battle-pill-live">LIVE</span></div><div className="battle-clock"><Clock3 size={17} /><strong>{formatTime(remaining)}</strong><small>remaining</small></div><div className="battle-player opponent"><span className="battle-player-icon">{battle.opponent?.dog_avatar ? <DogAvatar appearance={battle.opponent.dog_avatar} equipment={battle.opponent.dog_avatar.equipment} size={46} /> : <UserRound size={18} />}</span><div><strong>{battle.opponent?.display_name || battle.opponent?.username || "Opponent"}</strong><small>{battle.opponent_submission?.status || "Working"}</small></div><span className="battle-pill">OPPONENT</span></div></div>
        <div className="battle-workspace">
          <section className="battle-challenge panel"><div className="eyebrow">{battle.difficulty.toUpperCase()} CHALLENGE · {battle.language.toUpperCase()}</div><h2>{battle.challenge?.title}</h2><p>{battle.challenge?.description}</p><div className="battle-spec"><strong>Input format</strong><p>{battle.challenge?.input_format}</p><strong>Output format</strong><p>{battle.challenge?.output_format}</p><strong>Constraints</strong><p>{battle.challenge?.constraints}</p></div><div className="battle-sample"><strong>Sample input</strong><pre>{battle.challenge?.samples?.[0]?.input || ""}</pre><strong>Expected output</strong><pre>{battle.challenge?.samples?.[0]?.output || ""}</pre></div><div className="battle-trust-note"><ShieldCheck size={15} /><span>Hidden tests stay on the server. Your code is evaluated through CodeLeaf's configured isolated provider and is not saved as a battle submission.</span></div></section>
          <section className="battle-editor panel"><div className="battle-editor-toolbar"><span><Code2 size={15} /> solution.{battle.language === "python" ? "py" : "js"}</span><span>{source.length.toLocaleString()} chars</span></div><textarea spellCheck="false" autoCapitalize="off" autoCorrect="off" value={source} onChange={(event) => setSource(event.target.value)} maxLength={16_000} aria-label="Coding battle editor" /><div className="battle-editor-actions"><button type="button" className="game-button game-button-quiet" onClick={runSample} disabled={submitting || !source.trim()}><Play size={15} /> Run sample</button><button type="button" className="game-button game-button-primary" onClick={submitSolution} disabled={submitting || !source.trim()}><TerminalSquare size={15} /> {submitting ? "Evaluating…" : "Submit solution"}</button><button type="button" className="battle-leave-active" onClick={leaveBattle} disabled={submitting || loading}>Leave battle</button></div>{sampleResult && <div className={`battle-result ${sampleResult.passed_sample ? "success" : sampleResult.submission ? "neutral" : "warning"}`} role="status"><strong>{sampleResult.submission ? `Submission ${sampleResult.status}` : sampleResult.passed_sample ? "Sample passed" : "Sample not passed"}</strong><span>{sampleResult.message}</span></div>}</section>
        </div>
      </>}

      {finished && <section className={`battle-finish-card panel ${battle.status === "completed" && battle.you_won ? "winner" : ""}`}><div className="battle-finish-icon">{battle.status === "completed" ? (battle.you_won ? <Trophy size={32} /> : <Swords size={32} />) : <Clock3 size={32} />}</div><div className="eyebrow">BATTLE RESULT</div><h2>{battle.status === "completed" ? (battle.you_won ? "Victory!" : "Battle complete") : battle.status === "expired" ? "Time is up" : "Battle ended"}</h2><p>{battle.status === "completed" ? (battle.you_won ? "Your solution was the first fully correct submission. You earned 10 XP." : `${battle.winner_name || "Your opponent"} passed all hidden tests first.`) : battle.status === "expired" ? "The battle ended before a valid solution was accepted." : "This battle was cancelled."}</p><div className="battle-finish-actions"><button type="button" className="game-button game-button-primary" onClick={() => { setBattle(null); setSampleResult(null); setAchievementRewards([]); setAchievementXpEarned(0); setNotice(""); void findOpponent(); }} disabled={loading}><RotateCcw size={15} /> Play again</button><Link to="/dashboard" className="game-button game-button-quiet">Dashboard <ArrowLeft size={15} /></Link></div></section>}

      {!battle && <div className="battle-footer-note"><ShieldCheck size={15} /><span>Python and JavaScript use OnlineCompiler when its live health check succeeds; CodeLeaf Runner remains available as fallback. Provider errors never create a winner or award battle XP.</span></div>}
    </PageShell>
  );
}
