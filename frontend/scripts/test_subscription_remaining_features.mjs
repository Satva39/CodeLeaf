import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';

const read = (path) => readFileSync(new URL(path, import.meta.url), 'utf8');
const app = read('../src/App.jsx');
const plans = read('../src/pages/PlansPage.jsx');
const planData = read('../src/data.js');
const playground = read('../src/pages/PlaygroundPage.jsx');
const projectGuide = read('../src/pages/ProjectGuidePage.jsx');
const mockExam = read('../src/pages/MockExamPage.jsx');
const support = read('../src/pages/SupportPage.jsx');
const leaderboard = read('../src/pages/LeaderboardPage.jsx');
const styles = read('../src/styles/pages.css');

assert.match(app, /path="\/mock-exam\/:examSlug" element={<MockExamPage \/>}/, 'timed mock assessment route is registered');
assert.match(app, /path="\/support" element={<SupportPage \/>}/, 'support request route is registered');
assert.match(plans, /saved_snippets/, 'pricing page compares saved snippet allowances');
assert.match(plans, /leaderboards/, 'pricing comparison includes the Pro leaderboard entitlement');
assert.match(planData, /Weekly and all-time leaderboards/, 'Pro plan card advertises the gated leaderboard');
assert.match(playground, /api\/me\/snippets/, 'playground uses account-backed snippet APIs');
assert.match(playground, /Save new snippet/, 'playground exposes snippet save action');
assert.match(projectGuide, /api\/me\/project-milestones/, 'project checklist state is loaded from the backend');
assert.match(projectGuide, /Saved to your account/, 'project checklist communicates persistent state');
assert.match(mockExam, /\/mock-exam\/start/, 'mock assessment starts through the backend');
assert.match(mockExam, /\/api\/me\/mock-exams\//, 'mock assessment submits through the backend');
assert.match(mockExam, /server enforces the deadline/i, 'mock assessment communicates server-side timing');
assert.match(mockExam, /does not award XP/i, 'mock assessment does not promise XP or certificate rewards');
assert.match(support, /api\/me\/support-requests/, 'support requests are persisted with the backend');
assert.match(support, /Queue priority is derived from your verified account plan/i, 'support UI explains plan-derived triage');
assert.match(leaderboard, /Leaderboards are included with Pro and above/, 'leaderboard has a useful locked-plan state');
assert.match(leaderboard, /\/plans/, 'locked leaderboard links to plans');
assert.match(styles, /\.exam-start-card/, 'mock assessment has dedicated styling');
assert.match(styles, /\.support-page/, 'support has dedicated styling');
assert.match(styles, /\.project-milestone-progress-check/, 'project checklist has dedicated styling');

console.log('Subscription remaining-features UI contract checks passed.');

const portfolio = read("../src/pages/PortfolioPage.jsx");
const uploadApi = readFileSync(new URL("../../backend/app/phase5_routes.py", import.meta.url), "utf8");
assert.match(portfolio, /upload-session/);
assert.match(portfolio, /application\/octet-stream/);
assert.match(portfolio, /uploadProgress/);
assert.match(uploadApi, /PROJECT_ZIP_UPLOAD_CHUNK_BYTES = 4 \* 1024 \* 1024/);
assert.match(uploadApi, /archive_upload_complete/);
assert.match(uploadApi, /validate_project_zip_file\(archive_file\)/);
console.log("PASS portfolio ZIP uploads use bounded binary chunks and backend final validation");
