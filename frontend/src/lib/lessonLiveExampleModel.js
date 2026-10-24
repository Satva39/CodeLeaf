const normalized = (value) => String(value || "").toLowerCase().replaceAll("_", "-");

const matches = (text, pattern) => pattern.test(normalized(text));

/**
 * Chooses a safe, topic-aware browser demonstration for a published lesson.
 * "browser-*" modes render a sandboxed iframe. Other modes are deliberately
 * labeled simulations; they demonstrate a concept without pretending to run
 * Python, SQL, native binaries, shell commands, or other arbitrary code.
 */
export function getLessonLiveExampleMode({ courseSlug = "", lessonTitle = "", codeLanguage = "" } = {}) {
  const course = normalized(courseSlug);
  const title = normalized(lessonTitle);
  const language = normalized(codeLanguage);

  // Execute only browser-native source languages in the isolated frame.
  // Framework templates and preprocessors (JSX, TSX, SCSS, Sass, Vue SFCs)
  // require their own build/runtime, so they use an honest concept simulator.
  if (language === "html" || (course === "html" && ["", "text", "xml"].includes(language))) return "browser-html";
  if (language === "css" || (course === "css" && ["", "text"].includes(language))) return "browser-css";
  if (["javascript", "html"].includes(course) && ["", "text", "javascript", "js"].includes(language)) return "browser-javascript";
  const frameworkOrPreprocessorCourse = ["jquery", "angularjs", "react", "vue", "angular", "nextjs", "bootstrap", "tailwind-css", "sass"].includes(course);
  if (!frameworkOrPreprocessorCourse && ["javascript", "js"].includes(language) && /dom|browser|event|click|selector|document|element|frontend|form/.test(title)) return "browser-javascript";

  if (/(regular expression|regex|pattern matching|tokeni[sz]ation|lexical analysis)/.test(title) || ["regex", "regexp"].includes(course)) return "regex";
  if (/(data types?|type system|type inference|type narrowing|type guards?|union types?|intersection types?|generic types?|literal types?)/.test(title)) return "types";
  if (["json", "json-yaml", "yaml", "xml", "xquery", "xpath", "xslt"].includes(course) || ["json", "yaml", "xml", "xquery", "xpath", "xslt", "django-template"].includes(language) || /(configuration file|serialization|deserialization|json schema|yaml syntax|xml document)/.test(title)) return "config";
  if (["sql", "sqlite", "mysql", "postgresql", "mongodb"].includes(course) || language === "sql" || /(database|sql query|select statement|joins?|transactions?|indexing|normalization|relational model|query plan)/.test(title)) return "database";
  if (["excel", "dax", "powerquery"].includes(course) || ["excel-formula", "dax", "powerquery-m", "vba"].includes(language) || /(spreadsheet|worksheet|cell reference|formula|pivot table|power query|dax measure)/.test(title)) return "spreadsheet";
  if (["git"].includes(course) || /github-actions/.test(course) || /(git |version control|commit history|branching|merge conflict|rebase|pull request|workflow run|ci\/cd)/.test(title)) return "git";
  if (["docker", "kubernetes"].includes(course) || /(container|docker image|docker compose|kubernetes|pods?|orchestration|deployment rollout)/.test(title)) return "containers";
  if (["redis"].includes(course) || /(cache|caching|redis|time.to.live|eviction policy)/.test(title)) return "cache";
  if (["cybersecurity", "web-application-security"].includes(course) || /(authentication|authorization|access control|sql injection|cross.site scripting|\bxss\b|\bcsrf\b|cors|security header|password hash|threat model|input validation|session management|token security|encryption|cryptography)/.test(title)) return "security";
  if (/(machine learning|model training|classification|regression|prediction|neural network|tensor|dataset|feature engineering|model evaluation|gradient descent|accuracy|precision and recall|clustering)/.test(title)) return "data";
  if (/(sort(ing)? algorithm|search(ing)? algorithm|binary search|linear search|algorithm|time complexity|space complexity|recursion|graph traversal|breadth.first|depth.first|dynamic programming)/.test(title)) return "algorithm";
  if (/(loop|iteration|iterating|for each|while statement|for statement|repeat until|iterator|generator)/.test(title)) return "loops";
  if (/(conditional|if statement|if\/else|if else|boolean|truthy|falsy|comparison operator|ternary|decision branch|branching logic|switch statement)/.test(title)) return "conditions";
  if (/(array|list|stack|queue|collection|dictionary|hash map|hash table|key.value|set data structure|tuple|sequence|vector|linked list|tree data structure|heap data structure)/.test(title)) return "collections";
  if (/(function|method|parameter|argument|return value|lambda|closure|callback|higher.order|pure function|decorator)/.test(title)) return "functions";
  if (["fastapi", "flask", "django", "expressjs", "rest-api-development", "nodejs"].includes(course) || /(api endpoint|http request|http response|rest api|request lifecycle|routing and middleware|status code|client.server|webhook)/.test(title)) return "api";
  if (["bash", "linux", "powershell"].includes(course) || ["bash", "shell", "powershell", "dockerfile"].includes(language) || /(file system|file permissions|shell command|command line|process management|environment variable|directory navigation|standard input|standard output|pipes and redirects|cron job)/.test(title)) return "filesystem";
  if (/(class and object|object.oriented|inheritance|polymorphism|encapsulation|constructor|interface|abstract class|object model)/.test(title)) return "oop";
  if (/(exception|error handling|try\/catch|try catch|debugging|unit test|testing strategy|assertion|logging|retry logic|failure handling|fault tolerance)/.test(title)) return "error-flow";
  if (/(dns|tcp|udp|ip address|network packet|routing protocol|ssh|tls handshake|http protocol|socket|network layer|ports and protocols)/.test(title)) return "network";
  if (/(state machine|state transition|event loop|async|asynchronous|concurrency|parallelism|thread|process synchronization|promise|coroutine|finite state)/.test(title)) return "state";
  if (/(math|arithmetic|numerical method|linear algebra|matrix|statistics|probability|mean and median|standard deviation|calculus|optimization)/.test(title)) return "math";
  if (["ai", "generative-ai", "data-science", "scikit-learn", "pytorch", "numpy", "pandas", "scipy"].includes(course)) return "data";
  if (["react", "vue", "angular", "angularjs", "nextjs", "bootstrap", "tailwind-css", "sass"].includes(course) || ["jsx", "tsx", "vue"].includes(language) || /(component|responsive layout|user interface|design system|styling system|reactivity|state management|props and events|template binding)/.test(title)) return "ui";
  if (course === "typescript") return "types";
  if (course === "dsa") return "algorithm";
  if (course === "solidity") return "state";
  if (["python", "java", "c", "cpp", "csharp", "go", "ruby", "rust", "swift", "kotlin", "dart", "lua", "php", "asp"].includes(course)) return "variables";

  // Every lesson receives a small, explicitly illustrative experiment rather
  // than falsely claiming that a non-browser language's code was executed.
  return "concept";
}

