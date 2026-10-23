"""Send a real diagnostic email using CodeLeaf's configured SMTP transport.

Run from backend/: python scripts/test_smtp.py --to your-inbox@example.com
This sends one email and does not change the database or account state.
"""
from __future__ import annotations

import argparse
import smtplib
import sys
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth_security import send_smtp_message, smtp_configuration_problems  # noqa: E402
from app.config import settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--to", required=True, help="An inbox you can check")
    args = parser.parse_args()

    if settings.email_test_mode and settings.app_env.strip().lower() not in {"production", "prod"}:
        print("FAIL: EMAIL_TEST_MODE=true disables real email delivery. Set it to false and restart the backend.")
        return 2

    problems = smtp_configuration_problems()
    if problems:
        print("FAIL: Missing or unsafe SMTP settings: " + ", ".join(problems))
        print("Check backend/.env. Do not paste its secret values into logs or chat.")
        return 2

    message = EmailMessage()
    message["Subject"] = "CodeLeaf SMTP delivery test"
    message["From"] = settings.email_from.strip()
    message["To"] = args.to
    message["Date"] = formatdate(localtime=True)
    message.set_content(
        "This is a diagnostic message from CodeLeaf. If you received it, the configured SMTP server accepted and delivered this test message.\n\n"
        "Next, test account registration, verification, password reset, and email change flows."
    )
    message.add_alternative(
        "<!doctype html><html><body style=\"font-family:Arial,sans-serif;line-height:1.6\">"
        "<h2>CodeLeaf SMTP delivery test</h2><p>If you received this message, the configured SMTP transport accepted this test email.</p>"
        "<p>Next, test account registration, verification, password reset, and email change flows.</p></body></html>",
        subtype="html",
    )
    try:
        send_smtp_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        print(f"FAIL: SMTP authentication was rejected (status {exc.smtp_code}). Check SMTP_USERNAME and the provider-specific app password/API credential.")
        return 1
    except smtplib.SMTPResponseException as exc:
        print(f"FAIL: SMTP server rejected the message (status {exc.smtp_code}). Check the sender address and provider mail-sending policy.")
        return 1
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        print(f"FAIL: SMTP delivery did not complete ({type(exc).__name__}). Check hostname, port, TLS settings, network access, and backend logs.")
        return 1

    print("PASS: the SMTP server accepted the diagnostic message for delivery.")
    print("Check the destination inbox and spam/quarantine folders. Then test the CodeLeaf account flows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
