import { useEffect, useMemo, useState } from "react";
import { Check, Lock, RotateCcw, Sparkles, Trophy, WandSparkles } from "lucide-react";
import DogAvatar from "./DogAvatar.jsx";
import { useDogAvatar } from "./DogAvatarContext.jsx";
import { apiFetch } from "../../lib/apiClient.js";
import { API_BASE } from "../../lib/demoState.js";
import "../../styles/games.css";

async function readPayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(typeof payload.detail === "string" ? payload.detail : payload.message || `Request failed (${response.status})`);
  }
  return payload;
}

const CATEGORIES = ["All", "Headwear", "Ears", "Eyes", "Glasses", "Face Accessories", "Shirts", "Hoodies", "Jackets", "Full Outfits", "Pants", "Shoes", "Collars", "Neck Accessories", "Accessories", "Special Items", "Backgrounds"];
const BREEDS = [
  ["classic", "Classic Dog"], ["shiba", "Shiba Inu"], ["husky", "Husky"],
  ["retriever", "Golden Retriever"], ["corgi", "Corgi"], ["bulldog", "Bulldog"],
];
const COLORS = [["golden", "Golden"], ["cream", "Cream"], ["chocolate", "Chocolate"], ["charcoal", "Charcoal"], ["snow", "Snow"], ["copper", "Copper"]];