export function buildSandboxDocument(mode, sourceCode = "", lessonTitle = "") {
  const csp = `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data: blob:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; font-src data:; media-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'">`;
  const baseStyle = `
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 22px; color: #172033; background: #f5f8fc; }
    .demo-shell { max-width: 900px; margin: 0 auto; }
    .demo-kicker { color: #087f70; font-size: 11px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
    h1 { margin: 8px 0; font-size: clamp(20px, 4vw, 30px); line-height: 1.2; }
    p { line-height: 1.55; }
    .demo-card { border: 1px solid #dbe4ef; border-radius: 14px; background: white; padding: 18px; margin: 14px 0; box-shadow: 0 7px 24px #1732530d; }
    .demo-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .demo-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(130px,1fr)); gap: 10px; }
    .demo-tile { background: #e9f5f2; border: 1px solid #c7e8df; border-radius: 10px; padding: 12px; }
    .demo-button, button { border: 0; border-radius: 9px; padding: 10px 14px; background: #087f70; color: #fff; font: inherit; font-weight: 700; cursor: pointer; }
    input, select { border: 1px solid #c8d4e2; border-radius: 8px; padding: 9px; font: inherit; max-width: 100%; }
    small { color: #607087; }
  `;
  const code = String(sourceCode || "");
  if (mode === "browser-html") {
    const isDocument = /<html\b/i.test(code);
    if (!isDocument) return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${csp}<style>${baseStyle}</style></head><body>${code || '<main class="demo-shell"><span class="demo-kicker">Live HTML</span><h1>Hello, CodeLeaf!</h1><p>Edit the lesson example to see the rendered document.</p><button>Example button</button></main>'}</body></html>`;
    if (/<head\b[^>]*>/i.test(code)) return code.replace(/<head\b[^>]*>/i, (head) => `${head}<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${csp}<style>${baseStyle}</style>`);
    return code.replace(/<html\b[^>]*>/i, (html) => `${html}<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${csp}<style>${baseStyle}</style></head>`);
  }
  if (mode === "browser-css") {
    const liveCss = (code || ".demo-card { border-color: #0c9b86; }\nh1 { color: #087f70; }").replace(/<\/style/gi, "<\\/style");
    const transformExample = /transform|rotate|scale|skew/i.test(lessonTitle);
    const transformStyles = `.transform-stage{display:grid;place-items:center;min-height:190px;margin:18px 0;border:1px dashed #b9c9dc;border-radius:12px;background:linear-gradient(135deg,#eff5fb,#e6edf7)}.transform-target{display:grid;place-items:center;width:118px;height:118px;border:2px solid #8e1616;border-radius:7px;color:white;background:#e92323;font-weight:800;text-align:center;box-shadow:0 10px 24px #16253a28}`;
    const demoBody = transformExample
      ? `<main class="demo-shell"><span class="demo-kicker">Live CSS preview</span><h1>2D transform playground</h1><p>The lesson CSS is applied to the shape below. Watch how a transform changes its position, size, or angle without changing normal document flow.</p><div class="transform-stage"><div class="transform-target">Transform<br>this shape</div></div><small>Edit the CSS in the lesson editor to change the live result.</small></main>`
      : `<main class="demo-shell"><span class="demo-kicker">Live CSS preview</span><h1>Style this example</h1><p>Your lesson stylesheet is applied to these sample elements. Change the CSS in the lesson editor and this preview updates.</p><div class="demo-card"><h2>Learning card</h2><p>A paragraph to demonstrate type, color, spacing and layout rules.</p><button class="demo-button">Try me</button></div><div class="demo-grid"><div class="demo-tile">Element A</div><div class="demo-tile">Element B</div><div class="demo-tile">Element C</div></div><p><a href="#preview">A sample link</a></p></main>`;
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${csp}<style>${baseStyle}\n${transformStyles}\n${liveCss}</style></head><body>${demoBody}</body></html>`;
  }
  if (mode === "browser-javascript") {
    const safeCode = code.replace(/<\/script/gi, "<\\/script");
    const fallback = `const button = document.querySelector('#demo-button');\nbutton.addEventListener('click', () => {\n  document.querySelector('#demo-output').textContent = 'Button clicked!';\n  console.log('The live interaction ran.');\n});`;
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">${csp}<style>${baseStyle}#demo-output{min-height:24px;margin-top:12px;padding:10px;background:#f0f5fa;border-radius:8px;white-space:pre-wrap}</style></head><body><main class="demo-shell"><span class="demo-kicker">Live JavaScript preview</span><h1>Try the interaction</h1><div class="demo-card"><p id="demo-description">The lesson JavaScript runs in a restricted preview frame.</p><button id="demo-button" type="button">Run interaction</button><div id="demo-output" aria-live="polite">Output appears here.</div></div><div class="demo-grid"><div class="demo-tile demo-item">Sample item 1</div><div class="demo-tile demo-item">Sample item 2</div></div></main><script>const output = document.getElementById('demo-output'); output.textContent = ''; const write = (...args) => { output.textContent += (output.textContent ? '\n' : '') + args.map(x => typeof x === 'string' ? x : JSON.stringify(x)).join(' '); }; console.log = (...args) => write(...args); console.info = (...args) => write(...args); console.warn = (...args) => write('Warning:', ...args); console.error = (...args) => write('Error:', ...args); window.alert = (message) => write('Alert:', message); window.onerror = (_message, _source, _line, _column, error) => { write('Execution error:', error?.message || _message); }; try { ${safeCode || fallback} } catch (error) { write('Execution error:', error.message); }</script></body></html>`;
  }
  return "";
}
