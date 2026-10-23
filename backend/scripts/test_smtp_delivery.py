"""Mocked SMTP transport tests; no network connection or real email is sent."""
from __future__ import annotations

import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import auth_security  # noqa: E402
from app.config import settings  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


class FakeSMTP:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.commands: list[tuple] = []
        self.message = None
        self.send_error = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def ehlo(self):
        self.commands.append(("ehlo",))

    def starttls(self):
        self.commands.append(("starttls",))

    def login(self, username, password):
        self.commands.append(("login", username, password))

    def send_message(self, message):
        self.message = message
        if self.send_error:
            raise self.send_error
        return {}


def main() -> None:
    names = (
        "app_env", "email_test_mode", "email_from", "smtp_host", "smtp_port",
        "smtp_username", "smtp_password", "smtp_use_tls", "smtp_timeout_seconds",
    )
    previous = {name: getattr(settings, name) for name in names}
    try:
        settings.app_env = "development"
        settings.email_test_mode = False
        settings.email_from = "CodeLeaf Tests <test@example.org>"
        settings.smtp_host = "smtp.example.org"
        settings.smtp_port = 587
        settings.smtp_username = "test@example.org"
        settings.smtp_password = "not-a-real-secret"
        settings.smtp_use_tls = True
        settings.smtp_timeout_seconds = 10

        fake = FakeSMTP()
        with patch.object(auth_security.smtplib, "SMTP", return_value=fake) as smtp_factory:
            result = auth_security.send_action_email(
                "learner@example.org", "Verify your CodeLeaf email", "Verify your account",
                "http://localhost:5173/verify-email?token=fake-token", "Verify email", "in 24 hours",
            )
        require(result == {"delivery_mode": "email"}, "successful SMTP send returns email delivery mode")
        smtp_factory.assert_called_once_with("smtp.example.org", 587, timeout=10)
        require(("starttls",) in fake.commands, "STARTTLS is enabled for port 587")
        require(("login", "test@example.org", "not-a-real-secret") in fake.commands, "SMTP credentials are used")
        require(fake.message is not None and fake.message.is_multipart(), "email contains plain-text and HTML alternatives")
        require("fake-token" in fake.message.get_body(preferencelist=("plain",)).get_content(), "plain-text email contains the action link")
        require("Verify email" in fake.message.get_body(preferencelist=("html",)).get_content(), "HTML email contains a clickable action")

        settings.smtp_host = "smtp.gmail.com"
        settings.smtp_password = "abcd efgh ijkl mnop"
        gmail_fake = FakeSMTP()
        with patch.object(auth_security.smtplib, "SMTP", return_value=gmail_fake):
            auth_security.send_smtp_message(EmailMessage())
        require(("login", "test@example.org", "abcdefghijklmnop") in gmail_fake.commands, "Gmail app-password display spaces are normalized safely")
        settings.smtp_host = "smtp.example.org"
        settings.smtp_password = "not-a-real-secret"

        failed = FakeSMTP()
        failed.send_error = smtplib.SMTPAuthenticationError(535, b"authentication rejected")
        with patch.object(auth_security.smtplib, "SMTP", return_value=failed):
            result = auth_security.send_action_email(
                "learner@example.org", "Reset your CodeLeaf password", "Reset your password",
                "http://localhost:5173/reset-password?token=fake-token", "Reset password", "in 30 minutes",
            )
        require(result == {"delivery_mode": "not_confirmed"}, "SMTP authentication errors are not misreported as successful delivery")

        settings.smtp_password = None
        require("SMTP_PASSWORD" in auth_security.smtp_configuration_problems(), "missing SMTP password is detected")
        require("SMTP_USERNAME" not in auth_security.smtp_configuration_problems(), "configured SMTP username remains valid")

        settings.smtp_password = "not-a-real-secret"
        settings.smtp_port = 465
        secure = FakeSMTP()
        with patch.object(auth_security.smtplib, "SMTP_SSL", return_value=secure) as ssl_factory:
            auth_security.send_smtp_message(EmailMessage())
        ssl_factory.assert_called_once_with("smtp.example.org", 465, timeout=10)
        require(("starttls",) not in secure.commands and ("ehlo",) in secure.commands, "port 465 uses implicit TLS rather than STARTTLS")
    finally:
        for name, value in previous.items():
            setattr(settings, name, value)

    print("All SMTP delivery tests passed.")


if __name__ == "__main__":
    main()
