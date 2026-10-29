import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const home = readFileSync(resolve(process.cwd(), 'src/pages/HomePage.jsx'), 'utf8');
const css = readFileSync(resolve(process.cwd(), 'src/styles/home.css'), 'utf8');

assert.ok(home.includes('className="course-category-filter"'), 'compact category filter is rendered');
assert.ok(home.includes('value={category}'), 'the filter is controlled by the existing selected category state');
assert.ok(home.includes('setCategory(event.target.value)'), 'changing categories updates the existing filter state');
assert.ok(home.includes('<option value="All">All categories</option>'), 'all categories can be selected');
assert.ok(home.includes('categories.slice(1).map'), 'all remaining course categories are available in the select');
assert.ok(home.includes('{courses.length}'), 'the matching course count is displayed');
assert.ok(home.includes('onClick={() => setCategory("All")}'), 'a selected category can be cleared');
assert.ok(!home.includes('className="category-tabs"'), 'the wrapping category button list has been removed');

const startMarker = '/* CODELEAF_CATEGORY_FILTER_REDESIGN_START */';
const endMarker = '/* CODELEAF_CATEGORY_FILTER_REDESIGN_END */';
const start = css.indexOf(startMarker);
const end = css.indexOf(endMarker, start + startMarker.length);
assert.notEqual(start, -1, 'category filter CSS patch is present');
assert.ok(end > start, 'category filter CSS patch has a closing marker');
const block = css.slice(start, end);
for (const token of [
  '.course-category-filter {',
  '.course-category-filter__select select {',
  'appearance: none',
  '.course-category-filter__result',
  '.course-category-filter__clear:hover',
  '.course-category-filter__clear:focus-visible',
  '@media (max-width: 640px)',
  '@media (prefers-reduced-motion: reduce)',
]) {
  assert.ok(block.includes(token), `expected filter CSS to include ${token}`);
}
console.log('Home category filter UI/CSS checks passed.');
