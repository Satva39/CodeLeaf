# CodeLeaf payment checkout hotfix

## Files in this patch

This is an incremental patch for the current CodeLeaf source tree. It does not contain a full copy of the project, `.env` files, secrets, `node_modules`, `.venv`, or Git history.

## What this fixes

1. `frontend/api/proxy/[...path].js` now falls back to the known production API origin `https://codeleaf-api.onrender.com` when `CODELEAF_API_ORIGIN` is not set. A valid `CODELEAF_API_ORIGIN` server environment variable can still override it.
2. `GET /api/plans` returns the public plan catalog and safe payment-readiness diagnostics. It reports only missing variable names and booleans; it never returns secret values.
3. Paid plan cards remain disabled while the backend cannot confirm checkout readiness. Pro and Max each require their corresponding monthly provider plan ID. Full Access is a one-time order and does not require a monthly plan ID.
4. Checkout fails closed with a structured error unless the backend has the key ID, key secret, and webhook secret. The UI turns structured errors into readable messages.
5. `render.yaml` declares the required server-only settings as unsynchronized variables. It does not include credential values.

## Apply the patch

1. Extract this ZIP into the existing project root (for example `E:\Code_Leaf`) and preserve the folder structure.
2. Review the diff; keep all existing `.env` files and secrets unchanged.
3. Run the included focused tests listed below.
4. Commit and deploy only after reviewing the changes. Backend and frontend need the updated code before the new readiness response is available.

## Payment-account eligibility

Razorpay's current merchant terms require the merchant user to be at least 18 and legally capable of entering binding contracts. The merchant account, KYC, settlement details, dashboard settings, and credentials must be owned and managed by an eligible adult account holder or properly authorized business representative. Do not use another person's identity or credentials or bypass eligibility requirements. The student developer must not independently operate the merchant account.

## Server-only settings required from the authorized account holder

- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`
- `RAZORPAY_PRO_PLAN_ID` (must identify an INR ₹299 monthly plan)
- `RAZORPAY_MAX_PLAN_ID` (must identify an INR ₹699 monthly plan)
- `RAZORPAY_SUBSCRIPTION_TOTAL_COUNT` (the current project default is 1200 cycles; confirm intended subscription term and provider limits)

The backend checks the configured Pro/Max provider plan metadata before creating a subscription. Never put these values in frontend/Vite variables, browser code, source control, logs, or support messages.

The following is the deployed API webhook endpoint for the current service:

`https://codeleaf-api.onrender.com/api/payments/webhook`

The authorized account holder must verify that this exact endpoint and the events handled by the backend are saved in the provider dashboard, and that the dashboard secret matches `RAZORPAY_WEBHOOK_SECRET`. The code can check that the secret exists but cannot prove the dashboard webhook is saved. The events handled in the current backend are `order.paid`, subscription lifecycle events (`subscription.activated`, `subscription.charged`, `subscription.updated`, `subscription.cancelled`, `subscription.halted`, `subscription.paused`, `subscription.resumed`, `subscription.completed`, `subscription.expired`), `payment.failed`, `payment.refunded`, and `refund.processed`.

## Test commands

From `frontend/`:

```bash
node scripts/test_api_proxy.mjs
node scripts/test_deployment_config.mjs
node scripts/test_plan_comparison_catalog.mjs
node scripts/test_payment_readiness_ui.mjs
```

From `backend/`:

```bash
python -m compileall -q app scripts
python scripts/test_payment_security.py
```

These tests use mocked provider calls and temporary local databases. They do not prove that a live merchant account is activated or that a real payment succeeds.
