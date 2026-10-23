# User Session Manager

## Goal
Session lookup, expiration, invalidation, key isolation, and secret-safe logging.

## Safe development setup
1. Create a Python virtual environment.
2. Install the dependency in `requirements.txt`.
3. Start or select a disposable, private Redis development instance.
4. Set `REDIS_URL` in your local shell; do not commit `.env` files or credentials.
5. Implement the TODOs in `app.py`, then test normal, missing-data, repeat-request, and failure cases.

## Verification
- Use synthetic data only.
- Run your local tests and document output in this README.
- These starter files do not run inside CodeLeaf's browser and do not imply a production deployment.
