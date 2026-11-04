import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Lock, RotateCcw, Sparkles, Trophy, WandSparkles } from "lucide-react";
import { PageShell } from "../components/common.jsx";
import DogAvatar from "../components/avatar/DogAvatar.jsx";
import { apiFetch } from "../lib/apiClient.js";
import { API_BASE } from "../lib/demoState.js";
import "../styles/games.css";

async function readPayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : payload.message || `Request failed (${response.status})`);
  return payload;
}

const CATEGORIES = ["All", "Headwear", "Ears", "Eyes", "Glasses", "Face Accessories", "Shirts", "Hoodies", "Jackets", "Full Outfits", "Pants", "Shoes", "Collars", "Neck Accessories", "Accessories", "Special Items", "Backgrounds"];
const BREEDS = [
  ["classic", "Classic Dog"], ["shiba", "Shiba Inu"], ["husky", "Husky"],
  ["retriever", "Golden Retriever"], ["corgi", "Corgi"], ["bulldog", "Bulldog"],
];
const COLORS = [["golden", "Golden"], ["cream", "Cream"], ["chocolate", "Chocolate"], ["charcoal", "Charcoal"], ["snow", "Snow"], ["copper", "Copper"]];

export default function AvatarStudioPage() {
  const [avatar, setAvatar] = useState({ appearance: { breed: "classic", fur_color: "golden", eye_color: "brown" }, equipment: {}, catalog: [], achievements: [], owned_item_ids: [] });
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  async function loadAvatar() {
    setLoading(true);
    setError("");
    try {
      const data = await readPayload(await apiFetch(`${API_BASE}/api/me/avatar`, { credentials: "include" }));
      setAvatar(data);
    } catch (err) {
      setError(err.message || "The avatar collection could not be loaded.");
    } finally { setLoading(false); }
  }

  useEffect(() => { void loadAvatar(); }, []);

  const filteredItems = useMemo(() => {
    if (category === "All") return avatar.catalog || [];
    if (category === "Hoodies") return (avatar.catalog || []).filter((item) => item.name.toLowerCase().includes("hoodie"));
    if (category === "Jackets") return (avatar.catalog || []).filter((item) => item.name.toLowerCase().includes("jacket"));
    if (category === "Face Accessories") return (avatar.catalog || []).filter((item) => item.slot === "face" || item.slot === "glasses");
    return (avatar.catalog || []).filter((item) => item.category === category);
  }, [avatar.catalog, category]);

  async function updateAppearance(patch) {
    const next = { ...avatar.appearance, ...patch };
    setAvatar((current) => ({ ...current, appearance: next }));
    setBusy(true); setError(""); setNotice("");
    try {
      await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/appearance`, {
        method: "PATCH", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(next),
      }));
      setNotice("Your dog's appearance was saved to your account.");
    } catch (err) {
      setError(err.message || "Appearance could not be saved.");
      await loadAvatar();
    } finally { setBusy(false); }
  }

  async function equip(item) {
    if (!item.owned || busy) return;
    const itemId = item.equipped ? null : item.id;
    setBusy(true); setError(""); setNotice("");
    try {
      const data = await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/equipment`, {
        method: "PUT", credentials: "include", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slot: item.slot, item_id: itemId }),
      }));
      setAvatar((current) => ({ ...current, equipment: data.equipment, catalog: current.catalog.map((entry) => ({ ...entry, equipped: entry.slot === item.slot ? entry.id === itemId : entry.equipped })) }));
      setNotice(itemId ? `${item.name} equipped.` : `${item.name} unequipped.`);
    } catch (err) { setError(err.message || "That item could not be equipped."); }
    finally { setBusy(false); }
  }

  async function resetAvatar() {
    if (busy) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/reset`, { method: "POST", credentials: "include" }));
      await loadAvatar();
      setNotice("Your dog avatar has been reset. Your unlocked items are still yours.");
    } catch (err) { setError(err.message || "Avatar reset failed."); }
    finally { setBusy(false); }
  }

  const ownedCount = avatar.owned_item_ids?.length || 0;
  return (
    <PageShell className="game-page avatar-studio-page">
      <div className="game-page-heading">
        <div><div className="eyebrow">YOUR CODELEAF COMPANION</div><h1>Dog Avatar Studio</h1><p>Build a dog character that reflects your learning journey. Your inventory and equipped items stay synced to your account.</p></div>
        <Link to="/profile" className="game-secondary-link">Back to profile</Link>
      </div>
      {error && <div className="game-alert game-alert-error" role="alert">{error} {error.toLowerCase().includes("sign in") && <Link to="/login">Sign in</Link>}</div>}
      {notice && <div className="game-alert" role="status">{notice}</div>}
      <div className="avatar-studio-layout">
        <section className="avatar-preview-panel panel">
          <div className="avatar-preview-top"><span><Sparkles size={15} /> LIVE AVATAR</span><span>{ownedCount} / {avatar.catalog?.length || 0} owned</span></div>
          <div className="dog-preview-stage"><DogAvatar appearance={avatar.appearance} equipment={avatar.equipment} size={300} /></div>
          <div className="avatar-preview-name"><strong>{BREEDS.find(([id]) => id === avatar.appearance?.breed)?.[1] || "CodeLeaf Dog"}</strong><span>CodeLeaf learner companion</span></div>
          <div className="avatar-appearance-controls">
            <label>Dog breed<select disabled={busy || loading} value={avatar.appearance?.breed || "classic"} onChange={(event) => updateAppearance({ breed: event.target.value })}>{BREEDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
            <label>Fur color<select disabled={busy || loading} value={avatar.appearance?.fur_color || "golden"} onChange={(event) => updateAppearance({ fur_color: event.target.value })}>{COLORS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
            <label>Eye color<select disabled={busy || loading} value={avatar.appearance?.eye_color || "brown"} onChange={(event) => updateAppearance({ eye_color: event.target.value })}><option value="brown">Brown</option><option value="blue">Blue</option><option value="green">Green</option><option value="amber">Amber</option></select></label>
          </div>
          <button className="game-button game-button-quiet avatar-reset-button" type="button" onClick={resetAvatar} disabled={busy || loading}><RotateCcw size={15} /> Reset appearance</button>
          <div className="avatar-equipped-list"><strong>Currently equipped</strong><div>{Object.entries(avatar.equipment || {}).length ? Object.entries(avatar.equipment).map(([slot, id]) => <span key={slot}>{avatar.catalog?.find((item) => item.id === id)?.name || id}</span>) : <small>No accessories equipped yet.</small>}</div></div>
        </section>

        <section className="avatar-catalog-panel panel">
          <div className="avatar-catalog-heading"><div><div className="eyebrow">COSMETIC COLLECTION</div><h2>Customize your dog</h2><p>Unlocked items can be equipped immediately. Locked items show the achievement needed to earn them.</p></div><div className="avatar-collection-count"><Trophy size={17} /><strong>{ownedCount}</strong><small>unlocked</small></div></div>
          <div className="avatar-category-tabs" role="tablist" aria-label="Avatar item categories">{CATEGORIES.map((item) => <button type="button" role="tab" aria-selected={category === item} className={category === item ? "active" : ""} key={item} onClick={() => setCategory(item)}>{item}</button>)}</div>
          {loading ? <div className="avatar-catalog-empty">Loading your collection…</div> : filteredItems.length ? <div className="avatar-item-grid">{filteredItems.map((item) => <article className={`avatar-item-card ${item.owned ? "is-owned" : "is-locked"} ${item.equipped ? "is-equipped" : ""}`} key={item.id}>
            <div className="avatar-item-visual"><span>{item.icon}</span>{item.equipped && <i><Check size={12} /></i>}{!item.owned && <i className="avatar-lock"><Lock size={12} /></i>}</div>
            <div className="avatar-item-copy"><strong>{item.name}</strong><small>{item.category} · {item.rarity}</small></div>
            {item.owned ? <button type="button" className={`avatar-item-action ${item.equipped ? "equipped" : ""}`} disabled={busy} onClick={() => equip(item)}>{item.equipped ? "Unequip" : "Equip"}</button> : <div className="avatar-item-requirement">{item.unlock_requirement}</div>}
          </article>)}</div> : <div className="avatar-catalog-empty"><WandSparkles size={24} /><strong>No items in this category yet</strong><span>More cosmetic slots can be added as the collection grows.</span></div>}
        </section>
      </div>

      <section className="avatar-achievements panel">
        <div className="eyebrow">REWARDS ROADMAP</div><h2>Achievements & unlocks</h2><p>Every achievement in this catalogue grants one designated accessory, once. Progress is calculated from server-recorded activity.</p>
        <div className="avatar-achievement-grid">{(avatar.achievements || []).map((achievement) => <article className={`avatar-achievement-card ${achievement.unlocked ? "unlocked" : ""}`} key={achievement.id}><span className="achievement-check">{achievement.unlocked ? <Check size={14} /> : <Lock size={13} />}</span><div><strong>{achievement.name}</strong><p>{achievement.description}</p><small>Reward: {achievement.reward_item_name}</small></div></article>)}</div>
      </section>
    </PageShell>
  );
}
