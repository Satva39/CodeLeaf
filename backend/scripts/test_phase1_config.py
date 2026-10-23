"""Tests production configuration guards without loading or changing real .env values."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Settings  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def make_valid_production(**overrides) -> Settings:
    values = {
        "_env_file": None,
        "app_env": "production",
        "database_url": "postgresql+psycopg://codeleaf_ci:qP8vR2mX7kN4wY9t@ep-phase1-test.neon.tech/codeleaf?sslmode=require",
        "jwt_secret": "K7wN9pQ2xR5vT8mY4zB6cD1fG3hJ0kL7sA9uV2eX5rP8nM4q",
        "cookie_secure": True,
        "frontend_origins": "https://codeleaf.vercel.app",
        "preview_draft_courses": False,
        "frontend_base_url": "https://codeleaf.vercel.app",
        "email_test_mode": False,
        "email_from": "accounts@codeleaf.com",
        "smtp_host": "smtp.gmail.com",
        "smtp_username": "accounts@codeleaf.com",
        "smtp_password": "test-app-password-not-a-real-secret",
    }
    values.update(overrides)
    return Settings(**values)


def must_reject(message: str, **overrides) -> None:
    try:
        make_valid_production(**overrides)
    except Exception as exc:
        # Guardrails may surface as Pydantic ValidationError. Ensure it does not echo our known test secrets.
        diagnostic = str(exc)
        require(
            "qP8vR2mX7kN4wY9t" not in diagnostic
            and "K7wN9pQ2xR5vT8mY4zB6cD1fG3hJ0kL7sA9uV2eX5rP8nM4q" not in diagnostic,
            message,
        )
    else:
        raise AssertionError(f"Expected invalid production settings to be rejected: {message}")


def main() -> None:
    development = Settings(
        _env_file=None,
        app_env="development",
        database_url=None,
        jwt_secret="development-only-test-secret",
        cookie_secure=False,
        frontend_origins="http://localhost:5173",
        preview_draft_courses=True,
    )
    require(
        development.app_env == "development" and not development.cookie_secure,
        "valid local development settings remain usable without a database",
    )
    valid = make_valid_production()
    require(valid.app_env == "production" and valid.cookie_secure, "valid secure production settings are accepted")
    must_reject("placeholder JWT secret is rejected", jwt_secret="replace-with-a-long-random-secret-before-running-auth")
    must_reject("short JWT secret is rejected", jwt_secret="too-short")
    must_reject("repeated-character JWT secret is rejected", jwt_secret="x" * 48)
    must_reject("test-only JWT secret is rejected in production", jwt_secret="phase1-test-only-secret-" + ("x" * 48))
    must_reject("missing PostgreSQL URL is rejected", database_url=None)
    must_reject("non-PostgreSQL production database is rejected", database_url="sqlite:///local.db")
    must_reject("insecure production cookie setting is rejected", cookie_secure=False)
    must_reject("localhost frontend origins are rejected", frontend_origins="http://localhost:5173")
    must_reject("frontend origin paths are rejected", frontend_origins="https://codeleaf.vercel.app/api")
    must_reject("credentialed frontend origins are rejected", frontend_origins="https://user:password@codeleaf.vercel.app")
    must_reject("production PostgreSQL localhost URL is rejected", database_url="postgresql+psycopg://user:pass@localhost:5432/codeleaf")
    must_reject("production PostgreSQL URL without database name is rejected", database_url="postgresql+psycopg://user:pass@db.example.net/")
    must_reject("placeholder PostgreSQL host is rejected", database_url="postgresql+psycopg://user:good-password@db.example.net/codeleaf")
    must_reject("placeholder PostgreSQL password is rejected", database_url="postgresql+psycopg://user:example-password@ep-phase1-test.neon.tech/codeleaf")
    must_reject("missing PostgreSQL credentials are rejected", database_url="postgresql+psycopg://ep-phase1-test.neon.tech/codeleaf")
    must_reject("draft-preview mode is rejected in production", preview_draft_courses=True)
    must_reject("test email mode is rejected in production", email_test_mode=True)
    must_reject("missing mail service is rejected in production", smtp_host=None)
    must_reject("missing SMTP username is rejected in production", smtp_username=None)
    must_reject("missing SMTP password is rejected in production", smtp_password=None)
    must_reject("insecure frontend base URL is rejected in production", frontend_base_url="http://codeleaf.vercel.app")
    must_reject("frontend action-link origin must be allow-listed", frontend_base_url="https://another-codeleaf.vercel.app")
    must_reject("placeholder mail host is rejected in production", smtp_host="smtp.example.net")
    must_reject("unencrypted SMTP relay is rejected in production", smtp_use_tls=False)
    print("All Phase 1 production configuration tests passed.")


if __name__ == "__main__":
    main()
