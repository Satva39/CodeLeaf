import { useMemo, useState } from "react";
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

function equipmentForItem(currentEquipment, item) {
  const next = { ...(currentEquipment || {}) };
  // A jacket/shirt and a full outfit share one visible clothing layer.
  if (item.slot === "shirt") delete next.outfit;
  if (item.slot === "outfit") delete next.shirt;
  next[item.slot] = item.id;
  return next;
}

export default function DogAvatarEditor({ compact = false }) {
  const {
    dogAvatar,
    dogAvatarLoading,
    dogAvatarError,
    refreshDogAvatar,
    updateDogAvatar,
  } = useDogAvatar();
  const avatar = dogAvatar || {};
  const appearance = avatar.appearance || { breed: "classic", fur_color: "golden", eye_color: "brown" };
  const equipment = avatar.equipment || {};
  const catalog = Array.isArray(avatar.catalog) ? avatar.catalog : [];

  const [category, setCategory] = useState("All");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const filteredItems = useMemo(() => {
    if (category === "All") return catalog;
    if (category === "Hoodies") return catalog.filter((item) => item.name.toLowerCase().includes("hoodie"));
    if (category === "Jackets") return catalog.filter((item) => item.name.toLowerCase().includes("jacket"));
    if (category === "Face Accessories") return catalog.filter((item) => item.slot === "face" || item.slot === "glasses");
    return catalog.filter((item) => item.category === category);
  }, [catalog, category]);

  async function retryLoad() {
    setError("");
    setNotice("");
    await refreshDogAvatar({ force: true });
  }

  async function updateAppearance(patch) {
    if (busy || dogAvatarLoading) return;
    const next = { ...appearance, ...patch };
    const previous = appearance;
    setBusy(true);
    setError("");
    setNotice("");
    updateDogAvatar({ ...avatar, appearance: next });
    try {
      await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/appearance`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(next),
      }));
      const updated = updateDogAvatar({ ...avatar, appearance: next });
      window.dispatchEvent(new CustomEvent("codeleaf:dog-avatar-changed", { detail: { dogAvatar: updated } }));
      setNotice("Your dog's appearance has been saved to your profile.");
    } catch (err) {
      updateDogAvatar({ ...avatar, appearance: previous });
      setError(err.message || "Appearance could not be saved.");
      await refreshDogAvatar({ force: true });
    } finally {
      setBusy(false);
    }
  }

  async function equip(item) {
    if (!item.owned || busy || dogAvatarLoading) return;
    const itemId = item.equipped ? null : item.id;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const data = await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/equipment`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slot: item.slot, item_id: itemId }),
      }));
      const nextEquipment = data.equipment || {};
      const updated = updateDogAvatar({
        ...avatar,
        equipment: nextEquipment,
        catalog: catalog.map((entry) => ({
          ...entry,
          equipped: nextEquipment[entry.slot] === entry.id,
        })),
      });
      window.dispatchEvent(new CustomEvent("codeleaf:dog-avatar-changed", { detail: { dogAvatar: updated } }));
      setNotice(itemId ? `${item.name} equipped on your profile dog.` : `${item.name} removed from your profile dog.`);
    } catch (err) {
      setError(err.message || "That item could not be equipped.");
      await refreshDogAvatar({ force: true });
    } finally {
      setBusy(false);
    }
  }

  async function resetAvatar() {
    if (busy || dogAvatarLoading) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await readPayload(await apiFetch(`${API_BASE}/api/me/avatar/reset`, {
        method: "POST",
        credentials: "include",
      }));
      const updated = updateDogAvatar({
        ...avatar,
        appearance: result.appearance || { breed: "classic", fur_color: "golden", eye_color: "brown" },
        equipment: result.equipment || {},
        catalog: catalog.map((item) => ({ ...item, equipped: false })),
      });
      window.dispatchEvent(new CustomEvent("codeleaf:dog-avatar-changed", { detail: { dogAvatar: updated } }));
      setNotice("Your profile dog has been reset. Your unlocked items are still yours.");
    } catch (err) {
      setError(err.message || "Avatar reset failed.");
      await refreshDogAvatar({ force: true });
    } finally {
      setBusy(false);
    }
  }

  const ownedCount = avatar.owned_item_ids?.length || 0;
  const visibleError = error || dogAvatarError;

  return (
    <div className={`profile-dog-editor ${compact ? "profile-dog-editor-compact" : ""}`} id="dog-avatar">
      {visibleError && <div className="game-alert game-alert-error" role="alert">
        {visibleError}
        <button type="button" className="text-link" onClick={retryLoad} disabled={dogAvatarLoading}>Retry</button>
      </div>}
      {notice && <div className="game-alert" role="status">{notice}</div>}
      {dogAvatarLoading ? (
        <div className="avatar-catalog-empty" role="status">Loading your profile dog…</div>
      ) : (
        <>
          <div className="profile-dog-editor-main">
            <section className="profile-dog-editor-preview panel">
              <div className="avatar-preview-top"><span><Sparkles size={14} /> PROFILE DOG</span><span>{ownedCount} unlocked</span></div>
              <div className="profile-dog-stage">
                <DogAvatar appearance={appearance} equipment={equipment} size={compact ? 190 : 220} />
              </div>
              <div className="avatar-appearance-controls">
                <label>Breed<select disabled={busy} value={appearance.breed || "classic"} onChange={(event) => updateAppearance({ breed: event.target.value })}>{BREEDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
                <label>Fur color<select disabled={busy} value={appearance.fur_color || "golden"} onChange={(event) => updateAppearance({ fur_color: event.target.value })}>{COLORS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
                <label>Eye color<select disabled={busy} value={appearance.eye_color || "brown"} onChange={(event) => updateAppearance({ eye_color: event.target.value })}><option value="brown">Brown</option><option value="blue">Blue</option><option value="green">Green</option><option value="amber">Amber</option></select></label>
              </div>
              <button className="game-button game-button-quiet avatar-reset-button" type="button" onClick={resetAvatar} disabled={busy}><RotateCcw size={14} /> Reset dog appearance</button>
            </section>

            <section className="profile-dog-editor-catalog panel">
              <div className="avatar-catalog-heading"><div><div className="eyebrow">YOUR UNLOCKED ITEMS</div><h3>Accessories & outfits</h3><p>Preview each item on your dog before equipping it. The same appearance is used in your profile, navigation and leaderboard.</p></div><div className="avatar-collection-count"><Trophy size={15} /><strong>{ownedCount}</strong><small>owned</small></div></div>
              <div className="avatar-category-tabs" role="tablist" aria-label="Dog accessory categories">{CATEGORIES.map((item) => <button type="button" role="tab" aria-selected={category === item} className={category === item ? "active" : ""} key={item} onClick={() => setCategory(item)}>{item}</button>)}</div>
              {filteredItems.length ? (
                <div className="avatar-item-grid profile-dog-item-grid">
                  {filteredItems.map((item) => {
                    const previewEquipment = equipmentForItem(equipment, item);
                    return (
                      <article className={`avatar-item-card ${item.owned ? "is-owned" : "is-locked"} ${item.equipped ? "is-equipped" : ""}`} key={item.id}>
                        <div className="avatar-item-visual">
                          <DogAvatar
                            appearance={appearance}
                            equipment={previewEquipment}
                            size={96}
                            title={`${item.name} on your profile dog`}
                          />
                          {item.equipped && <i aria-label="Currently equipped"><Check size={12} /></i>}
                          {!item.owned && <i className="avatar-lock" aria-label="Locked"><Lock size={12} /></i>}
                        </div>
                        <div className="avatar-item-copy"><strong>{item.name}</strong><small>{item.category} · {item.rarity}</small></div>
                        {item.owned ? <button type="button" className={`avatar-item-action ${item.equipped ? "equipped" : ""}`} disabled={busy} onClick={() => equip(item)}>{item.equipped ? "Unequip" : "Equip"}</button> : <div className="avatar-item-requirement">{item.unlock_requirement}</div>}
                      </article>
                    );
                  })}
                </div>
              ) : <div className="avatar-catalog-empty"><WandSparkles size={22} /><strong>No items in this category yet</strong></div>}
            </section>
          </div>

          {avatar.achievements?.length > 0 && (
            <section className="profile-dog-achievements panel">
              <div className="eyebrow">DOG REWARDS</div>
              <h3>Achievements that unlock items</h3>
              <div className="avatar-achievement-grid">
                {avatar.achievements.map((achievement) => (
                  <article className={`avatar-achievement-card ${achievement.unlocked ? "unlocked" : ""}`} key={achievement.id}>
                    <span className="achievement-check">{achievement.unlocked ? <Check size={14} /> : <Lock size={13} />}</span>
                    <div><strong>{achievement.name}</strong><p>{achievement.description}</p><small>Reward: {achievement.reward_item_name}</small></div>
                  </article>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
