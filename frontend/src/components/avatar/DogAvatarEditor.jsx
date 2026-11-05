import { useEffect, useMemo, useState } from "react";
import { Check, Lock, RotateCcw, Save, Sparkles, Trophy, Undo2 } from "lucide-react";
import DogAvatar from "./DogAvatar.jsx";
import AvatarItemArtwork from "./AvatarItemArtwork.jsx";
import { useDogAvatar } from "./DogAvatarContext.jsx";
import { apiFetch } from "../../lib/apiClient.js";
import { API_BASE } from "../../lib/demoState.js";
import "../../styles/games.css";

async function readPayload(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof payload.detail === "string" ? payload.detail : payload.message || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return payload;
}

const CATEGORIES = [
  "All", "Headwear", "Ears", "Eyes", "Glasses", "Face Accessories", "Shirts",
  "Hoodies", "Jackets", "Full Outfits", "Pants", "Shoes", "Collars",
  "Neck Accessories", "Accessories", "Special Items", "Backgrounds",
];
const BREEDS = [
  ["classic", "Classic Dog"], ["shiba", "Shiba Inu"], ["husky", "Husky"],
  ["retriever", "Golden Retriever"], ["corgi", "Corgi"], ["bulldog", "Bulldog"],
];
const COLORS = [
  ["golden", "Golden"], ["cream", "Cream"], ["chocolate", "Chocolate"],
  ["charcoal", "Charcoal"], ["snow", "Snow"], ["copper", "Copper"],
];
const EYE_COLORS = [["brown", "Brown"], ["blue", "Blue"], ["green", "Green"], ["amber", "Amber"]];

function cloneAppearance(value = {}) {
  return {
    breed: value.breed || "classic",
    fur_color: value.fur_color || "golden",
    eye_color: value.eye_color || "brown",
  };
}

function cloneEquipment(value = {}) {
  const next = value && typeof value === "object" && !Array.isArray(value) ? { ...value } : {};
  // Older saved profiles could contain both clothing slots; the current renderer
  // supports one top layer and uses the explicitly equipped shirt as the winner.
  if (next.shirt && next.outfit) delete next.outfit;
  return next;
}

