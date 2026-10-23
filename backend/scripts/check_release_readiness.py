"""Run read-only local release checks without overstating external verification.

Run from backend/:
  python scripts/check_release_readiness.py
  python scripts/check_release_readiness.py --production
  python scripts/check_release_readiness.py --production --require-payments
  python scripts/check_release_readiness.py --skip-content-validation

No publishing, database migration, or remote deployment is performed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(BACKEND_ROOT / "scripts"))

from alembic.config import Config  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", action="store_true", help="validate production security settings")
    parser.add_argument("--check-db", action="store_true", help="connect to the configured database and inspect required tables")
    parser.add_argument("--require-payments", action="store_true", help="require Razorpay environment fields to be present")
    parser.add_argument("--skip-content-validation", action="store_true", help="skip full read-only course manifest validation")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    settings = None

    try:
        from app.config import Settings
        settings = Settings(app_env="production") if args.production else Settings()
        print(f"PASS [required] configuration validated for {settings.app_env} mode (values hidden)")
    except Exception as exc:
        errors.append(f"configuration invalid ({type(exc).__name__}); inspect environment variable names and placeholders locally")

    try:
        config = Config(str(BACKEND_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
        heads = ScriptDirectory.from_config(config).get_heads()
        if len(heads) == 1:
            print(f"PASS [required] Alembic graph has one head ({heads[0]})")
        else:
            errors.append(f"Alembic graph has {len(heads)} heads: {heads!r}")
    except Exception as exc:
        errors.append(f"Alembic graph check failed ({type(exc).__name__})")

    frontend_root = PROJECT_ROOT / "frontend"
    vercel_config = frontend_root / "vercel.json"
    proxy = frontend_root / "api" / "proxy" / "[...path].js"
    if not vercel_config.is_file():
        errors.append("frontend/vercel.json is missing")
    else:
        try:
            data = json.loads(vercel_config.read_text(encoding="utf-8"))
            rewrites = data.get("rewrites", [])
            proxy_rewrite = any(
                item.get("source") == "/api/:path*" and item.get("destination") == "/api/proxy/:path*"
                for item in rewrites if isinstance(item, dict)
            )
            hardcoded_host = "your-codeleaf-api.onrender.com" in vercel_config.read_text(encoding="utf-8")
            if not proxy_rewrite:
                errors.append("Vercel config does not route /api/* through the same-origin API proxy")
            elif not proxy.is_file():
                errors.append("frontend API proxy implementation is missing")
            elif hardcoded_host:
                errors.append("Vercel config contains a hardcoded placeholder API host")
            else:
                print("PASS [required] Vercel API proxy route exists without a hardcoded deployment host")
        except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
            errors.append(f"Vercel proxy config is invalid ({type(exc).__name__})")

    if not args.skip_content_validation:
        try:
            from validate_course_manifests import validate_course_directory
            course_dirs = sorted(path.parent for path in (BACKEND_ROOT / "content" / "courses").glob("*/course.json"))
            counts = {"modules": 0, "lessons": 0, "exercises": 0, "projects": 0, "assessments": 0, "diagrams": 0}
            failures: list[str] = []
            for course_dir in course_dirs:
                try:
                    report = validate_course_directory(course_dir)
                    for key in counts:
                        counts[key] += getattr(report, key)
                except Exception as exc:
                    failures.append(f"{course_dir.name}: {exc}")
            if failures:
                errors.extend(f"course {failure}" for failure in failures[:100])
            print(f"Course content [required]: checked={len(course_dirs)}; passed={len(course_dirs) - len(failures)}; failed={len(failures)}; " + ", ".join(f"{key}={value}" for key, value in counts.items()))
            if not course_dirs:
                errors.append("no course manifests were found")
        except Exception as exc:
            errors.append(f"course validation could not run ({type(exc).__name__})")
    else:
        warnings.append("full course validation skipped by request")

    hygiene = subprocess.run(
        [sys.executable, str(BACKEND_ROOT / "scripts" / "check_repository_hygiene.py")],
        cwd=BACKEND_ROOT, capture_output=True, text=True, check=False,
    )
    if hygiene.returncode == 0:
        print("PASS [required] repository hygiene command completed")
        for line in hygiene.stdout.splitlines():
            if line.startswith("WARN:") or line.startswith("NOTE:"):
                warnings.append(line)
    else:
        errors.append("repository hygiene check failed; review check_repository_hygiene.py output locally")
        for line in (hygiene.stdout + "\n" + hygiene.stderr).splitlines()[-12:]:
            if line.strip():
                print("  " + line)

    if args.check_db:
        try:
            from sqlalchemy import inspect, text
            from app.db import engine
            if engine is None:
                raise RuntimeError("DATABASE_URL is not configured")
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                tables = set(inspect(connection).get_table_names())
            missing = sorted({"courses", "course_modules", "lessons", "exercises", "users"} - tables)
            if missing:
                errors.append("configured database is reachable but missing required tables: " + ", ".join(missing))
            else:
                print("PASS [optional] configured database is reachable and required tables exist")
        except Exception as exc:
            errors.append(f"database check failed ({type(exc).__name__}); inspect local connection settings privately")
    else:
        warnings.append("database connectivity/schema not checked (use --check-db only when you intend to connect to the configured database)")

    if args.require_payments:
        if settings is None:
            errors.append("payment configuration cannot be checked until base settings are valid")
        else:
            fields = (
                settings.razorpay_key_id, settings.razorpay_key_secret,
                settings.razorpay_webhook_secret, settings.razorpay_pro_plan_id,
                settings.razorpay_max_plan_id,
            )
            if all(value and value.strip() for value in fields):
                print("PASS [optional] required Razorpay configuration values are present (values hidden)")
            else:
                errors.append("one or more required Razorpay configuration values are missing")
    else:
        warnings.append("Razorpay fields were not required; no payment-provider requests were made")

    print("\nEXTERNALLY UNVERIFIED: live Razorpay transactions/webhooks, Vercel and Render deployment health, Vercel's CODELEAF_API_ORIGIN setting, remote PostgreSQL availability/backups, and production secrets were not verified by this local script.")
    for warning in warnings:
        print(warning if warning.startswith(("WARN:", "NOTE:")) else f"WARN: {warning}")
    if errors:
        print(f"\nBLOCKED: {len(errors)} required check(s) failed:")
        for error in errors[:100]:
            print(" -", error)
        return 1
    print("\nPASS: local readiness checks passed. This does not establish production or provider readiness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
