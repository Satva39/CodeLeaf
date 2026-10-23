import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const vite = readFileSync(new URL('../vite.config.js', import.meta.url), 'utf8');
const demoState = readFileSync(new URL('../src/lib/demoState.js', import.meta.url), 'utf8');
const envExample = readFileSync(new URL('../.env.example', import.meta.url), 'utf8');

assert.match(vite, /proxy\s*:/);
assert.match(vite, /['"]\/api['"]\s*:/);
assert.match(vite, /target:\s*['"]http:\/\/127\.0\.0\.1:8000['"]/);
assert.match(demoState, /import\.meta\.env\.DEV\s*\?\s*['"]{2}/);
assert.match(envExample, /^VITE_API_BASE_URL=\s*$/m, 'frontend/.env.example must leave VITE_API_BASE_URL blank for local Vite proxying');
console.log('PASS local frontend sends same-origin /api requests through the Vite proxy');
console.log('PASS local API requests avoid browser cross-origin/CORS hostname mismatches');
