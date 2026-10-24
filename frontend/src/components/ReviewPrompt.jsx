import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowRight, CheckCircle2, RefreshCw } from "lucide-react";
import { API_BASE } from "../lib/demoState.js";
import { apiFetch } from "../lib/apiClient.js";
import "../styles/phase3-review.css";

const RATINGS = [
  { value: "again", label: "Again", detail: "I need another pass" },
  { value: "hard", label: "Hard", detail: "I remembered with effort" },
  { value: "good", label: "Good", detail: "I recalled the main idea" },
  { value: "easy", label: "Easy", detail: "I could explain it clearly" },
];

export default function ReviewPrompt({ courseSlug, lessonSlug }) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const reviewId = searchParams.get("reviewId") || "";
  const itemType = searchParams.get("reviewType") || "";
  const itemSlug = searchParams.get("reviewItemSlug") || "";
  const [rating, setRating] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  if (!reviewId || !itemSlug || !["lesson", "exercise"].includes(itemType)) return null;

  async function submitRating(event) {
    event.preventDefault();
    if (!rating || busy || saved) return;
    setBusy(true);
    setError("");
    try {
      const response = await apiFetch(`${API_BASE}/api/me/reviews/${encodeURIComponent(reviewId)}/rate`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ rating, course_slug: courseSlug, lesson_slug: lessonSlug, item_type: itemType, item_slug: itemSlug }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Your review rating could not be saved.");
      setSaved(true);
    } catch (submitError) {
      setError(submitError.message || "Your review rating could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="phase3-review-prompt lesson-content-block" aria-labelledby="review-prompt-title">
      <div className="phase3-review-prompt-icon"><RefreshCw size={20} /></div>
      <div className="phase3-review-prompt-body">
        <span className="eyebrow">REVIEW SESSION</span>
        <h2 id="review-prompt-title">How well did you recall this?</h2>
        <p>Choose a rating after reviewing the material. This is a self-assessment used to schedule your next review; it does not award XP or mark content complete.</p>
        {saved ? (
          <div className="phase3-review-saved" role="status"><CheckCircle2 size={18} /><span>Your next review is scheduled. No XP was added for the self-rating.</span><button type="button" className="button button-primary button-small" onClick={() => navigate("/review?reviewed=1")}>Return to review queue <ArrowRight size={14} /></button></div>
        ) : (
          <form onSubmit={submitRating}>
            <div className="phase3-review-rating-grid" role="group" aria-label="How well you recalled the material">
              {RATINGS.map((option) => <button type="button" key={option.value} className={rating === option.value ? "phase3-review-rating is-selected" : "phase3-review-rating"} aria-pressed={rating === option.value} onClick={() => setRating(option.value)}><strong>{option.label}</strong><span>{option.detail}</span></button>)}
            </div>
            {error && <p className="phase3-review-error-inline" role="alert">{error}</p>}
            <button type="submit" className="button button-primary" disabled={!rating || busy}>{busy ? "Saving rating…" : "Save review rating"} <ArrowRight size={14} /></button>
          </form>
        )}
      </div>
    </section>
  );
}
