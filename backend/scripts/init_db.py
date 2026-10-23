"""Development-only helper: create starter tables and seed the public course catalog.

For production, create and apply a reviewed Alembic migration instead of running create_all().
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from app.config import settings
from app.db import Base, SessionLocal, engine
from app.models import Course
from app.main import PUBLIC_COURSES


def main() -> None:
    if engine is None or SessionLocal is None:
        raise SystemExit("DATABASE_URL is blank. Set it in backend/.env before initializing PostgreSQL.")
    if settings.app_env.lower() == "production":
        raise SystemExit("This helper uses create_all() and is development-only. Use a reviewed Alembic migration in production.")
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for index, item in enumerate(PUBLIC_COURSES):
            row = db.scalar(select(Course).where(Course.slug == item["slug"]))
            if row is None:
                row = Course(slug=item["slug"], title=item["title"], description=item["description"], category=item["category"], level=item["level"], published=False, sort_order=index)
                db.add(row)
            else:
                row.title = item["title"]
                row.description = item["description"]
                row.category = item["category"]
                row.level = item["level"]
                row.sort_order = index
        db.commit()
    print(f"Initialized development schema and {len(PUBLIC_COURSES)} catalog entries.")
    print("Note: course/module/lesson content must be imported from approved curriculum manifests before publishing.")


if __name__ == "__main__":
    main()
