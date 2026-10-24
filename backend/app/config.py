from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET_VALUES = {
    "replace-with-a-long-random-secret-before-running-auth",
    "change-me",
    "changeme",
    "secret",
    "secret-key",
    "development-secret",
    "dev-secret",
}


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "CodeLeaf API"
    api_prefix: str = "/api"
    frontend_origins: str = "http://localhost:5173"
    database_url: str | None = None
    # Explicit local-only preview toggle for course content that is still in draft.
    # This remains disabled unless PREVIEW_DRAFT_COURSES=true is set locally.
    preview_draft_courses: bool = False
    jwt_secret: str = "replace-with-a-long-random-secret-before-running-auth"
    jwt_ttl_seconds: int = Field(default=86_400, gt=0, le=7_776_000)
    cookie_secure: bool = False
    frontend_base_url: str = "http://localhost:5173"
    email_test_mode: bool = False
    email_from: str | None = None
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_timeout_seconds: int = Field(default=10, ge=3, le=60)
    auth_rate_limit_window_seconds: int = Field(default=900, ge=60, le=86400)
    auth_rate_limit_max_attempts: int = Field(default=8, ge=3, le=100)
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    razorpay_pro_plan_id: str | None = None
    razorpay_max_plan_id: str | None = None
    razorpay_subscription_total_count: int = Field(default=1200, gt=0)
    # Optional URL for the isolated runner control plane. The main API never executes learner code.
    runner_service_url: str | None = None
    runner_service_token: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def sqlalchemy_database_url(self) -> str | None:
        url = self.database_url
        if not url:
            return None
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.frontend_origins.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Fail closed when deployed with insecure or incomplete production settings."""
        if self.app_env.strip().lower() not in {"production", "prod"}:
            return self

        problems: list[str] = []
        secret = self.jwt_secret.strip()
        if (
            len(secret) < 32
            or secret.lower() in _INSECURE_SECRET_VALUES
            or len(set(secret)) < 8
            or any(
                marker in secret.lower()
                for marker in (
                    "replace-with", "change-me", "your-secret", "not-for-deployment",
                    "test-only", "development-only", "dev-only", "ci-only",
                    "placeholder", "example-secret",
                )
            )
        ):
            problems.append(
                "JWT_SECRET must be a unique random value of at least 32 characters"
            )

        db_url = (self.sqlalchemy_database_url or "").strip()
        if not db_url:
            problems.append("DATABASE_URL is required")
        elif not db_url.startswith("postgresql+psycopg://"):
            problems.append(
                "DATABASE_URL must point to PostgreSQL using the psycopg driver"
            )
        else:
            parsed_db = urlsplit(db_url)
            if not parsed_db.hostname or not parsed_db.path.strip("/"):
                problems.append(
                    "DATABASE_URL must include a database host and database name"
                )
            else:
                hostname = parsed_db.hostname.lower()
                database_name = parsed_db.path.strip("/").lower()
                password = parsed_db.password or ""
                if hostname in {"localhost", "127.0.0.1", "::1"}:
                    problems.append("production DATABASE_URL must not point to localhost")
                if any(marker in hostname for marker in ("example", "placeholder", "your-host")):
                    problems.append("production DATABASE_URL must not use a placeholder host")
                if database_name in {"dbname", "database", "your_database", "your-db", "example"}:
                    problems.append("production DATABASE_URL must use a real database name")
                if not parsed_db.username or not password:
                    problems.append("production DATABASE_URL must include database username and password")
                elif password.lower() in {
                    "password", "example", "example-password", "changeme", "change-me",
                    "replace-me", "your-password", "dev_only_password_change_me", "postgres",
                } or any(marker in password.lower() for marker in ("replace-with", "placeholder", "your-password")):
                    problems.append("production DATABASE_URL must not use placeholder credentials")

        if not self.cookie_secure:
            problems.append("COOKIE_SECURE must be true in production")
        if self.email_test_mode:
            problems.append("EMAIL_TEST_MODE must be false in production")
        if not self.smtp_host or not self.email_from:
            problems.append("SMTP_HOST and EMAIL_FROM are required in production for account email")
        if not self.smtp_username or not self.smtp_password:
            problems.append("SMTP_USERNAME and SMTP_PASSWORD are required for authenticated SMTP delivery")
        if self.smtp_host and (
            self.smtp_host.strip().lower() in {"localhost", "127.0.0.1", "example.com", "example.net", "example.org"}
            or any(marker in self.smtp_host.strip().lower() for marker in ("placeholder", "your-host", "example"))
        ):
            problems.append("SMTP_HOST must be a real mail service host in production")
        if self.email_from and ("@" not in self.email_from or any(marker in self.email_from.lower() for marker in ("example.com", "example.net", "example.org", "placeholder"))):
            problems.append("EMAIL_FROM must be a real sender address in production")
        if self.smtp_port != 465 and not self.smtp_use_tls:
            problems.append("SMTP_USE_TLS must be true unless SMTP_PORT is 465")
        frontend_url = urlsplit(self.frontend_base_url.strip())
        if (frontend_url.scheme != "https" or not frontend_url.netloc or frontend_url.path not in {"", "/"}
                or frontend_url.query or frontend_url.fragment or frontend_url.username is not None
                or frontend_url.password is not None):
            problems.append("FRONTEND_BASE_URL must be a real HTTPS frontend origin in production")
        elif self.frontend_base_url.strip().rstrip("/") not in self.allowed_origins:
            problems.append("FRONTEND_BASE_URL must match one of FRONTEND_ORIGINS in production")
        if self.preview_draft_courses:
            problems.append("PREVIEW_DRAFT_COURSES must be false in production")

        origins = self.allowed_origins
        if not origins:
            problems.append(
                "FRONTEND_ORIGINS must contain at least one deployed HTTPS origin"
            )
        for origin in origins:
            parsed_origin = urlsplit(origin)
            if (
                parsed_origin.scheme != "https"
                or not parsed_origin.netloc
                or parsed_origin.path not in {"", "/"}
                or parsed_origin.query
                or parsed_origin.fragment
                or parsed_origin.hostname is None
                or parsed_origin.username is not None
                or parsed_origin.password is not None
                or parsed_origin.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
                or "example.com" in parsed_origin.hostname.lower()
                or "your-codeleaf" in parsed_origin.hostname.lower()
            ):
                problems.append(
                    "FRONTEND_ORIGINS must contain only real HTTPS origins (no paths or local hosts)"
                )
                break

        if problems:
            # Deliberately never include the values themselves in the exception.
            raise ValueError("Invalid production configuration: " + "; ".join(problems))
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