export default function DogAvatarEditor({ compact = false }) {
  const { updateDogAvatar } = useDogAvatar();
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
      updateDogAvatar(data);
    } catch (err) {
      setError(err.message || "Your dog customization could not be loaded. Sign in to edit your account dog.");
    } finally {
      setLoading(false);
    }
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
    if (busy || loading) return;
    const next = { ...avatar.appearance, ...patch };
    setAvatar((current) => ({ ...current, appearance: next }));
    setBusy(true); setError(""); setNotice("");
    try {
      await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/appearance`, {
        method: "PATCH", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(next),
      }));
      const updated = { ...avatar, appearance: next };
      updateDogAvatar(updated);
      window.dispatchEvent(new CustomEvent("codeleaf:dog-avatar-changed", { detail: { dogAvatar: updated } }));
      setNotice("Your dog's appearance has been saved to your profile.");
    } catch (err) {
      setError(err.message || "Appearance could not be saved.");
      await loadAvatar();
    } finally { setBusy(false); }
  }

  async function equip(item) {
    if (!item.owned || busy || loading) return;
    const itemId = item.equipped ? null : item.id;
    setBusy(true); setError(""); setNotice("");
    try {
      const data = await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/equipment`, {
        method: "PUT", credentials: "include", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slot: item.slot, item_id: itemId }),
      }));
      const updated = {
        ...avatar,
        equipment: data.equipment || {},
        catalog: (avatar.catalog || []).map((entry) => ({ ...entry, equipped: entry.slot === item.slot ? entry.id === itemId : entry.equipped })),
      };
      setAvatar(updated);
      updateDogAvatar(updated);
      window.dispatchEvent(new CustomEvent("codeleaf:dog-avatar-changed", { detail: { dogAvatar: updated } }));
      setNotice(itemId ? `${item.name} equipped on your profile dog.` : `${item.name} removed from your profile dog.`);
    } catch (err) { setError(err.message || "That item could not be equipped."); }
    finally { setBusy(false); }
  }

  async function resetAvatar() {
    if (busy || loading) return;
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/reset`, { method: "POST", credentials: "include" }));
      const updated = { ...avatar, appearance: result.appearance || { breed: "classic", fur_color: "golden", eye_color: "brown" }, equipment: result.equipment || {} };
      updated.catalog = (avatar.catalog || []).map((item) => ({ ...item, equipped: false }));
      setAvatar(updated);
      updateDogAvatar(updated);
      window.dispatchEvent(new CustomEvent("codeleaf:dog-avatar-changed", { detail: { dogAvatar: updated } }));
      setNotice("Your profile dog has been reset. Your unlocked items are still yours.");
    } catch (err) { setError(err.message || "Avatar reset failed."); }
    finally { setBusy(false); }
  }

  const ownedCount = avatar.owned_item_ids?.length || 0;
  return (
    <div className={`profile-dog-editor ${compact ? "profile-dog-editor-compact" : ""}`} id="dog-avatar">
      {error && <div className="game-alert game-alert-error" role="alert">{error}</div>}
      {notice && <div className="game-alert" role="status">{notice}</div>}
      {loading ? <div className="avatar-catalog-empty">Loading your dog and unlocked accessories…</div> : (
        <>
          <div className="profile-dog-editor-main">
            <section className="profile-dog-editor-preview panel">
              <div className="avatar-preview-top"><span><Sparkles size={14} /> PROFILE DOG</span><span>{ownedCount} unlocked</span></div>
              <div className="profile-dog-stage"><DogAvatar appearance={avatar.appearance} equipment={avatar.equipment} size={compact ? 174 : 210} /></div>
              <div className="avatar-appearance-controls">
                <label>Breed<select disabled={busy} value={avatar.appearance?.breed || "classic"} onChange={(event) => updateAppearance({ breed: event.target.value })}>{BREEDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
                <label>Fur color<select disabled={busy} value={avatar.appearance?.fur_color || "golden"} onChange={(event) => updateAppearance({ fur_color: event.target.value })}>{COLORS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
                <label>Eye color<select disabled={busy} value={avatar.appearance?.eye_color || "brown"} onChange={(event) => updateAppearance({ eye_color: event.target.value })}><option value="brown">Brown</option><option value="blue">Blue</option><option value="green">Green</option><option value="amber">Amber</option></select></label>
              </div>
              <button className="game-button game-button-quiet avatar-reset-button" type="button" onClick={resetAvatar} disabled={busy}><RotateCcw size={14} /> Reset dog appearance</button>
            </section>
            <section className="profile-dog-editor-catalog panel">
              <div className="avatar-catalog-heading"><div><div className="eyebrow">YOUR UNLOCKED ITEMS</div><h3>Accessories & outfits</h3><p>Equip items you have earned. Locked rewards show how to unlock them.</p></div><div className="avatar-collection-count"><Trophy size={15} /><strong>{ownedCount}</strong><small>owned</small></div></div>
              <div className="avatar-category-tabs" role="tablist" aria-label="Dog accessory categories">{CATEGORIES.map((item) => <button type="button" role="tab" aria-selected={category === item} className={category === item ? "active" : ""} key={item} onClick={() => setCategory(item)}>{item}</button>)}</div>
              {filteredItems.length ? <div className="avatar-item-grid profile-dog-item-grid">{filteredItems.map((item) => <article className={`avatar-item-card ${item.owned ? "is-owned" : "is-locked"} ${item.equipped ? "is-equipped" : ""}`} key={item.id}>
                <div className="avatar-item-visual"><span>{item.icon}</span>{item.equipped && <i><Check size={12} /></i>}{!item.owned && <i className="avatar-lock"><Lock size={12} /></i>}</div>
                <div className="avatar-item-copy"><strong>{item.name}</strong><small>{item.category} · {item.rarity}</small></div>
                {item.owned ? <button type="button" className={`avatar-item-action ${item.equipped ? "equipped" : ""}`} disabled={busy} onClick={() => equip(item)}>{item.equipped ? "Unequip" : "Equip"}</button> : <div className="avatar-item-requirement">{item.unlock_requirement}</div>}
              </article>)}</div> : <div className="avatar-catalog-empty"><WandSparkles size={22} /><strong>No items in this category yet</strong></div>}
            </section>
          </div>
          {avatar.achievements?.length > 0 && <section className="profile-dog-achievements panel"><div className="eyebrow">DOG REWARDS</div><h3>Achievements that unlock items</h3><div className="avatar-achievement-grid">{avatar.achievements.map((achievement) => <article className={`avatar-achievement-card ${achievement.unlocked ? "unlocked" : ""}`} key={achievement.id}><span className="achievement-check">{achievement.unlocked ? <Check size={14} /> : <Lock size={13} />}</span><div><strong>{achievement.name}</strong><p>{achievement.description}</p><small>Reward: {achievement.reward_item_name}</small></div></article>)}</div></section>}
        </>
      )}
    </div>
  );
}
