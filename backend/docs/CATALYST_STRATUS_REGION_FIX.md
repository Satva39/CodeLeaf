# CodeLeaf Catalyst Stratus India-region permanent fix

The live development smoke test succeeded on 2026-10-31 after using these values:

```dotenv
CATALYST_PROJECT_DOMAIN=https://api.catalyst.zoho.in
CATALYST_ACCOUNTS_URL=https://accounts.zoho.in
CATALYST_STRATUS_RESOURCE_SUFFIX=.zohostratus.in
```

The CodeLeaf adapter now applies these settings before importing `zcatalyst_sdk` and includes a small compatibility shim for the SDK 1.5.0 URL join behavior. The shim strips leading slashes only for requests that have no explicit URL and no `catalyst_service`, matching the successful diagnostic. It leaves service-prefixed and explicitly addressed requests alone. It does not turn off TLS certificate verification and does not alter SDK files inside `.venv`.

## Apply locally

Copy the changed files from this patch into the matching paths under `E:\Code_Leaf\backend`:

- `app/storage/catalyst_stratus.py`
- `app/storage/factory.py`
- `app/config.py`
- `.env.example` (reference only; do not replace your real `.env`)
- `scripts/test_catalyst_stratus_adapter.py`
- `docs/CATALYST_STRATUS_MIGRATION.md`

Add these three settings to the existing `backend/.env` if not already present:

```dotenv
CATALYST_PROJECT_DOMAIN=https://api.catalyst.zoho.in
CATALYST_ACCOUNTS_URL=https://accounts.zoho.in
CATALYST_STRATUS_RESOURCE_SUFFIX=.zohostratus.in
```

Do not replace the existing project ID, ZAID, bucket name, client ID, client secret, or refresh token. Do not commit `.env`.

Run these checks from `backend`:

```powershell
python -m py_compile app\storage\catalyst_stratus.py app\storage\factory.py app\config.py scripts\test_catalyst_stratus_adapter.py
python scripts\test_catalyst_stratus_adapter.py
python scripts\catalyst_stratus_smoke_test.py
```

The adapter unit test is mocked. The live smoke test should again report connectivity, upload, metadata, range read, checksum, and cleanup as PASS.

## Render

After local checks pass, add the same three `CATALYST_*` variables to the Render backend service environment. Keep the existing `CATALYST_*` credentials private. Leave the storage selector unchanged for now:

```dotenv
PORTFOLIO_STORAGE_PROVIDER=database
CATALYST_STRATUS_ENABLED=false
```

Do not run the archive migration or Neon cleanup as part of this compatibility patch. First deploy the code with the database provider still active, run a small test-account portfolio upload/download/delete, audit the source archives, then follow the staged migration and verification steps in `CATALYST_STRATUS_MIGRATION.md`.
