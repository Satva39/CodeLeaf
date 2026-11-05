# CodeLeaf Playground execution support

This update adds a real execution/processing path for previously unsupported Playground file types and expands language-to-runtime resolution. It does not claim every file format is a standalone program.

## How each category runs

| Category | CodeLeaf behavior | What the user sees |
|---|---|---|
| XML | Secure parse, validation, structure summary, pretty-print, and a bounded XPath selection | Validation result, root, node/attribute counts, matched elements, formatted XML |
| JSON | Parse, reject non-standard constants, pretty-print | Validation and formatted JSON |
| YAML | Safe YAML parse and pretty-print; basic CloudFormation and GitHub Actions structure checks | Validation and document summary |
| CSV | Parse rows, detect delimiter, check row consistency, preview rows | Row/column information and a table preview |
| TOML | Parse with Python `tomllib` and pretty-print | Validation and parsed TOML data |
| Dockerfile | Static instruction/order checks only | Lint findings; **does not build images or run Docker instructions** |
| GitHub Actions / CloudFormation YAML | Safe YAML parse plus basic structural checks | Configuration validation; **does not run workflows or deploy infrastructure** |
| Markdown / Git notes / plain text | Safe content inspection and summary | Content output; not a general Markdown application runtime |
| Redis command file | Request-local in-memory educational simulator for a limited command set | Actual command results; state is discarded after each request |
| HTML / CSS / JavaScript / React | Existing isolated browser preview | Rendered preview |
| Sass / SCSS | Dart Sass browser compiler in a script-only sandboxed iframe | Compiled CSS and preview |
| AngularJS 1.x | Browser preview in a script-only sandboxed iframe | Interactive preview |
| Compiled/interpreted languages | OnlineCompiler first when a compatible runtime is advertised; otherwise CodeLeaf Runner, then existing JDoodle fallback according to the existing routing policy | Actual provider and execution result |

**XML is data/markup, not an executable programming language.** Its Run action therefore validates and inspects the XML instead of fabricating program output. The XPath control accepts a deliberately limited subset of ElementTree paths.

The `excel` Playground language currently uses a CSV text file (`data.csv`). It is a CSV inspector, not an `.xlsx` workbook engine.

## Terminal language runtimes

The latest CodeLeaf-Runner `config/runtime-manifest.json` includes an `extended` profile containing 81 Piston language runtimes. This CodeLeaf update maps all 81 registry keys to language identities, filenames, starter files, and terminal execution mode.

**A mapping is not the same as an installed runtime.** The Runner must install the extended profile and advertise the runtime through its capabilities endpoint before CodeLeaf treats that language as available.

On the CodeLeaf-Runner host, follow the Runner repository's own setup and security documentation. The runtime installation flow is:

```bash
docker compose --profile runtime-admin up -d piston-admin
python scripts/provision_piston_runtimes.py --profile extended --apply
docker compose --profile runtime-admin stop piston-admin
```

Then verify the Runner's runtime/capabilities endpoint. Only after all required runtimes are installed and reported by the Runner should the CodeLeaf backend be configured with:

```env
RUNNER_SERVICE_URL=https://YOUR_RUNNER_API
RUNNER_SERVICE_TOKEN=YOUR_PRIVATE_RUNNER_TOKEN
```

Set these on the CodeLeaf backend (Render), never in Vercel/browser variables.

**Network safety:** do not expose Piston's administrative API or Redis directly to the public internet. Keep the Runner API authenticated, behind HTTPS, and apply per-run CPU, memory, wall-time, process, output and file limits. Follow the Runner repository's own deployment guidance; do not make the runtime-admin service publicly reachable.

## OnlineCompiler Python packages

The OnlineCompiler mapping now allows Python's documented preinstalled `numpy`, `scipy`, and `scikit-learn` packages to use the Python 3.14 runtime. `pandas` continues to use the dedicated pandas runtime. This depends on the provider's current published runtime/package availability and can change if its catalogue changes.

## Explicit limitations

These are not falsely advertised as completed execution:

- Modern Angular still needs a full Angular CLI workspace/build pipeline and dependency installation.
- Classic ASP needs a Windows IIS/ASP environment; the current Linux/Piston runner cannot execute it as a normal Linux job.
- PyTorch needs a PyTorch-enabled runtime image; it is not part of the documented OnlineCompiler Python package image used here.
- Dockerfile checks are static linting, not Docker builds.
- GitHub Actions and CloudFormation checks validate structure only; they do not run workflows or create cloud infrastructure.
- Redis support in this update is an isolated, ephemeral educational simulator, not a persistent Redis server.
- CSV support does not imply binary Excel `.xlsx` workbook support.

Do not report any of those as executed until a suitable environment/adapter is separately provided and tested.

## Configuration

The new `POST /api/playground/tools/run` endpoint is authenticated using CodeLeaf's existing `require_user` dependency. The endpoint applies source-size and format-specific limits and does not execute arbitrary submitted code on the FastAPI host.

The backend dependency `PyYAML>=6.0.2,<7.0` is required for safe YAML parsing. Install it through the existing backend requirements workflow when deploying.

## Tests

Run in `backend/`:

```bash
python scripts/test_playground_tools.py
```

Run in `frontend/`:

```bash
node scripts/test_playground_universal_runtimes.mjs
node scripts/test_language_workspace.mjs
node scripts/test_playground_output_modes.mjs
node scripts/test_runner_status_ui.mjs
npm run build
```

A successful local production build still needs the frontend dependencies installed. The implementation report records the checks actually run in the packaging environment.
