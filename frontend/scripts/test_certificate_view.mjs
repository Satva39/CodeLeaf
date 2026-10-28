import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const app = read("../src/App.jsx");
const certificates = read("../src/pages/CertificatesPage.jsx");
const view = read("../src/pages/CertificateViewPage.jsx");
const practical = read("../src/pages/PracticalExamPage.jsx");
const exam = read("../src/pages/ExamPage.jsx");
const backend = read("../../backend/app/main.py");
const backendTest = read("../../backend/scripts/test_phase2_exam_api.py");
const styles = read("../src/styles/pages.css");

assert.match(app, /import CertificateViewPage from "\.\/pages\/CertificateViewPage\.jsx"/);
assert.match(app, /path="\/certificates\/view\/:publicId" element=\{<CertificateViewPage \/>\}/);
assert.match(certificates, /View certificate/);
assert.match(certificates, /\/certificates\/view\/\$\{encodeURIComponent\(certificate\.public_id\)\}/);
assert.match(view, /\/api\/me\/certificates\/\$\{encodeURIComponent\(publicId\)\}/);
assert.match(view, /Print \/ Save as PDF/);
assert.match(view, /Download certificate/);
assert.match(view, /\/api\/me\/certificates\/\$\{encodeURIComponent\(certificate\.public_id\)\}\/download/);
assert.match(view, /URL\.createObjectURL/);
assert.match(view, /recipient_name/);
assert.match(view, /course_title/);
assert.match(view, /public_id/);
assert.match(view, /window\.print\(\)/);
assert.match(practical, /result\.certificate\?\.public_id/);
assert.match(practical, /View certificate/);
assert.match(exam, /result\.certificate\?\.public_id/);
assert.match(backend, /@app\.get\("\/api\/me\/certificates\/\{public_id\}"\)/);
assert.match(backend, /Certificate\.user_id == user\.id/);
assert.match(backend, /Certificate\.revoked_at\.is_\(None\)/);
assert.match(backendTest, /certificate detail endpoint returns printable details to its owner/);
assert.match(backendTest, /certificate detail endpoint denies another learner access/);
assert.match(styles, /\.certificate-document/);
assert.match(styles, /@media print/);


assert.match(certificates, /const issuedCertificate = certificates\.find/);
assert.match(certificates, /to=\{`\/certificates\/view\/\$\{encodeURIComponent\(issuedCertificate\.public_id\)\}`\}/);
assert.match(certificates, /!certificateIssued && lessonsIncomplete/);
assert.match(certificates, /!certificateIssued && exercisesIncomplete/);
assert.match(backend, /prefer the linked reference file over legacy placeholders/);
assert.match(backend, /solution_doc\.get\("reference_code"\) or solution_doc\.get\("example_code"\)/);

console.log("Certificate viewing contract checks passed.");
