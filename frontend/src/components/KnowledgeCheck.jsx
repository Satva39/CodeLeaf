import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, RotateCcw, Send } from "lucide-react";
import { API_BASE } from "../lib/demoState.js";

async function readResponse(response) {
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(
      payload?.detail || `Knowledge check request failed (${response.status}).`,
    );
    error.status = response.status;
    throw error;
  }
  return payload;
}

/** A reusable knowledge-check UI that receives answer feedback only after submission. */
export function KnowledgeCheck({ courseSlug, lessonSlug }) {
  const [questionSet, setQuestionSet] = useState(null);
  const [answers, setAnswers] = useState({});
  const [feedback, setFeedback] = useState(null);
  const [status, setStatus] = useState("loading");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [loadAttempt, setLoadAttempt] = useState(0);
  const requestUrl = `${API_BASE}/api/courses/${encodeURIComponent(courseSlug)}/lessons/${encodeURIComponent(lessonSlug)}/knowledge-check`;

  useEffect(() => {
    const controller = new AbortController();
    setQuestionSet(null);
    setAnswers({});
    setFeedback(null);
    setError("");
    setStatus("loading");
    apiFetch(requestUrl, {
      headers: { Accept: "application/json" },
      credentials: "same-origin",
      signal: controller.signal,
    })
      .then(readResponse)
      .then((payload) => {
        if (
          !Array.isArray(payload?.questions) ||
          payload.questions.length === 0
        ) {
          setStatus("unavailable");
          return;
        }
        setQuestionSet(payload);
        setStatus("ready");
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        if (requestError.status === 404) {
          setStatus("unavailable");
          return;
        }
        setError(
          requestError.message || "Could not load this knowledge check.",
        );
        setStatus("error");
      });
    return () => controller.abort();
  }, [requestUrl, loadAttempt]);

  const resultById = useMemo(
    () =>
      new Map(
        (feedback?.results || []).map((result) => [result.question_id, result]),
      ),
    [feedback],
  );
  const answeredCount = Object.keys(answers).filter((id) =>
    Boolean(answers[id]),
  ).length;
  const total = questionSet?.questions?.length || 0;

  async function submitAnswers(event) {
    event.preventDefault();
    if (!questionSet || answeredCount !== total || submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const response = await apiFetch(`${requestUrl}/submit`, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ answers }),
      });
      const payload = await readResponse(response);
      setFeedback(payload);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Your answers could not be checked. Please retry.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (status === "unavailable") return null;
  if (status === "loading") {
    return (
      <section
        className="lesson-content-block knowledge-check-section"
        aria-busy="true"
      >
        <span className="eyebrow">QUICK REVIEW</span>
        <h2>Loading knowledge check…</h2>
        <p>Preparing the questions for this lesson.</p>
      </section>
    );
  }

  return (
    <section
      className="lesson-content-block knowledge-check-section"
      aria-labelledby="knowledge-check-title"
    >
      <div className="knowledge-check-heading">
        <div>
          <span className="eyebrow">QUICK REVIEW</span>
          <h2 id="knowledge-check-title">
            {questionSet?.title || "Knowledge check"}
          </h2>
          <p>
            Choose one answer for each question, then submit to see feedback.
          </p>
        </div>
        <span className="knowledge-check-count">{total} questions</span>
      </div>
      {status === "error" && (
        <div className="knowledge-check-error" role="alert">
          <AlertCircle size={17} />
          <span>{error}</span>
          <button
            type="button"
            className="button button-secondary button-small"
            onClick={() => setLoadAttempt((attempt) => attempt + 1)}
          >
            Retry
          </button>
        </div>
      )}
      {status === "ready" && questionSet && (
        <form onSubmit={submitAnswers}>
          <div className="knowledge-check-questions">
            {questionSet.questions.map((question, index) => {
              const result = resultById.get(question.id);
              return (
                <fieldset className="knowledge-question" key={question.id}>
                  <legend>
                    <span className="knowledge-question-number">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    {question.prompt}
                  </legend>
                  <div className="knowledge-question-options">
                    {question.options.map((option) => (
                      <label className="knowledge-option" key={option}>
                        <input
                          type="radio"
                          name={`knowledge-${question.id}`}
                          value={option}
                          checked={answers[question.id] === option}
                          disabled={Boolean(feedback)}
                          onChange={() =>
                            setAnswers((current) => ({
                              ...current,
                              [question.id]: option,
                            }))
                          }
                          required
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                  {result && (
                    <div
                      className={`knowledge-feedback ${result.is_correct ? "success" : "incorrect"}`}
                    >
                      <strong>
                        {result.is_correct ? (
                          <CheckCircle2 size={15} />
                        ) : (
                          <AlertCircle size={15} />
                        )}
                        {result.is_correct ? "Correct" : "Not quite"}
                      </strong>
                      {!result.is_correct && (
                        <p>
                          <b>Correct answer:</b> {result.correct_answer}
                        </p>
                      )}
                      <p>{result.explanation}</p>
                    </div>
                  )}
                </fieldset>
              );
            })}
          </div>
          {error && status !== "error" && (
            <p className="knowledge-check-inline-error" role="alert">
              {error}
            </p>
          )}
          {feedback ? (
            <div className="knowledge-check-result" aria-live="polite">
              <div>
                <strong>
                  {feedback.correct_count} / {feedback.answered_count} correct
                </strong>
                <span>{feedback.score_percent}% on this attempt</span>
              </div>
              <button
                className="button button-secondary"
                type="button"
                onClick={() => {
                  setAnswers({});
                  setFeedback(null);
                  setError("");
                }}
              >
                <RotateCcw size={14} /> Try again
              </button>
            </div>
          ) : (
            <div className="knowledge-check-submit-row">
              <span>
                {answeredCount} of {total} answered
              </span>
              <button
                className="button button-primary"
                type="submit"
                disabled={answeredCount !== total || submitting}
              >
                <Send size={14} /> {submitting ? "Checking…" : "Check answers"}
              </button>
            </div>
          )}
        </form>
      )}
    </section>
  );
}

export default KnowledgeCheck;
