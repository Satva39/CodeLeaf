"""Generate course-specific, deterministically text-graded practical assessments.

Run from backend/: python scripts/generate_practical_assessments.py
The existing practical API accepts structured text/artifact submissions and
never executes submitted code inside the API process. Each task therefore uses
its supported deterministic content grader; runtime execution is not claimed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "content" / "courses"

# Each entry defines a course-specific applied implementation task, a defect
# scenario, and expected constructs for the implementation, regression tests,
# and production-safety review. Values are intentionally specific to each track.
COURSES = {
    "angular": {
        "topic": "build an order editor with a reactive form, required validation, and safe teardown of asynchronous subscriptions",
        "starter": "@Component({ selector: 'app-order-editor', template: '...' })\nexport class OrderEditorComponent {\n  // Add a FormGroup, validators, submit handler, and teardown.\n}",
        "impl": ["formgroup", "validators.required", "ngoninit", "ngondestroy"],
        "bug": "a component leaves an RxJS subscription active after the route changes, so stale results update a destroyed view",
        "fix": ["takeuntildestroyed", "subscribe", "ngondestroy"],
        "tests": ["describe", "it(", "expect(", "invalid form", "valid form"],
        "ops": ["role", "server-side validation", "unsubscribe", "error handling"],
    },
    "angularjs": {
        "topic": "maintain a legacy AngularJS customer search controller with cancellation-aware requests and safe DOM rendering",
        "starter": "angular.module('legacyApp').controller('CustomerSearchCtrl', function ($scope, $http) {\n  // Add query handling and request state.\n});",
        "impl": ["angular.module", "$http", "$scope", "loading"],
        "bug": "a legacy search inserts untrusted customer text as HTML and old responses overwrite newer results",
        "fix": [".text(", "cancel", "request", "error"],
        "tests": ["describe(", "it(", "$httpbackend", "expect", "empty query"],
        "ops": ["sanitize", "authorization", "dependency", "error handling"],
    },
    "asp": {
        "topic": "implement a Classic ASP order lookup page with validated request parameters and a parameterized ADO query",
        "starter": "<%\n' Read an order ID, validate it, run a parameterized query, and encode output.\n%>",
        "impl": ["request.querystring", "adodb.command", "parameters.append", "server.htmlencode"],
        "bug": "an order lookup concatenates Request.QueryString directly into SQL and writes database text into HTML",
        "fix": ["adodb.command", "parameters.append", "server.htmlencode"],
        "tests": ["empty id", "invalid id", "not found", "expected", "assert"],
        "ops": ["least privilege", "parameterized", "server.htmlencode", "error log"],
    },
    "aws": {
        "topic": "design a least-privilege S3 event workflow that invokes a Lambda processor and records failures safely",
        "starter": "Resources:\n  ProcessorRole:\n    Type: AWS::IAM::Role\n  ProcessorFunction:\n    Type: AWS::Lambda::Function\n",
        "impl": ["aws::iam::role", "s3", "lambda", "actions:", "resources:"],
        "bug": "a Lambda role grants wildcard access to every S3 bucket and retries a poison event forever",
        "fix": ["least privilege", "specific arn", "dead-letter", "retry"],
        "tests": ["event fixture", "expected", "failure case", "idempotency", "assert"],
        "ops": ["cloudwatch", "alarm", "least privilege", "dead-letter queue"],
    },
    "bash": {
        "topic": "write a robust CLI log summarizer that accepts a file argument, counts error lines, and returns meaningful exit codes",
        "starter": "#!/usr/bin/env bash\nset -euo pipefail\nlog_file=\"${1:-}\"\n# Validate the argument and summarize ERROR lines.\n",
        "impl": ["set -euo pipefail", "grep", "printf", "exit"],
        "bug": "a script breaks on filenames with spaces and hides the failure of an upstream command in a pipeline",
        "fix": ["\"$log_file\"", "pipefail", "--", "status"],
        "tests": ["shellcheck", "empty file", "missing file", "exit status", "assert"],
        "ops": ["mktemp", "trap", "quote", "least privilege"],
    },
    "bootstrap": {
        "topic": "create an accessible responsive account dialog using Bootstrap components and validation states",
        "starter": "<button class=\"btn btn-primary\" data-bs-toggle=\"modal\" data-bs-target=\"#accountModal\">Open</button>\n<div class=\"modal fade\" id=\"accountModal\">...</div>",
        "impl": ["modal-dialog", "modal-content", "aria-labelledby", "form-control", "is-invalid"],
        "bug": "a modal has no accessible name, form errors are color-only, and a small-screen layout overflows",
        "fix": ["aria-labelledby", "invalid-feedback", "is-invalid", "container-fluid"],
        "tests": ["keyboard", "focus", "aria", "required", "validation"],
        "ops": ["responsive", "focus trap", "contrast", "semantic html"],
    },
    "c": {
        "topic": "implement a command-line CSV record counter with explicit allocation checks, input validation, and cleanup",
        "starter": "#include <stdio.h>\n#include <stdlib.h>\nint main(int argc, char **argv) {\n    /* Validate argv, read records, release resources. */\n    return 0;\n}",
        "impl": ["int main", "argc", "fopen", "fclose", "free"],
        "bug": "a parser assumes a successful allocation and reads beyond a buffer when a long record arrives",
        "fix": ["sizeof", "realloc", "null", "buffer length"],
        "tests": ["assert", "empty input", "long record", "invalid argument"],
        "ops": ["address sanitizer", "bounds check", "error path", "free"],
    },
    "cpp": {
        "topic": "build a typed inventory summary using STL containers, RAII, and explicit handling of missing products",
        "starter": "#include <string>\n#include <vector>\nstruct Item { std::string sku; int quantity; };\n// Implement aggregation without manual owning pointers.\n",
        "impl": ["std::vector", "std::unordered_map", "const", "std::string"],
        "bug": "an inventory loop uses an invalidated iterator and fails when the SKU has no matching entry",
        "fix": ["find(", "end()", "iterator", "const auto"],
        "tests": ["static_assert", "assert(", "empty vector", "missing sku"],
        "ops": ["raii", "std::optional", "exception", "sanitizer"],
    },
    "csharp": {
        "topic": "implement an asynchronous customer lookup service with cancellation and a typed result",
        "starter": "public sealed class CustomerService {\n    // Add an async lookup using CancellationToken.\n}",
        "impl": ["async task", "cancellationtoken", "await", "try", "catch"],
        "bug": "an API lookup blocks synchronously, swallows cancellation, and returns null for both missing and failed requests",
        "fix": ["cancellationtoken", "throwifcancellationrequested", "result", "exception"],
        "tests": ["fact", "assert.", "cancellationtoken", "not found"],
        "ops": ["nullable", "logging", "timeout", "dependency injection"],
    },
    "css": {
        "topic": "create a responsive dashboard card grid with readable focus states and reduced-motion support",
        "starter": ".dashboard-grid {\n  /* Add responsive layout rules. */\n}\n.dashboard-card {\n  /* Add card styling. */\n}\n",
        "impl": ["display: grid", "minmax(", "gap:", "focus-visible", "prefers-reduced-motion"],
        "bug": "fixed-width cards overflow at 320px and keyboard focus is removed from interactive links",
        "fix": ["minmax(", "max-width: 100%", "focus-visible", "outline"],
        "tests": ["320px", "768px", "1440px", "keyboard", "reduced motion"],
        "ops": ["contrast", "responsive", "focus-visible", "prefers-reduced-motion"],
    },
    "cybersecurity": {
        "topic": "triage a suspicious login incident using evidence preservation, scope assessment, and controlled containment",
        "starter": "Incident ID:\nIndicators:\nAffected accounts:\nEvidence preserved:\nContainment and recovery:\n",
        "impl": ["timestamp", "source ip", "affected account", "evidence hash", "chain of custody"],
        "bug": "an analyst deletes raw logs before preserving them and disables every user account without checking scope",
        "fix": ["preserve logs", "chain of custody", "scope", "least disruptive containment"],
        "tests": ["timeline", "indicator", "false positive", "verify", "recovery"],
        "ops": ["least privilege", "rotate credentials", "monitor", "incident review"],
    },
    "dart": {
        "topic": "create a null-safe Dart model and asynchronous repository for paginated product data",
        "starter": "class Product {\n  // Add typed fields and a factory constructor.\n}\n\nFuture<List<Product>> loadProducts() async {\n  // Validate and map an API response.\n}",
        "impl": ["class product", "factory", "fromjson", "future<list<product>>", "try"],
        "bug": "an API response may contain null fields and an asynchronous error is left unhandled",
        "fix": ["?", "??", "try", "catch", "fromjson"],
        "tests": ["test(", "expect(", "null", "empty list", "throws"],
        "ops": ["timeout", "typed model", "error state", "dispose"],
    },
    "data-science": {
        "topic": "produce a reproducible customer-churn evaluation with a grouped split, baseline, and metric report",
        "starter": "# Load data, split by customer_id, fit preprocessing, and report held-out metrics.\n",
        "impl": ["groupkfold", "pipeline", "baseline", "precision_score", "recall_score"],
        "bug": "the same customer appears in train and test while an imputer was fitted before the split",
        "fix": ["group", "train_test_split", "fit only on training data", "pipeline"],
        "tests": ["held-out", "baseline", "precision", "recall", "reproducible"],
        "ops": ["drift", "data leakage", "privacy", "monitoring"],
    },
    "django": {
        "topic": "implement a validated inventory update endpoint using a ModelForm, atomic transaction, and permission checks",
        "starter": "class StockUpdateForm(forms.ModelForm):\n    # Add validation.\n\n@login_required\ndef update_stock(request):\n    # Validate, authorize, and update transactionally.\n",
        "impl": ["modelform", "is_valid()", "transaction.atomic", "login_required", "save()"],
        "bug": "two concurrent updates can oversell stock, and the view trusts a client-supplied owner ID",
        "fix": ["select_for_update", "request.user", "transaction.atomic", "permission"],
        "tests": ["testcase", "assertEqual", "unauthorized", "insufficient stock"],
        "ops": ["csrf", "permission", "atomic", "logging"],
    },
    "docker": {
        "topic": "package a small API in a multi-stage Docker image with a non-root runtime and health check",
        "starter": "FROM python:3.13-slim AS build\n# Install locked dependencies.\nFROM python:3.13-slim\n# Copy runtime artifacts and run without root.\n",
        "impl": ["as build", "copy --from=build", "user", "healthcheck", "cmd"],
        "bug": "the image runs as root, copies build caches and credentials, and never checks service health",
        "fix": ["user", ".dockerignore", "healthcheck", "secrets"],
        "tests": ["docker build", "docker run", "health", "non-root", "exit code"],
        "ops": ["read-only", "least privilege", "pinned image", "scan"],
    },
    "dsa": {
        "topic": "design an LRU cache with O(1) average lookup and update operations",
        "starter": "class LRUCache:\n    def get(self, key):\n        pass\n\n    def put(self, key, value):\n        pass\n",
        "impl": ["hash map", "doubly linked list", "o(1)", "evict", "capacity"],
        "bug": "a cache does not refresh recency on a hit and fails when capacity is one",
        "fix": ["move to front", "evict least recently used", "capacity", "update"],
        "tests": ["capacity one", "cache hit", "eviction", "empty cache", "assert"],
        "ops": ["time complexity", "space complexity", "invariant", "edge case"],
    },
    "excel": {
        "topic": "build a sales reconciliation sheet that looks up product prices, sums regional sales, and handles missing SKUs",
        "starter": "A: SKU | B: Region | C: Quantity | D: Unit price | E: Revenue\nAdd formulas and a validation note for missing SKUs.\n",
        "impl": ["xlookup", "sumifs", "iferror", "quantity", "revenue"],
        "bug": "lookup failures show #N/A and the summary includes rows from other regions",
        "fix": ["iferror", "xlookup", "sumifs", "region"],
        "tests": ["known sku", "missing sku", "zero quantity", "region filter", "expected"],
        "ops": ["data validation", "named range", "protect formula cells", "audit"],
    },
    "expressjs": {
        "topic": "build an Express order endpoint with schema validation, authenticated ownership, and centralized error handling",
        "starter": "const express = require('express');\nconst router = express.Router();\nrouter.post('/orders', async (req, res, next) => {\n  // Validate input and persist an authorized order.\n});\n",
        "impl": ["router.post", "validation", "req.user", "next(error)", "status(201)"],
        "bug": "a route trusts req.body.ownerId and sends a stack trace to the client on database errors",
        "fix": ["req.user", "status(403)", "next(error)", "logger"],
        "tests": ["supertest", "status(400)", "status(401)", "status(201)", "ownership"],
        "ops": ["rate limit", "helmet", "request id", "redact"],
    },
    "fastapi": {
        "topic": "implement a validated FastAPI endpoint for an inventory reservation with typed input and ownership checks",
        "starter": "class ReservationIn(BaseModel):\n    # Define validated fields.\n\n@app.post('/reservations')\ndef create_reservation(payload: ReservationIn):\n    # Validate ownership and persist safely.\n",
        "impl": ["basemodel", "field", "@app.post", "httpException", "status_code"],
        "bug": "the endpoint trusts a client user ID and catches every exception as HTTP 200",
        "fix": ["depends(", "require_user", "httpException", "status_code=400"],
        "tests": ["testclient", "status_code", "unauthorized", "invalid payload", "assert"],
        "ops": ["timeout", "rate limit", "structured log", "redact"],
    },
    "flask": {
        "topic": "create a Flask inventory blueprint with validated forms, SQLAlchemy persistence, and authorization",
        "starter": "inventory_bp = Blueprint('inventory', __name__)\n@inventory_bp.post('/items')\ndef create_item():\n    # Validate request and persist an authorized item.\n    pass\n",
        "impl": ["blueprint", "request", "db.session", "commit()", "login_required"],
        "bug": "the view commits unvalidated input and returns raw exception text to the browser",
        "fix": ["rollback()", "validation", "current_user", "logger"],
        "tests": ["test_client", "status_code", "invalid input", "unauthorized", "assert"],
        "ops": ["csrf", "secure cookie", "parameterized", "error handler"],
    },
    "git": {
        "topic": "recover a feature branch after an accidental commit while preserving another developer's upstream commits",
        "starter": "git status\ngit fetch origin\n# Inspect history, recover safely, then update the feature branch.\n",
        "impl": ["git status", "git fetch", "git log", "git rebase"],
        "bug": "a developer plans to use git reset --hard and force-push an unreviewed shared branch",
        "fix": ["git reflog", "git branch backup", "git push --force-with-lease", "git status"],
        "tests": ["git diff --check", "git status", "git log", "working tree"],
        "ops": ["backup branch", "review diff", "protected branch", "force-with-lease"],
    },
    "github-actions": {
        "topic": "design a GitHub Actions workflow that runs tests on pull requests and publishes only from a protected release branch",
        "starter": "name: CI\non:\n  pull_request:\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
        "impl": ["on:", "pull_request:", "permissions:", "runs-on:", "steps:"],
        "bug": "a workflow uses write-all token permissions and exposes a deployment secret to untrusted pull-request code",
        "fix": ["permissions:", "contents: read", "environment:", "pull_request_target"],
        "tests": ["workflow validation", "pull request", "failed test", "artifact", "assert"],
        "ops": ["pin action sha", "least privilege", "environment protection", "secret"],
    },
    "go": {
        "topic": "build a Go HTTP handler that validates a request, calls a context-aware service, and returns structured errors",
        "starter": "func CreateOrder(w http.ResponseWriter, r *http.Request) {\n    // Decode, validate, call service, and respond.\n}\n",
        "impl": ["context.context", "json.newdecoder", "http.statuscreated", "error", "defer"],
        "bug": "a request handler ignores cancellation and returns a success response after the database call fails",
        "fix": ["r.context()", "if err != nil", "http.error", "timeout"],
        "tests": ["httptest", "t.run", "statuscode", "invalid json", "assert"],
        "ops": ["context timeout", "structured logging", "graceful shutdown", "race"],
    },
    "html": {
        "topic": "build an accessible product registration form with semantic sections, field labels, and native validation",
        "starter": "<form action=\"/products\" method=\"post\">\n  <!-- Add labeled fields, validation, and submit feedback. -->\n</form>",
        "impl": ["<form", "<label", "for=", "name=", "required", "<button"],
        "bug": "a form uses placeholders instead of labels and cannot be completed with a keyboard alone",
        "fix": ["<label", "id=", "for=", "fieldset", "legend"],
        "tests": ["label association", "required", "keyboard", "error message", "submit"],
        "ops": ["semantic html", "aria-describedby", "server validation", "autocomplete"],
    },
    "java": {
        "topic": "implement an order service that validates line items, calculates totals with BigDecimal, and returns explicit errors",
        "starter": "public final class OrderService {\n    public OrderResult createOrder(List<OrderLine> lines) {\n        // Validate and calculate safely.\n    }\n}\n",
        "impl": ["bigdecimal", "list<orderline>", "illegalargumentexception", "validate", "stream"],
        "bug": "the service uses double for currency and treats an empty order as a successful purchase",
        "fix": ["bigdecimal", "compareto", "isEmpty()", "exception"],
        "tests": ["@test", "assertEquals", "empty order", "rounding", "invalid quantity"],
        "ops": ["try-with-resources", "logging", "validation", "idempotency"],
    },
    "javascript": {
        "topic": "implement a debounced search box with request cancellation, accessible loading state, and safe result rendering",
        "starter": "function createSearch(input, results) {\n  // Debounce input and render results as text.\n}\n",
        "impl": ["settimeout", "cleartimeout", "addeventlistener", "textcontent", "abortcontroller"],
        "bug": "slow older search responses overwrite new results and returned text is inserted as HTML",
        "fix": ["abortcontroller", "textcontent", "catch", "clearTimeout"],
        "tests": ["node:test", "assert", "empty query", "stale response", "html input"],
        "ops": ["abortcontroller", "timeout", "textcontent", "aria-live"],
    },
    "jquery": {
        "topic": "maintain a delegated jQuery table filter that handles dynamically added rows and avoids unsafe HTML rendering",
        "starter": "$(document).on('input', '#filter', function () {\n  // Filter rows using text and update an accessible status.\n});\n",
        "impl": ["$(document).on", ".text()", ".toggle(", "aria-live"],
        "bug": "handlers are bound before dynamic rows are added and search terms are injected through .html()",
        "fix": ["$(document).on", ".text(", ".off(", "escape"],
        "tests": ["trigger", "expect", "dynamic row", "empty query", "html input"],
        "ops": ["event delegation", ".text(", "unbind", "accessible status"],
    },
    "json-yaml": {
        "topic": "define and validate a deployment configuration in YAML and JSON with required keys and explicit types",
        "starter": "service:\n  name: catalog-api\n  replicas: 2\n  readinessProbe:\n    enabled: true\n",
        "impl": ["schema", "required", "type", "replicas", "readinessprobe"],
        "bug": "a configuration accepts a string where an integer is required and silently ignores unknown production keys",
        "fix": ["type: integer", "additionalproperties: false", "required", "validation"],
        "tests": ["valid fixture", "invalid fixture", "schema validation", "missing key", "assert"],
        "ops": ["safe_load", "schema", "secret reference", "unknown key"],
    },
    "kotlin": {
        "topic": "create a null-safe Kotlin data model and repository that maps API records and represents failures explicitly",
        "starter": "data class Product(/* typed fields */)\n\nsuspend fun loadProducts(): Result<List<Product>> {\n    // Map response and handle errors.\n}\n",
        "impl": ["data class", "suspend fun", "result<list<product>>", "mapnotnull", "try"],
        "bug": "a repository force-unwraps an optional field and converts network failure to an empty success result",
        "fix": ["?.", "?:", "result.failure", "catch"],
        "tests": ["@test", "assertEquals", "null", "empty list", "failure"],
        "ops": ["cancellation", "timeout", "sealed class", "error state"],
    },
    "linux": {
        "topic": "write an operational shell script that checks disk usage, logs a timestamped result, and exits on threshold breach",
        "starter": "#!/usr/bin/env bash\nset -euo pipefail\n# Read a threshold, inspect usage, write a log, and return a status.\n",
        "impl": ["df", "awk", "date", "logger", "exit"],
        "bug": "a cron job runs with an unexpected PATH and deletes temporary files using an unchecked variable",
        "fix": ["set -euo pipefail", "command -v", "mktemp", "trap", "quote"],
        "tests": ["threshold met", "threshold exceeded", "missing command", "exit code", "assert"],
        "ops": ["chmod 750", "least privilege", "log rotation", "trap"],
    },
    "lua": {
        "topic": "write a Lua configuration normalizer that validates a table, applies defaults, and reports invalid fields",
        "starter": "local function normalize_config(config)\n  -- Validate a table and return normalized values.\nend\n\nreturn normalize_config\n",
        "impl": ["local function", "type(config)", "pairs(", "return", "nil"],
        "bug": "configuration code indexes nil and mutates the shared defaults table across calls",
        "fix": ["type(", "nil", "copy", "pairs(", "error("],
        "tests": ["assert(", "empty table", "missing key", "invalid type", "default"],
        "ops": ["validate input", "avoid shared mutation", "pcall", "error message"],
    },
    "mongodb": {
        "topic": "aggregate order records by customer, filter completed orders, and inspect index use for a large collection",
        "starter": "db.orders.aggregate([\n  // Add $match and $group stages.\n])\n",
        "impl": ["$match", "$group", "$sum", "customerid", "explain"],
        "bug": "an aggregation groups every order before filtering status and a lookup collection has no supporting index",
        "fix": ["$match", "createindex", "explain", "pipeline"],
        "tests": ["fixture", "expected result", "empty collection", "duplicate order", "assert"],
        "ops": ["schema validation", "compound index", "least privilege", "explain"],
    },
    "mysql": {
        "topic": "write a transaction-safe inventory reservation using parameterized statements and row-level locking",
        "starter": "START TRANSACTION;\n-- Lock stock row, validate quantity, update, then COMMIT or ROLLBACK.\n",
        "impl": ["start transaction", "for update", "update", "commit", "rollback"],
        "bug": "two purchases can reserve the same last item and a failed update leaves the transaction open",
        "fix": ["for update", "rollback", "affected rows", "commit"],
        "tests": ["transaction", "zero stock", "concurrent", "rollback", "assert"],
        "ops": ["prepared statement", "least privilege", "explain", "index"],
    },
    "nextjs": {
        "topic": "build a server-rendered product detail route with validated parameters, not-found handling, and deliberate caching",
        "starter": "export default async function ProductPage({ params }) {\n  // Fetch a product safely and handle missing data.\n}\n",
        "impl": ["async function", "params", "notfound(", "await", "revalidate"],
        "bug": "a page fetches private account data in a shared cache and renders an invalid product slug",
        "fix": ["no-store", "notfound(", "validate", "authorization"],
        "tests": ["valid slug", "invalid slug", "not found", "cache", "assert"],
        "ops": ["server component", "no-store", "metadata", "authorization"],
    },
    "nodejs": {
        "topic": "process a large uploaded file as a stream with backpressure, bounded memory use, and explicit error handling",
        "starter": "import { createReadStream, createWriteStream } from 'node:fs';\nimport { pipeline } from 'node:stream/promises';\n// Implement the streaming transform.\n",
        "impl": ["createreadstream", "pipeline(", "transform", "await", "catch"],
        "bug": "the handler reads the entire file into memory and fails to clean up partial output after an error",
        "fix": ["pipeline(", "destroy", "catch", "temporary file"],
        "tests": ["node:test", "assert", "large input", "stream error", "cleanup"],
        "ops": ["backpressure", "timeout", "size limit", "abortsignal"],
    },
    "numpy": {
        "topic": "normalize a numeric matrix row-wise while preserving invalid-value masks and avoiding Python loops",
        "starter": "import numpy as np\n\ndef normalize_rows(values):\n    # Validate shape, handle non-finite values, and normalize rows.\n    ...\n",
        "impl": ["np.asarray", "np.isfinite", "axis=1", "np.where", "dtype"],
        "bug": "the implementation divides by zero for an all-zero row and treats NaN as an ordinary measurement",
        "fix": ["np.isfinite", "zero", "axis", "mask"],
        "tests": ["np.testing", "all-zero", "nan", "shape", "dtype"],
        "ops": ["vectorized", "memory", "finite", "reproducible"],
    },
    "pandas": {
        "topic": "produce a monthly sales report using pandas groupby, validated merges, and explicit missing-value handling",
        "starter": "import pandas as pd\n\ndef monthly_report(orders, customers):\n    # Validate keys, merge, group, and summarize.\n    ...\n",
        "impl": ["merge(", "validate=", "groupby(", "agg(", "fillna"],
        "bug": "a many-to-many customer merge duplicates revenue and missing dates are silently assigned to a month",
        "fix": ["validate=", "dropna", "to_datetime", "duplicated"],
        "tests": ["pytest", "duplicate key", "missing date", "expected sum", "assert"],
        "ops": ["dtype", "missingness", "row count", "reproducible"],
    },
    "php": {
        "topic": "implement a product creation service with validated input, PDO prepared statements, and secure error handling",
        "starter": "function createProduct(PDO $pdo, array $input): array {\n    // Validate fields, use a prepared statement, and return a result.\n}\n",
        "impl": ["filter_var", "prepare(", "execute(", "password_hash", "throw"],
        "bug": "the handler concatenates request values into SQL and returns internal exception messages to clients",
        "fix": ["prepare(", "execute(", "catch", "error log"],
        "tests": ["phpunit", "assertsame", "invalid input", "duplicate sku", "unauthorized"],
        "ops": ["csrf", "prepared statement", "secure session", "redact"],
    },
    "postgresql": {
        "topic": "design a concurrent-safe reservation transaction and a supporting index for recent customer orders",
        "starter": "BEGIN;\n-- Validate a reservation, update stock, and COMMIT or ROLLBACK.\n",
        "impl": ["begin", "for update", "commit", "rollback", "create index"],
        "bug": "concurrent reservations oversell stock and a slow report scans the entire orders table",
        "fix": ["for update", "rollback", "explain analyze", "create index"],
        "tests": ["transaction", "concurrent", "rollback", "expected rows", "assert"],
        "ops": ["parameterized", "least privilege", "explain analyze", "backup"],
    },
    "powershell": {
        "topic": "create a PowerShell inventory audit command with typed parameters, pipeline output, and meaningful error behavior",
        "starter": "function Get-InventoryAudit {\n  [CmdletBinding()]\n  param()\n  # Emit objects and validate input.\n}\n",
        "impl": ["[cmdletbinding()]", "param(", "[parameter(", "try", "catch"],
        "bug": "a command writes formatted strings instead of objects and silently continues after a failed operation",
        "fix": ["write-error", "$erroractionpreference", "throw", "pscustomobject"],
        "tests": ["pester", "should -be", "empty input", "invalid parameter", "error"],
        "ops": ["validatepattern", "erroraction", "credential", "transcript"],
    },
    "python": {
        "topic": "implement a CSV sales summarizer with Decimal-safe totals, malformed-row reporting, and unit tests",
        "starter": "from decimal import Decimal\nimport csv\nfrom pathlib import Path\n\ndef summarize_sales(path: Path) -> dict:\n    # Parse, validate, summarize, and report rejected rows.\n    ...\n",
        "impl": ["decimal(", "csv.dictreader", "pathlib", "try", "except"],
        "bug": "the script uses float for currency, crashes on one malformed row, and reports no rejected records",
        "fix": ["decimal(", "invalidoperation", "rejected", "logging"],
        "tests": ["unittest", "assertEqual", "malformed row", "empty file", "decimal"],
        "ops": ["pathlib", "type hints", "csv injection", "structured logging"],
    },
    "pytorch": {
        "topic": "build a reproducible PyTorch training loop with validation metrics, gradient reset, and checkpointing",
        "starter": "model.train()\nfor epoch in range(num_epochs):\n    # Zero gradients, forward, loss, backward, and optimizer step.\n    ...\n",
        "impl": ["optimizer.zero_grad", "loss.backward", "optimizer.step", "model.train", "state_dict"],
        "bug": "gradients accumulate between batches and validation updates model weights by omitting no_grad",
        "fix": ["zero_grad", "torch.no_grad", "model.eval", "optimizer.step"],
        "tests": ["fixed seed", "validation", "loss", "checkpoint", "assert"],
        "ops": ["reproducibility", "device", "checkpoint", "drift"],
    },
    "r": {
        "topic": "create a reproducible R data-cleaning and grouped-summary pipeline with missing-value checks",
        "starter": "library(dplyr)\nclean_summary <- function(data) {\n  # Validate columns, clean missing values, and summarize by group.\n}\n",
        "impl": ["dplyr", "group_by(", "summarise(", "na.rm = true", "set.seed"],
        "bug": "a grouped summary silently drops missing outcomes and random sampling is not reproducible",
        "fix": ["is.na", "na.rm = true", "set.seed", "count("],
        "tests": ["stopifnot", "empty data", "missing value", "expected n", "reproducible"],
        "ops": ["data dictionary", "set.seed", "missingness", "sessioninfo"],
    },
    "react": {
        "topic": "build a controlled React search form with debounced results, loading feedback, and cleanup on unmount",
        "starter": "function ProductSearch() {\n  // Use state/effect for a controlled query and cancel stale work.\n  return null;\n}\n",
        "impl": ["usestate", "useeffect", "onchange", "onsubmit", "aria-live"],
        "bug": "an effect creates a timer that is never cleared and stale requests overwrite the latest result",
        "fix": ["clearTimeout", "abortcontroller", "return () =>", "catch"],
        "tests": ["testing-library", "userEvent", "expect(", "empty query", "unmount"],
        "ops": ["cleanup", "aria-live", "controlled input", "error state"],
    },
    "redis": {
        "topic": "design an atomic API rate limiter with a bounded time window and predictable expiry behavior",
        "starter": "-- Provide an atomic Redis operation for a per-user request limit.\n-- Define count, expiry, and allowed/blocked result.\n",
        "impl": ["incr", "expire", "ttl", "atomic", "user key"],
        "bug": "the counter increments separately from expiry creation, leaving a key that never expires after a crash",
        "fix": ["lua", "atomic", "expire", "ttl"],
        "tests": ["limit boundary", "expiry", "parallel requests", "isolated users", "assert"],
        "ops": ["ttl", "memory policy", "key prefix", "monitor"],
    },
    "rest-api-development": {
        "topic": "specify an idempotent order-creation endpoint with schema validation, ownership, and clear HTTP errors",
        "starter": "POST /v1/orders\nRequest: {\"items\": [...], \"idempotency_key\": \"...\"}\nDefine response schemas and error cases.\n",
        "impl": ["idempotency-key", "201", "400", "401", "409"],
        "bug": "replaying a POST creates duplicate orders and an unauthorized user can query another owner's resource",
        "fix": ["idempotency", "ownership", "401", "403", "409"],
        "tests": ["contract test", "duplicate request", "invalid schema", "unauthorized", "assert"],
        "ops": ["rate limit", "request id", "redact", "timeout"],
    },
    "ruby": {
        "topic": "implement a Ruby service object that imports validated contact rows and reports row-level failures",
        "starter": "class ContactImporter\n  def call(rows)\n    # Validate, import, and return a structured result.\n  end\nend\n",
        "impl": ["class contactimporter", "def call", "each_with_object", "raise", "rescue"],
        "bug": "an importer mutates a shared default array and rescues every error without reporting the rejected row",
        "fix": ["initialize", "rescue", "errors", "immutable", "raise"],
        "tests": ["rspec", "expect(", "empty rows", "invalid email", "failure"],
        "ops": ["keyword arguments", "structured error", "idempotent", "logging"],
    },
    "rust": {
        "topic": "implement a Rust parser that converts records into typed values while returning recoverable errors",
        "starter": "fn parse_record(line: &str) -> Result<Record, ParseError> {\n    // Parse, validate, and return typed data.\n}\n",
        "impl": ["result<record", "?", "ok(", "err(", "option"],
        "bug": "the parser unwraps untrusted fields and panics on malformed input instead of returning an error",
        "fix": ["map_err", "?", "ok_or", "result"],
        "tests": ["#[test]", "assert_eq!", "malformed input", "empty field", "error"],
        "ops": ["ownership", "no unwrap", "bounded input", "error context"],
    },
    "sass": {
        "topic": "create a maintainable design-token layer and responsive card mixin in Sass using the module system",
        "starter": "@use 'sass:map';\n$space-md: 1rem;\n@mixin responsive-card {\n  // Add tokenized responsive styles.\n}\n",
        "impl": ["@use", "$space-md", "@mixin", "@include", "@media"],
        "bug": "the stylesheet repeats hard-coded colors and spacing values and a nested selector becomes too specific",
        "fix": ["@use", "variable", "mixin", "nesting", "focus-visible"],
        "tests": ["sass --check", "breakpoint", "focus", "contrast", "assert"],
        "ops": ["design token", "@use", "responsive", "reduced motion"],
    },
    "scikit-learn": {
        "topic": "build a leakage-safe classification pipeline with grouped validation and a baseline comparison",
        "starter": "from sklearn.pipeline import Pipeline\nfrom sklearn.compose import ColumnTransformer\n# Fit preprocessing and classifier only within the cross-validation pipeline.\n",
        "impl": ["pipeline(", "columntransformer", "groupkfold", "baseline", "precision_score"],
        "bug": "feature scaling is fit before split and repeated entities appear in both train and test folds",
        "fix": ["groupkfold", "pipeline", "fit only on training data", "data leakage"],
        "tests": ["cross_val_score", "group", "baseline", "held-out", "assert"],
        "ops": ["drift", "precision", "recall", "reproducible"],
    },
    "scipy": {
        "topic": "fit a nonlinear curve with SciPy, inspect convergence, and report parameter uncertainty",
        "starter": "import numpy as np\nfrom scipy.optimize import curve_fit\n\ndef model(x, a, b):\n    return a * np.exp(-b * x)\n",
        "impl": ["curve_fit(", "popt", "pcov", "np.isfinite", "maxfev"],
        "bug": "the fit accepts NaN values and reports parameters without checking convergence or covariance quality",
        "fix": ["np.isfinite", "pcov", "residual", "warning"],
        "tests": ["np.testing", "synthetic data", "noise", "convergence", "assert"],
        "ops": ["confidence interval", "residual", "reproducible", "bounds"],
    },
    "solidity": {
        "topic": "design a restricted vault withdrawal with checks-effects-interactions and explicit events",
        "starter": "contract Vault {\n    mapping(address => uint256) public balances;\n    // Add access control, safe withdrawal, and events.\n}\n",
        "impl": ["onlyowner", "nonreentrant", "balances[msg.sender]", "emit", "require"],
        "bug": "a withdrawal performs an external call before updating balances and has no reentrancy protection",
        "fix": ["checks-effects-interactions", "nonreentrant", "balances", "emit"],
        "tests": ["forge test", "revert", "unauthorized", "reentrancy", "assert"],
        "ops": ["access control", "custom error", "event", "slither"],
    },
    "sql": {
        "topic": "write a CTE and window-function report that ranks each customer's orders by month and totals revenue",
        "starter": "WITH monthly_orders AS (\n  -- Aggregate revenue by customer and month.\n)\nSELECT ...;\n",
        "impl": ["with monthly_orders", "sum(", "group by", "row_number()", "partition by"],
        "bug": "a join multiplies revenue rows and the ranking includes orders from the wrong month",
        "fix": ["join key", "group by", "partition by", "row_number()"],
        "tests": ["fixture", "duplicate join", "empty month", "expected total", "assert"],
        "ops": ["parameterized", "explain", "index", "least privilege"],
    },
    "sqlite": {
        "topic": "implement a SQLite transaction that imports validated records with prepared parameters and uniqueness handling",
        "starter": "PRAGMA foreign_keys = ON;\nBEGIN;\n-- Validate rows, insert parameterized values, and roll back on failure.\n",
        "impl": ["pragma foreign_keys = on", "begin", "?", "commit", "rollback"],
        "bug": "foreign-key enforcement is disabled and a failed batch leaves partially imported rows",
        "fix": ["pragma foreign_keys = on", "rollback", "transaction", "unique"],
        "tests": ["in-memory database", "duplicate key", "invalid foreign key", "rollback", "assert"],
        "ops": ["parameterized", "busy timeout", "index", "backup"],
    },
    "swift": {
        "topic": "build a Swift Codable model and async repository with cancellation-aware network loading",
        "starter": "struct Product: Codable {\n    // Define typed properties.\n}\n\nfunc loadProducts() async throws -> [Product] {\n    // Fetch and decode data.\n}\n",
        "impl": ["struct product: codable", "async throws", "urlsession", "jsondecoder", "guard let"],
        "bug": "a network task updates a screen after cancellation and decoding failures are treated as empty success",
        "fix": ["task.iscancelled", "throw", "do", "catch"],
        "tests": ["xctest", "xctassert", "invalid json", "empty response", "cancellation"],
        "ops": ["codable", "task cancellation", "error state", "privacy"],
    },
    "tailwind-css": {
        "topic": "style an accessible responsive dashboard using Tailwind utilities without hiding focus or reducing text readability",
        "starter": "<section class=\"grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3\">\n  <!-- Add accessible dashboard cards. -->\n</section>",
        "impl": ["grid-cols-1", "md:grid-cols-2", "focus-visible:", "gap-", "aria-label"],
        "bug": "cards overflow on narrow screens and the design removes the keyboard outline to match a mockup",
        "fix": ["min-w-0", "focus-visible:", "outline", "break-words"],
        "tests": ["320px", "768px", "1440px", "keyboard", "contrast"],
        "ops": ["responsive", "focus-visible", "contrast", "reduced motion"],
    },
    "typescript": {
        "topic": "design a type-safe API result with discriminated unions and exhaustive handling of success and failure states",
        "starter": "type ApiResult<T> =\n  | { status: 'success'; data: T }\n  | { status: 'error'; message: string };\n\nfunction handleResult<T>(result: ApiResult<T>) {\n  // Narrow and exhaustively handle each case.\n}\n",
        "impl": ["type apiresult", "status: 'success'", "status: 'error'", "switch", "never"],
        "bug": "a response casts untrusted JSON to a domain type and an unknown status silently falls through",
        "fix": ["unknown", "type guard", "never", "validation"],
        "tests": ["vitest", "expect(", "success case", "error case", "unknown status"],
        "ops": ["strict", "unknown", "runtime validation", "exhaustive"],
    },
    "vue": {
        "topic": "build a Vue product filter with reactive state, computed results, and cleanup of a watcher or event listener",
        "starter": "<script setup>\nimport { ref, computed, onUnmounted } from 'vue'\n// Define filtering state and cleanup.\n</script>\n",
        "impl": ["ref(", "computed(", "onunmounted", "v-model", "@submit.prevent"],
        "bug": "a watcher triggers redundant network calls and an event listener remains active after unmount",
        "fix": ["watch(", "onunmounted", "cleanup", "debounce"],
        "tests": ["vitest", "mount(", "expect(", "empty results", "unmount"],
        "ops": ["cleanup", "computed", "error state", "accessible"],
    },
    "web-application-security": {
        "topic": "harden a cookie-authenticated form endpoint against CSRF, XSS, session theft, and repeated abuse",
        "starter": "Threat: untrusted form submission\nControls: origin checks, CSRF token, output encoding, cookie policy, rate limit\n",
        "impl": ["csrf token", "samesite", "httponly", "content security policy", "rate limit"],
        "bug": "the endpoint trusts cross-site requests and reflects unescaped user input while session cookies are script-readable",
        "fix": ["csrf token", "escape", "httponly", "samesite", "csp"],
        "tests": ["cross-site request", "script payload", "expired session", "rate limit", "assert"],
        "ops": ["least privilege", "security headers", "audit log", "incident response"],
    },
    "xml": {
        "topic": "validate an XML order document with a namespace-aware schema and safe parser settings",
        "starter": "<orders xmlns=\"https://example.test/orders\">\n  <order id=\"A-100\"><quantity>2</quantity></order>\n</orders>\n",
        "impl": ["namespace", "xsd", "schema", "quantity", "validation"],
        "bug": "an XML parser resolves external entities and a namespace-qualified element is rejected by a namespace-blind selector",
        "fix": ["external entities", "disable", "namespace", "xpath", "schema validation"],
        "tests": ["valid fixture", "invalid quantity", "unknown namespace", "xxe", "assert"],
        "ops": ["disable dtd", "disable external entities", "size limit", "validate"],
    },
    "generative-ai": {
        "topic": "design a retrieval-grounded support assistant with source citations, uncertainty handling, and safe fallback",
        "starter": "Evidence retrieval:\nCitations:\nPrompt-injection controls:\nFallback and escalation:\n",
        "impl": ["retrieval", "citations", "untrusted input", "prompt injection", "fallback"],
        "bug": "retrieved text can override system instructions and the assistant invents a policy when retrieval returns no evidence",
        "fix": ["untrusted input", "prompt injection", "abstain", "citation"],
        "tests": ["supported answer", "missing evidence", "malicious document", "privacy", "assert"],
        "ops": ["privacy", "access control", "latency", "monitoring"],
    },

}


def task(task_id: str, title: str, prompt: str, starter: str, required: list[str], rubric: list[str], points: int = 25) -> dict:
    return {
        "id": task_id,
        "title": title,
        "prompt": prompt,
        "submission_type": "text",
        "starter": starter,
        "rubric": rubric,
        "points": points,
        "grader": {"type": "contains_all", "required_strings": required},
        "feedback_correct": "The required implementation elements were detected.",
        "feedback_incorrect": "The submission is missing one or more required implementation elements. Review the task requirements and resubmit on a new attempt if allowed.",
    }


def _short_phrase(value: str, words: int = 7, max_chars: int = 68) -> str:
    phrase = " ".join(str(value or "").strip().rstrip(".!?").split()[:words])
    if len(phrase) > max_chars:
        phrase = phrase[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    if phrase:
        phrase = phrase[0].upper() + phrase[1:]
    return phrase


def create_exam(slug: str, cfg: dict, course_title: str) -> dict:
    topic = cfg["topic"]
    starter = cfg["starter"]
    bug = cfg["bug"]
    implementation_title = f"Implement: {_short_phrase(topic)}"
    repair_title = f"Repair: {_short_phrase(bug)}"
    test_title = f"Regression tests: {_short_phrase(topic, words=5, max_chars=54)}"
    course_short_title = _short_phrase(course_title.split("—")[0].split("–")[0], words=5, max_chars=48)
    hardening_title = f"Production hardening: {course_short_title}"
    return {
        "id": f"{slug}-intermediate-practical-v1",
        "title": f"{course_title} — Intermediate Practical Assessment",
        "status": "published",
        "difficulty": "intermediate",
        "pass_percent": 75,
        "execution_mode": "structured_text_validation",
        "instructions": (
            f"This is a course-specific, intermediate practical assessment for {course_title}. "
            "Submit the requested code, query, configuration, or operational artifact as text. "
            "The backend applies deterministic content checks to required implementation elements; "
            "it does not execute arbitrary learner code. Do not include secrets or production credentials. "
            "A task is accepted only when its required elements are present."
        ),
        "tasks": [
            task(
                "implement-core-artifact", implementation_title,
                f"Create an intermediate {course_title} solution for this task: {topic}. "
                "Submit the relevant code, query, configuration, or worked artifact. "
                "Include the required data flow and handle invalid or missing input. "
                "Use the starter below as a starting point, not as the complete solution.",
                starter,
                cfg["impl"],
                [f"Implements the stated {course_title} task.", "Handles invalid or missing input.", "Uses the expected language or tool constructs."],
            ),
            task(
                "repair-defect", repair_title,
                f"A production {course_title} implementation has this defect: {bug}. "
                "Return a corrected artifact and a concise explanation of why the correction works. "
                "Your solution must show a concrete fix, not only describe the problem.",
                f"Defect report: {bug}\n\nCorrection:\n\nReasoning:",
                cfg["fix"],
                ["Identifies the failure mode.", "Provides an applicable correction.", "Explains how the correction prevents recurrence."],
            ),
            task(
                "regression-tests", test_title,
                f"Write a small regression-test set for the {topic}. Include the normal case, an invalid or empty input case, and a boundary or failure case. "
                "Show assertions or equivalent verification commands and the expected outcome.",
                "Normal case:\n\nInvalid/empty case:\n\nBoundary/failure case:\n\nAssertions or commands:",
                cfg["tests"],
                ["Covers normal behavior.", "Covers at least one edge case.", "Includes an assertion or runnable verification command."],
            ),
            task(
                "production-reliability", hardening_title,
                f"Review your {course_title} solution for reliability, security, and maintainability. "
                "Describe and implement a small set of concrete safeguards in the code, query, configuration, or runbook. "
                "Do not expose secrets or rely on client-controlled authorization.",
                "Risk:\n\nMitigation in the artifact:\n\nVerification:\n\nOperational signal:",
                cfg["ops"],
                ["Includes a concrete reliability or security safeguard.", "Explains how the safeguard is verified.", "Avoids unsafe default behavior."],
            ),
        ],
    }


def main() -> None:
    course_dirs = sorted(path for path in ROOT.iterdir() if path.is_dir() and (path / "course.json").is_file())
    missing = [path.name for path in course_dirs if path.name not in COURSES and path.name != "ai"]
    extras = sorted(set(COURSES) - {path.name for path in course_dirs})
    if missing or extras:
        raise SystemExit(f"Assessment mapping mismatch; missing={missing}, extras={extras}")

    written = 0
    for course_dir in course_dirs:
        slug = course_dir.name
        manifest_path = course_dir / "course.json"
        original_manifest_text = manifest_path.read_bytes().decode("utf-8")
        manifest_newline = "\r\n" if "\r\n" in original_manifest_text else "\n"
        manifest = json.loads(original_manifest_text)
        course_info = manifest.get("course", manifest)
        if course_info.get("status") != "published":
            continue
        if slug == "ai":
            # Preserve the already-authored AI Foundation practical assessment.
            continue
        assessment_path = course_dir / "exams" / "practical-exam.json"
        cfg = COURSES[slug]
        exam = create_exam(slug, cfg, str(course_info.get("title") or slug.title()))
        assessment_path.parent.mkdir(parents=True, exist_ok=True)
        assessment_path.write_text(json.dumps(exam, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        assessment_files = manifest.get("assessment_files")
        if not isinstance(assessment_files, list):
            assessment_files = []
            manifest["assessment_files"] = assessment_files
        if "exams/practical-exam.json" not in assessment_files:
            assessment_files.append("exams/practical-exam.json")
        serialized_manifest = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        if manifest_newline == "\r\n":
            serialized_manifest = serialized_manifest.replace("\n", "\r\n")
        manifest_path.write_bytes(serialized_manifest.encode("utf-8"))
        written += 1
    print(f"Wrote {written} course-specific practical assessments; AI assessment preserved.")

if __name__ == "__main__":
    main()
