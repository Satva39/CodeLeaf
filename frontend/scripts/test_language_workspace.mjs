import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { COURSE_CATALOG } from '../src/data.js';
import {
  createBrowserDocument,
  defaultSourceForLanguage,
  getLanguageForFilename,
  resolveLanguage,
  safeWorkspaceFilename,
  starterFiles,
} from '../src/lib/languageWorkspace.js';

assert.equal(resolveLanguage('c').filename, 'main.c');
assert.equal(resolveLanguage('c++').filename, 'main.cpp');
assert.equal(resolveLanguage('python').filename, 'main.py');
assert.equal(resolveLanguage('java').filename, 'Main.java');
assert.equal(resolveLanguage('json-yaml').extension, 'yml');
assert.equal(resolveLanguage('redis').filename, 'commands.redis');
assert.equal(resolveLanguage('react').filename, 'App.jsx');
assert.equal(resolveLanguage('nodejs').filename, 'script.js');
assert.equal(getLanguageForFilename('main.c').key, 'c');
assert.equal(getLanguageForFilename('README.md').key, 'markdown');
assert.equal(getLanguageForFilename('values.yml').key, 'yaml');
assert.match(defaultSourceForLanguage('c'), /#include <stdio\.h>/);
assert.match(defaultSourceForLanguage('python'), /print\(/);

const cFiles = starterFiles({ courseSlug: 'c', codeLanguage: 'c', source: '#include <stdio.h>\nint main(void){return 0;}' });
assert.equal(cFiles.length, 1);
assert.equal(cFiles[0].name, 'main.c');
assert.match(cFiles[0].content, /stdio\.h/);
const cssFiles = starterFiles({ courseSlug: 'css', codeLanguage: 'css', source: 'h1 { color: red; }' });
assert.equal(cssFiles[0].name, 'styles.css');
assert.ok(cssFiles.some((file) => file.name === 'index.html'));
assert.match(createBrowserDocument(cssFiles), /Content-Security-Policy/);
assert.match(createBrowserDocument(cssFiles), /h1 \{ color: red; \}/);
for (const course of COURSE_CATALOG) {
  const language = resolveLanguage(course.slug);
  assert.notEqual(language.key, 'plain', `${course.slug} should have an explicit language profile`);
  assert.ok(defaultSourceForLanguage(language.key).trim(), `${course.slug} should have a starter example`);
}
assert.equal(safeWorkspaceFilename('notes.py'), true);
assert.equal(safeWorkspaceFilename('../secrets.env'), false);
assert.equal(safeWorkspaceFilename('folder/file.js'), false);

const lesson = await readFile(new URL('../src/pages/LessonPage.jsx', import.meta.url), 'utf8');
assert.match(lesson, /usableReferenceSources\(content\.sources\)/);
assert.match(lesson, /referenceSources\.length > 0/);
assert.match(lesson, /setExpandedGroup/);
assert.match(lesson, /Browse all exercises/);
const app = await readFile(new URL('../src/App.jsx', import.meta.url), 'utf8');
assert.match(app, /TryItPage/);
assert.match(app, /ExerciseDetailPage/);
const workspace = await readFile(new URL('../src/pages/PlaygroundPage.jsx', import.meta.url), 'utf8');
for (const phrase of ['Create file', 'Rename', 'Delete', 'Export project', 'Import project', 'Auto-saved in this browser']) assert.ok(workspace.includes(phrase), `missing workspace affordance: ${phrase}`);
console.log(`PASS language-specific file names and starter code cover all ${COURSE_CATALOG.length} current course slugs`);
console.log('PASS CSS lesson opens with styles.css selected and a restricted HTML preview');
console.log('PASS unsafe workspace file paths are rejected');
console.log('PASS try-it route, standalone exercise route, conditional references and accordion navigation are wired');
console.log('PASS multi-file create/rename/delete/import/export/autosave affordances are present');
