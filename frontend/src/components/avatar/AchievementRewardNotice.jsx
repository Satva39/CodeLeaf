import { useState } from "react";
import { Link } from "react-router-dom";
import { Check, Gift, Sparkles, X } from "lucide-react";
import { apiFetch } from "../../lib/apiClient.js";
import { API_BASE } from "../../lib/demoState.js";

export default function AchievementRewardNotice({ rewards = [], xpEarned = 0, onDismiss }) {
  const [equipping, setEquipping] = useState(false);
  const [equippedId, setEquippedId] = useState("");
  const [error, setError] = useState("");
  if (!Array.isArray(rewards) || rewards.length === 0) return null;
  const first = rewards[0];
  async function equipNow() {
    if (!first?.item_id || !first?.item_slot || equipping) return;
    setEquipping(true); setError("");
    try {
      const response = await apiFetch(`${API_BASE}/api/me/avatar/equipment`, {
        method: "PUT", credentials: "include", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slot: first.item_slot, item_id: first.item_id }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Could not equip this reward.");
      setEquippedId(first.item_id);
      window.dispatchEvent(new CustomEvent("codeleaf:dog-avatar-changed"));
    } catch (err) { setError(err.message || "Could not equip this reward."); }
    finally { setEquipping(false); }
  }
  return (
    <section className="achievement-reward-notice" role="status" aria-live="polite">
      <button className="achievement-reward-dismiss" type="button" aria-label="Dismiss reward notification" onClick={onDismiss}><X size={15} /></button>
      <div className="achievement-reward-icon"><Gift size={20} /></div>
      <div className="achievement-reward-item-preview" aria-hidden="true">{first.item_icon || "🎁"}</div>
      <div className="achievement-reward-copy">
        <span className="eyebrow">NEW REWARD UNLOCKED</span>
        <strong>{rewards.length === 1 ? first.item_name : `${rewards.length} new avatar rewards`}</strong>
        <p>{rewards.length === 1 ? `You completed ${first.achievement_name}. ${first.item_name} was added to your collection.` : rewards.map((reward) => reward.item_name).join(", ") + " were added to your collection."}</p>
        <div className="achievement-reward-meta">{Number(xpEarned) > 0 && <span><Sparkles size={13} /> +{Number(xpEarned)} XP</span>}<span>{rewards.length} {rewards.length === 1 ? "achievement" : "achievements"} completed</span></div>
        {error && <small className="achievement-reward-error">{error}</small>}
        <div className="achievement-reward-actions">
          {equippedId ? <span className="achievement-equipped"><Check size={14} /> Equipped!</span> : <button type="button" onClick={equipNow} disabled={equipping || !first?.item_slot}>{equipping ? "Equipping…" : "Equip now"}</button>}
          <Link to="/profile?edit=1#dog-avatar" onClick={onDismiss}>Customize your dog</Link>
          <button type="button" className="achievement-later" onClick={onDismiss}>Later</button>
        </div>
      </div>
    </section>
  );
}
