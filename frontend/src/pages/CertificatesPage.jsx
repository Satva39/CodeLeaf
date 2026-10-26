import { apiFetch } from "../lib/apiClient.js";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowDownRight,
  Award,
  ArrowRight,
  CheckCircle2,
  Clock3,
  Search,
  ShieldCheck,
} from "lucide-react";
import { Link } from "react-router-dom";
import { COURSE_CATALOG, COURSE_CATEGORIES } from "../data.js";
import { API_BASE } from "../lib/demoState.js";
import { PageShell, CourseIcon, EmptyState } from "../components/common.jsx";

export default function CertificatesPage() {
  const [filter, setFilter] = useState("All topics");
  const [query, setQuery] = useState("");
  const [certificates, setCertificates] = useState([]);
  const [eligibility, setEligibility] = useState(null);
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState(null);
  const [loadMessage, setLoadMessage] = useState("");
  const [examAvailability, setExamAvailability] = useState({});
  const [courseEligibility, setCourseEligibility] = useState({});
  const [courseEligibilityLoading, setCourseEligibilityLoading] = useState(false);
  const [examCatalogLoading, setExamCatalogLoading] = useState(true);
  const [examCatalogError, setExamCatalogError] = useState("");
  const examCategories = ["All topics", ...COURSE_CATEGORIES];
  const items = useMemo(
    () =>
      COURSE_CATALOG.filter(
        (course) =>
          (filter === "All topics" || course.category === filter) &&
          course.title.toLowerCase().includes(query.toLowerCase()),
      ),
    [filter, query],
  );

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setLoading(true);
      try {
        const response = await apiFetch(`${API_BASE}/api/me/certificates`, {
          credentials: "include",
          signal: controller.signal,
        });
        const payload = await response.json().catch(() => ({}));
        if (response.status === 401) {
          setSignedIn(false);
          setCertificates([]);
          setEligibility(null);
          setLoadMessage(
            "Sign in to view certificates issued to your account.",
          );
          return;
        }
        if (!response.ok)
          throw new Error(
            payload.detail || "Your certificates could not be loaded.",
          );
        setSignedIn(true);
        setCertificates(Array.isArray(payload.items) ? payload.items : []);
        const eligibilityResponse = await apiFetch(
          `${API_BASE}/api/me/certificate-eligibility/html`,
          { credentials: "include", signal: controller.signal },
        );
        const eligibilityPayload = await eligibilityResponse
          .json()
          .catch(() => ({}));
        if (eligibilityResponse.ok) setEligibility(eligibilityPayload);
        else if (eligibilityResponse.status !== 404)
          setLoadMessage(
            eligibilityPayload.detail ||
              "Certificate eligibility could not be checked.",
          );
      } catch (error) {
        if (error.name !== "AbortError")
          setLoadMessage(
            error.message || "Your certificates could not be loaded.",
          );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    load();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (signedIn !== true) {
      setCourseEligibility({});
      setCourseEligibilityLoading(false);
      return undefined;
    }
    const controller = new AbortController();
    async function loadCourseEligibility() {
      setCourseEligibilityLoading(true);
      try {
        const response = await apiFetch(`${API_BASE}/api/me/certificate-eligibility`, {
          credentials: "include",
          signal: controller.signal,
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || "Course eligibility could not be checked.");
        const next = {};
        for (const item of Array.isArray(payload.items) ? payload.items : []) {
          if (item && typeof item.course_slug === "string") next[item.course_slug] = item;
        }
        setCourseEligibility(next);
      } catch (error) {
        if (error.name !== "AbortError") setCourseEligibility({});
      } finally {
        if (!controller.signal.aborted) setCourseEligibilityLoading(false);
      }
    }
    loadCourseEligibility();
    return () => controller.abort();
  }, [signedIn]);

  useEffect(() => {
    const controller = new AbortController();
    async function loadExamAvailability() {
      setExamCatalogLoading(true);
      setExamCatalogError("");
      try {
        const response = await apiFetch(`${API_BASE}/api/exams/catalog`, {
          credentials: "include",
          signal: controller.signal,
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(
            payload.detail || "Exam availability could not be checked.",
          );
        }
        const next = {};
        for (const exam of Array.isArray(payload.items) ? payload.items : []) {
          if (exam && typeof exam.slug === "string") next[exam.slug] = exam;
        }
        setExamAvailability(next);
      } catch (error) {
        if (error.name !== "AbortError") {
          setExamAvailability({});
          setExamCatalogError(
            error.message || "Exam availability could not be checked.",
          );
        }
      } finally {
        if (!controller.signal.aborted) setExamCatalogLoading(false);
      }
    }
    loadExamAvailability();
    return () => controller.abort();
  }, []);

  return (
    <PageShell>
      <div className="certificate-hero panel">
        <div>
          <div className="eyebrow">SHOW WHAT YOU KNOW</div>
          <h1>Certificates</h1>
          <p>
            Only credentials issued by the backend appear as earned
            certificates. Exam availability and eligibility follow each course’s
            published content and verified completion rules.
          </p>
          <div className="hero-actions">
            <a href="#available-exams" className="button button-primary">
              Browse certification tracks <ArrowDownRight size={15} />
            </a>
            <span className="muted-inline">
              <ShieldCheck size={14} /> Verifiable learning credentials
            </span>
          </div>
        </div>
        <div className="certificate-art">
          <div className="certificate-paper">
            <div className="certificate-paper-mark">
              <Award size={26} />
            </div>
            <small>CODELEAF CREDENTIAL</small>
            <b>CodeLeaf</b>
            <span>Backend-verified milestone</span>
            <div className="certificate-paper-lines" />
          </div>
          <div className="certificate-seal">
            <Award size={23} />
          </div>
        </div>
      </div>

      {signedIn && eligibility && (
        <section
          className="panel certificate-eligibility-card"
          aria-live="polite"
        >
          <div>
            <span className="eyebrow">HTML CERTIFICATE STATUS</span>
            <h2>
              {String(eligibility.status || "pending").replaceAll("_", " ")}
            </h2>
            <p>{eligibility.message}</p>
            {eligibility.completed_lessons != null && (
              <small>
                Required lessons completed: {eligibility.completed_lessons} of{" "}
                {eligibility.total_lessons}
              </small>
            )}
          </div>
          <span
            className={`pill ${eligibility.status === "issued" ? "pill-mint" : "pill-neutral"}`}
          >
            {eligibility.status === "issued" ? "Issued" : "Not issued"}
          </span>
        </section>
      )}
      {loadMessage && (
        <p className="collection-checked-note" role="status">
          {loadMessage}
        </p>
      )}

      <div className="exam-layout">
        <div className="exam-main-col">
          <div className="panel exam-filters" id="available-exams">
            <div className="category-tabs">
              {examCategories.map((category) => (
                <button
                  key={category}
                  onClick={() => setFilter(category)}
                  className={filter === category ? "active" : ""}
                >
                  {category}
                </button>
              ))}
            </div>
            <div className="catalog-search compact-search">
              <Search size={16} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Filter certification tracks..."
                aria-label="Filter certification tracks"
              />
              <span>{items.length}</span>
            </div>
          </div>
          {examCatalogError && (
            <p className="collection-checked-note" role="status">
              Live exam availability could not be checked: {examCatalogError}
            </p>
          )}
          <div className="exam-list">
            {items.map((course) => {
              const exam = examAvailability[course.slug];
              const available = exam?.available === true;
              const learnerEligibility = courseEligibility[course.slug];
              const hasLearnerEligibility = signedIn === true
                && typeof learnerEligibility?.total_lessons === "number"
                && typeof learnerEligibility?.total_exercises === "number";
              const lessonsIncomplete = hasLearnerEligibility && learnerEligibility.lessons_complete === false;
              const exercisesIncomplete = hasLearnerEligibility && learnerEligibility.exercises_complete === false;
              const prerequisitesComplete = hasLearnerEligibility && learnerEligibility.prerequisites_complete === true;
              const practicalPending = hasLearnerEligibility && ["practical_exam_required", "practical_exam_not_passed"].includes(learnerEligibility.certificate_status);
              const canStartExam = available && !practicalPending && (signedIn !== true || (hasLearnerEligibility && prerequisitesComplete && learnerEligibility.start_exam_available === true));
              const htmlCertificateIssued =
                course.slug === "html" && eligibility?.status === "issued";
              const statusLabel = courseEligibilityLoading
                ? "Checking progress"
                : hasLearnerEligibility && !prerequisitesComplete
                  ? "Prerequisites incomplete"
                  : examCatalogLoading
                    ? "Checking publication"
                    : !exam
                      ? "Status unavailable"
                      : available
                        ? "Exam published"
                        : exam.status === "configuration_error"
                          ? "Needs attention"
                          : "Publication required";
              return (
                <div className="exam-card panel" key={course.slug}>
                  <CourseIcon course={course} size="md" />
                  <div className="exam-card-info">
                    <small>COURSE TRACK</small>
                    <h3>{course.title} certification</h3>
                    <p>
                      {examCatalogLoading
                        ? "Checking the published exam blueprint and question bank…"
                        : exam?.message ||
                          "Live exam availability has not been returned by the backend."}
                    </p>
                    <div className="exam-meta">
                      <span>
                        <Clock3 size={13} /> Server-scored exam
                      </span>
                      <span>
                        <ShieldCheck size={13} /> {statusLabel}
                      </span>
                    </div>
                  </div>
                  <div className="exam-card-actions">
                    {hasLearnerEligibility && lessonsIncomplete && (
                      <Link className="button button-secondary exam-card-action" to={`/learn/${encodeURIComponent(course.slug)}`}>
                        Complete all lessons <ArrowRight size={15} />
                      </Link>
                    )}
                    {hasLearnerEligibility && exercisesIncomplete && (
                      <Link className="button button-secondary exam-card-action" to={`/practice/${encodeURIComponent(course.slug)}`}>
                        Complete all exercises <ArrowRight size={15} />
                      </Link>
                    )}
                    {practicalPending && prerequisitesComplete && available && (
                      <Link className="button button-primary exam-card-action" to={`/practical/${encodeURIComponent(course.slug)}`}>
                        {learnerEligibility.certificate_status === "practical_exam_not_passed" ? "Retry practical exam" : "Take practical exam"} <ArrowRight size={15} />
                      </Link>
                    )}
                    {canStartExam && !htmlCertificateIssued && !lessonsIncomplete && !exercisesIncomplete ? (
                      <Link className="button button-primary exam-card-action" to={`/exam/${encodeURIComponent(course.slug)}`}>
                        Start exam <ArrowRight size={15} />
                      </Link>
                    ) : htmlCertificateIssued || learnerEligibility?.certificate_issued ? (
                      <span className="pill pill-mint">Issued</span>
                    ) : hasLearnerEligibility && prerequisitesComplete && !available ? (
                      <span className="pill pill-neutral">Exam unavailable</span>
                    ) : !lessonsIncomplete && !exercisesIncomplete && !canStartExam ? (
                      <span className="pill pill-neutral">
                        {courseEligibilityLoading || examCatalogLoading ? "Checking…" : exam?.status === "configuration_error" ? "Needs attention" : exam ? "Roadmap" : "Unavailable"}
                      </span>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <aside className="exam-side-col">
          <div className="panel earned-certs-card">
            <span className="earned-cert-icon">
              <Award size={19} />
            </span>
            <h3>Your certificates</h3>
            <strong className="earned-count">
              {loading ? "—" : certificates.length}
            </strong>
            <p>
              {signedIn
                ? "Backend-issued credentials linked to your account."
                : "Sign in to see backend-issued credentials."}
            </p>
            {certificates.length
              ? certificates.map((certificate) => (
                  <div key={certificate.public_id} className="earned-cert-row">
                    <CheckCircle2 size={14} />
                    <span>
                      <strong>
                        {certificate.course_title || certificate.course_slug}
                      </strong>
                      <small>
                        {certificate.public_id} ·{" "}
                        {certificate.issued_at
                          ? new Date(certificate.issued_at).toLocaleDateString()
                          : "date unavailable"}
                      </small>
                      <a
                        href={`${API_BASE}/api/certificates/verify/${encodeURIComponent(certificate.public_id)}`}
                        target="_blank"
                        rel="noreferrer noopener"
                      >
                        Verify credential
                      </a>
                    </span>
                  </div>
                ))
              : !loading && (
                  <small>
                    {signedIn
                      ? "No verified certificates have been issued yet."
                      : "No certificate records are shown while signed out."}
                  </small>
                )}
          </div>
          <div className="panel exam-info-card">
            <ShieldCheck size={20} />
            <h3>How it works</h3>
            <ol>
              <li>Study the published curriculum.</li>
              <li>Complete all required published lessons and exercises.</li>
              <li>Pass the 80-question MCQ exam and mandatory practical assessment.</li>
              <li>Certificates appear here only after the backend verifies and issues them.</li>
            </ol>
          </div>
        </aside>
      </div>
    </PageShell>
  );
}