function equipmentWithItem(equipment, item) {
  const next = { ...equipment };
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
  const appearance = avatar.appearance || {};
  const equipment = cloneEquipment(avatar.equipment);
  const catalog = Array.isArray(avatar.catalog) ? avatar.catalog : [];

  const [draftAppearance, setDraftAppearance] = useState(() => cloneAppearance(appearance));
  const [draftEquipment, setDraftEquipment] = useState(() => cloneEquipment(equipment));
  const [category, setCategory] = useState("All");
  const [selectedItemId, setSelectedItemId] = useState("");
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  // Keep a clean draft in sync with account/session changes. Never overwrite a
  // learner's unsaved preview while the editor is open.
  useEffect(() => {
    if (dirty || dogAvatarLoading) return;
    setDraftAppearance(cloneAppearance(avatar.appearance));
    setDraftEquipment(cloneEquipment(avatar.equipment));
    setSelectedItemId("");
  }, [avatar.appearance, avatar.equipment, dirty, dogAvatarLoading]);

  const filteredItems = useMemo(() => {
    if (category === "All") return catalog;
    if (category === "Hoodies") return catalog.filter((item) => item.name.toLowerCase().includes("hoodie"));
    if (category === "Jackets") return catalog.filter((item) => item.name.toLowerCase().includes("jacket"));
    if (category === "Face Accessories") return catalog.filter((item) => item.slot === "face" || item.slot === "glasses");
    return catalog.filter((item) => item.category === category);
  }, [catalog, category]);

  const ownedCount = avatar.owned_item_ids?.length || 0;
  const visibleError = error || dogAvatarError;
  const equippedItems = catalog.filter((item) => draftEquipment[item.slot] === item.id);
  const savedAppearance = cloneAppearance(avatar.appearance);
  const savedEquipment = cloneEquipment(avatar.equipment);

  function changeAppearance(patch) {
    setDraftAppearance((current) => ({ ...current, ...patch }));
    setDirty(true);
    setError("");
    setNotice("Preview updated. Save your changes to apply them across CodeLeaf.");
  }

  function previewItem(item) {
    if (!item?.owned || busy || dogAvatarLoading) return;
    const isInPreview = draftEquipment[item.slot] === item.id;
    setDraftEquipment((current) => {
      if (isInPreview) {
        const next = { ...current };
        delete next[item.slot];
        return next;
      }
      return equipmentWithItem(current, item);
    });
    setSelectedItemId(isInPreview ? "" : item.id);
    setDirty(true);
    setError("");
    setNotice(isInPreview ? `${item.name} removed from the preview.` : `${item.name} previewed on your dog. Nothing is saved yet.`);
  }

  function discardPreview() {
    setDraftAppearance(savedAppearance);
    setDraftEquipment(savedEquipment);
    setSelectedItemId("");
    setDirty(false);
    setError("");
    setNotice("Unsaved preview changes were discarded.");
  }

  function resetPreview() {
    setDraftAppearance({ breed: "classic", fur_color: "golden", eye_color: "brown" });
    setDraftEquipment({});
    setSelectedItemId("");
    setDirty(true);
    setError("");
    setNotice("Default dog appearance is ready to save. Your unlocked inventory is unchanged.");
  }

  async function retryLoad() {
    setError("");
    setNotice("");
    await refreshDogAvatar({ force: true });
  }

  async function saveAvatar() {
    if (!dirty || busy || dogAvatarLoading) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const data = await readPayload(await apiFetch(`${API_BASE}/api/me/avatar`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ appearance: draftAppearance, equipment: draftEquipment }),
      }));
      const nextEquipment = cloneEquipment(data.equipment);
      const updated = updateDogAvatar({
        ...avatar,
        appearance: cloneAppearance(data.appearance),
        equipment: nextEquipment,
        catalog: catalog.map((item) => ({
          ...item,
          equipped: nextEquipment[item.slot] === item.id,
        })),
      });
      window.dispatchEvent(new CustomEvent("codeleaf:dog-avatar-changed", { detail: { dogAvatar: updated } }));
      setDraftAppearance(cloneAppearance(data.appearance));
      setDraftEquipment(nextEquipment);
      setSelectedItemId("");
      setDirty(false);
      setNotice("Your dog has been saved and synchronized across CodeLeaf.");
    } catch (err) {
      setError(err.message || "Your dog could not be saved. Your previous saved appearance is unchanged.");
      // Keep the draft visible so the learner does not lose their preview work.
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`profile-dog-editor ${compact ? "profile-dog-editor-compact" : ""}`} id="dog-avatar">
      {visibleError && <div className="game-alert game-alert-error" role="alert">
        {visibleError}
        <button type="button" className="text-link" onClick={retryLoad} disabled={dogAvatarLoading || busy}>Retry</button>
      </div>}
      {notice && <div className="game-alert" role="status">{notice}</div>}
      {dogAvatarLoading ? (
        <div className="avatar-catalog-empty" role="status">Loading your profile dog…</div>
      ) : (
        <>
          <div className="profile-dog-editor-main">
            <section className="profile-dog-editor-preview panel" aria-label="Live dog preview">
              <div className="avatar-preview-top">
                <span><Sparkles size={14} /> PROFILE DOG · LIVE PREVIEW</span>
                <span>{ownedCount} owned</span>
              </div>
              <div className="profile-dog-stage">
                <DogAvatar appearance={draftAppearance} equipment={draftEquipment} size={compact ? 250 : 280} />
              </div>
              <div className="avatar-appearance-controls">
                <label>Breed<select disabled={busy} value={draftAppearance.breed} onChange={(event) => changeAppearance({ breed: event.target.value })}>{BREEDS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
                <label>Fur color<select disabled={busy} value={draftAppearance.fur_color} onChange={(event) => changeAppearance({ fur_color: event.target.value })}>{COLORS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
                <label>Eye color<select disabled={busy} value={draftAppearance.eye_color} onChange={(event) => changeAppearance({ eye_color: event.target.value })}>{EYE_COLORS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
              </div>
              <div className="avatar-equipped-list">
                <strong>Currently in preview</strong>
                <div>
                  {equippedItems.length ? equippedItems.map((item) => <span key={item.id}>{item.name}</span>) : <small>No accessories selected</small>}
                </div>
              </div>
              <button className="game-button game-button-quiet avatar-reset-button" type="button" onClick={resetPreview} disabled={busy}>
                <RotateCcw size={14} /> Reset preview
              </button>
              <div className="avatar-editor-actions">
                <button className="game-button game-button-quiet" type="button" onClick={discardPreview} disabled={!dirty || busy}>
                  <Undo2 size={14} /> Discard preview
                </button>
                <button className="game-button game-button-primary" type="button" onClick={saveAvatar} disabled={!dirty || busy}>
                  <Save size={14} /> {busy ? "Saving…" : "Save changes"}
                </button>
              </div>
            </section>

            <section className="profile-dog-editor-catalog panel">
              <div className="avatar-catalog-heading">
                <div><div className="eyebrow">YOUR WARDROBE</div><h3>Accessories & outfits</h3><p>Select an owned item to preview it on the large dog. Previewing never changes your inventory or saves automatically.</p></div>
                <div className="avatar-collection-count"><Trophy size={15} /><strong>{ownedCount}</strong><small>owned</small></div>
              </div>
              <div className="avatar-category-tabs" role="tablist" aria-label="Dog accessory categories">
                {CATEGORIES.map((item) => <button type="button" role="tab" aria-selected={category === item} className={category === item ? "active" : ""} key={item} onClick={() => setCategory(item)}>{item}</button>)}
              </div>
              {filteredItems.length ? (
                <div className="avatar-item-grid profile-dog-item-grid">
                  {filteredItems.map((item) => {
                    const isInPreview = draftEquipment[item.slot] === item.id;
                    const selected = selectedItemId === item.id;
                    return (
                      <article className={`avatar-item-card ${item.owned ? "is-owned" : "is-locked"} ${isInPreview ? "is-equipped" : ""} ${selected ? "is-selected" : ""}`} key={item.id}>
                        <button type="button" className="avatar-item-preview-button" onClick={() => previewItem(item)} disabled={!item.owned || busy} aria-pressed={isInPreview}>
                          <AvatarItemArtwork item={item} />
                          {isInPreview && <i className="avatar-item-owned-mark" aria-label="In current preview"><Check size={12} /></i>}
                          {!item.owned && <i className="avatar-lock" aria-label="Locked"><Lock size={12} /></i>}
                        </button>
                        <div className="avatar-item-copy"><strong>{item.name}</strong><small>{item.category} · {item.rarity}</small></div>
                        {item.owned ? (
                          <button type="button" className={`avatar-item-action ${isInPreview ? "equipped" : ""}`} disabled={busy} onClick={() => previewItem(item)}>
                            {isInPreview ? "Remove preview" : "Preview item"}
                          </button>
                        ) : (
                          <div className="avatar-item-requirement">{item.unlock_requirement || "Unlock this item to preview it."}</div>
                        )}
                      </article>
                    );
                  })}
                </div>
              ) : (
                <div className="avatar-catalog-empty"><Sparkles size={22} /><strong>No items in this category yet</strong></div>
              )}
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
