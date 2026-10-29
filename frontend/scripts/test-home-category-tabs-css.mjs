import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const cssPath = resolve(process.cwd(), 'src/styles/home.css');
const css = readFileSync(cssPath, 'utf8');
const startMarker = '/* CODELEAF_CATEGORY_TABS_POLISH_START */';
const endMarker = '/* CODELEAF_CATEGORY_TABS_POLISH_END */';
const start = css.indexOf(startMarker);
const end = css.indexOf(endMarker, start + startMarker.length);
assert.notEqual(start, -1, 'category chip CSS patch is present');
assert.ok(end > start, 'category chip CSS patch has a closing marker');
const block = css.slice(start, end);
for (const token of [
  'border-radius: 999px',
  'min-height: 38px',
  'text-overflow: ellipsis',
  'flex-wrap: nowrap',
  'overflow-x: auto',
  '.category-tabs button:hover',
  '.category-tabs button:focus-visible',
  '.category-tabs button.active',
  '@media (prefers-reduced-motion: reduce)',
]) {
  assert.ok(block.includes(token), `expected category CSS to include ${token}`);
}
console.log('Home category filter CSS checks passed.');
