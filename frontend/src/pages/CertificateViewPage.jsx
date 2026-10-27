import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Award,
  BadgeCheck,
  CheckCircle2,
  Printer,
  ShieldCheck,
} from "lucide-react";
import { API_BASE } from "../lib/demoState.js";
import { apiFetch } from "../lib/apiClient.js";
import { EmptyState, PageShell } from "../components/common.jsx";

function formatIssuedDate(value) {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}

export default function CertificateViewPage() {
  const { publicId = "" } = useParams();
  const [certificate, setCertificate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [unauthenticated, setUnauthenticated] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setCertificate(null);
    setLoading(true);
    setError("");
    setUnauthenticated(false);

    async function loadCertificate() {
      try {
        const response = await apiFetch(
          `${API_BASE}/api/me/certificates/${encodeURIComponent(publicId)}`,
          { credentials: "include", signal: controller.signal },
        );
        const payload = await response.json().catch(() => ({}));
        if (response.status === 401) {
          setUnauthenticated(true);
          throw new Error("Sign in with the account that earned this certificate.");
        }
        if (!response.ok) {
          const detail = payload.detail;
          throw new Error(
            typeof detail === "string"
              ? detail
              : detail?.message || "This certificate could not be loaded.",
          );
        }
        if (payload.valid !== true || payload.public_id !== publicId) {
          throw new Error("The server did not confirm this certificate.");
        }
        setCertificate(payload);
      } catch (requestError) {
        if (requestError.name !== "AbortError") {
          setError(requestError.message || "This certificate could not be loaded.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    if (publicId) void loadCertificate();
    else {
      setError("A certificate ID is required to view a credential.");
      setLoading(false);
    }
    return () => controller.abort();
  }, [publicId]);

  if (loading) {
    return (
      <PageShell className="narrow-page certificate-view-page">
        <div className="panel collection-state" role="status">
          Loading your certificate…
        </div>
      </PageShell>
    );
  }

  if (error || !certificate) {
    return (
      <PageShell className="narrow-page certificate-view-page">
        <EmptyState
          icon={ShieldCheck}
          title={unauthenticated ? "Sign in to view your certificate" : "Certificate unavailable"}
          detail={error || "This certificate is not available for the signed-in account."}
          action={
            unauthenticated ? (
              <Link
                to={`/login?next=${encodeURIComponent(`/certificates/view/${publicId}`)}`}
                className="button button-primary"
              >
                Sign in to continue
              </Link>
            ) : (
              <Link to="/certificates" className="button button-secondary">
                <ArrowLeft size={15} /> Back to certificates
              </Link>
            )
          }
        />
      </PageShell>
    );
  }

  return (
    <PageShell className="certificate-view-page">
      <div className="certificate-view-toolbar">
        <Link to="/certificates" className="text-link certificate-view-back">
          <ArrowLeft size={15} /> Back to certificates
        </Link>
        <button
          className="button button-secondary certificate-print-action"
          type="button"
          onClick={() => window.print()}
        >
          <Printer size={16} /> Print / Save as PDF
        </button>
      </div>

      <article className="certificate-document" aria-labelledby="certificate-title">
        <div className="certificate-document-topline">
          <span className="certificate-document-mark"><Award size={27} /></span>
          <span>CODELEAF · VERIFIED LEARNING</span>
          <span className="certificate-document-badge"><BadgeCheck size={15} /> OFFICIAL CREDENTIAL</span>
        </div>

        <div className="certificate-document-content">
          <p className="certificate-document-eyebrow">CERTIFICATE OF ACHIEVEMENT</p>
          <h1 id="certificate-title">Certificate of Completion</h1>
          <p className="certificate-document-intro">This certificate is proudly presented to</p>
          <h2 className="certificate-recipient">{certificate.recipient_name || "CodeLeaf learner"}</h2>
          <div className="certificate-document-rule" />
          <p className="certificate-document-description">
            for completing the published learning requirements and passing the
            required theoretical and practical certification assessments for
          </p>
          <h2 className="certificate-course-title">{certificate.course_title || certificate.course_slug}</h2>
          <p className="certificate-document-confirmation">
            <CheckCircle2 size={16} /> Issued after verification by the CodeLeaf certification service
          </p>
        </div>

        <div className="certificate-document-footer">
          <div>
            <span>DATE ISSUED</span>
            <strong>{formatIssuedDate(certificate.issued_at)}</strong>
          </div>
          <div className="certificate-document-id">
            <span>CREDENTIAL ID</span>
            <strong>{certificate.public_id}</strong>
          </div>
          <div className="certificate-document-seal" aria-label="Verified credential">
            <ShieldCheck size={25} />
            <span>VERIFIED</span>
          </div>
        </div>
      </article>

      <div className="certificate-view-verification">
        <ShieldCheck size={17} />
        <p>
          This credential is linked to your account. Its current validity can
          be checked using the public verification record.
        </p>
        <a
          href={`${API_BASE}/api/certificates/verify/${encodeURIComponent(certificate.public_id)}`}
          target="_blank"
          rel="noreferrer noopener"
        >
          Verify credential
        </a>
      </div>
    </PageShell>
  );
}
