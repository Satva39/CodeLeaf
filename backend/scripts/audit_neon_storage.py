"""Read-only PostgreSQL storage audit for CodeLeaf.

Run from backend/ with the intended DATABASE_URL in the environment or backend/.env.
This script never updates or deletes database records.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import LargeBinary, text
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import engine  # noqa: E402


def run_audit() -> dict:
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured. Set it in backend/.env first.")

    report: dict = {"database": {}, "tables": [], "large_binary_columns": [], "portfolio_archives": {}}
    preparer = engine.dialect.identifier_preparer
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        report["database"]["name"] = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()
        report["database"]["size_bytes"] = int(
            connection.execute(
                text("SELECT pg_database_size(current_database())")
            ).scalar_one()
        )

        inspector = __import__("sqlalchemy").inspect(connection)
        table_names = sorted(
            name for name in inspector.get_table_names() if not name.startswith("pg_")
        )
        for table_name in table_names:
            relation = connection.execute(
                text(
                    "SELECT pg_total_relation_size(to_regclass(:name)), "
                    "pg_table_size(to_regclass(:name)), "
                    "pg_indexes_size(to_regclass(:name))"
                ),
                {"name": table_name},
            ).one()
            report["tables"].append(
                {
                    "table": table_name,
                    "total_bytes": int(relation[0] or 0),
                    "table_bytes": int(relation[1] or 0),
                    "index_bytes": int(relation[2] or 0),
                }
            )

            for column in inspector.get_columns(table_name):
                column_type = column["type"]
                if not isinstance(column_type, LargeBinary):
                    continue
                q_table = preparer.quote(table_name)
                q_column = preparer.quote(column["name"])
                row = connection.execute(
                    text(
                        f"SELECT COUNT(*) FILTER (WHERE {q_column} IS NOT NULL), "
                        f"COALESCE(SUM(octet_length({q_column})), 0) FROM {q_table}"
                    )
                ).one()
                report["large_binary_columns"].append(
                    {
                        "table": table_name,
                        "column": column["name"],
                        "non_null_rows": int(row[0] or 0),
                        "payload_bytes": int(row[1] or 0),
                    }
                )

        table_set = set(table_names)
        if {"project_submissions", "project_submission_zip_chunks"}.issubset(table_set):
            inline = connection.execute(
                text(
                    "SELECT COUNT(*) FILTER (WHERE zip_bundle IS NOT NULL), "
                    "COALESCE(SUM(octet_length(zip_bundle)), 0) "
                    "FROM project_submissions"
                )
            ).one()
            chunks = connection.execute(
                text(
                    "SELECT COUNT(*), COALESCE(SUM(octet_length(payload)), 0) "
                    "FROM project_submission_zip_chunks"
                )
            ).one()
            archive_rows = connection.execute(
                text(
                    "SELECT ps.id::text, ps.zip_filename, COALESCE(ps.stored_bytes, 0) AS stored_bytes, "
                    "COALESCE(o.chunk_count, 0) AS chunk_count, "
                    "COALESCE(o.chunk_bytes, 0) AS chunk_bytes, "
                    "COALESCE(octet_length(ps.zip_bundle), 0) AS inline_bytes, "
                    "ps.storage_provider, ps.object_status "
                    "FROM project_submissions ps LEFT JOIN ("
                    "SELECT submission_id, COUNT(*) AS chunk_count, "
                    "SUM(octet_length(payload)) AS chunk_bytes "
                    "FROM project_submission_zip_chunks GROUP BY submission_id"
                    ") o ON o.submission_id = ps.id "
                    "WHERE ps.zip_bundle IS NOT NULL OR COALESCE(o.chunk_count, 0) > 0 "
                    "ORDER BY (COALESCE(o.chunk_bytes, 0) + COALESCE(octet_length(ps.zip_bundle), 0)) DESC "
                    "LIMIT 20"
                )
            ).mappings().all()
            count_row = connection.execute(
                text(
                    "SELECT COUNT(DISTINCT ps.id) FROM project_submissions ps "
                    "LEFT JOIN project_submission_zip_chunks c ON c.submission_id = ps.id "
                    "WHERE ps.zip_bundle IS NOT NULL OR c.submission_id IS NOT NULL"
                )
            ).scalar_one()
            report["portfolio_archives"] = {
                "archives_with_inline_bytes": int(inline[0] or 0),
                "inline_payload_bytes": int(inline[1] or 0),
                "chunk_rows": int(chunks[0] or 0),
                "chunk_payload_bytes": int(chunks[1] or 0),
                "archives_with_legacy_payload": int(count_row or 0),
                "largest_archives": [dict(row) for row in archive_rows],
            }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Neon storage audit")
    parser.add_argument("--json", action="store_true", help="print the complete report as JSON")
    args = parser.parse_args()
    try:
        report = run_audit()
    except (RuntimeError, SQLAlchemyError) as exc:
        print(f"Storage audit failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, default=str))
        return 0

    db = report["database"]
    print(f"Database: {db['name']} ({db['size_bytes']:,} bytes)")
    print("\nLargest relations (table + indexes):")
    for item in sorted(report["tables"], key=lambda row: row["total_bytes"], reverse=True)[:20]:
        print(
            f"  {item['table']:<42} total={item['total_bytes']:>14,} "
            f"table={item['table_bytes']:>14,} indexes={item['index_bytes']:>14,}"
        )
    print("\nLargeBinary columns:")
    for item in report["large_binary_columns"]:
        print(
            f"  {item['table']}.{item['column']}: {item['non_null_rows']:,} rows, "
            f"{item['payload_bytes']:,} payload bytes"
        )
    archives = report.get("portfolio_archives", {})
    if archives:
        print("\nPortfolio archive payloads:")
        for key, value in archives.items():
            if key != "largest_archives":
                print(f"  {key}: {value:,}")
        print("\nLargest 20 archive records:")
        for item in archives["largest_archives"]:
            size = item["inline_bytes"] + item["chunk_bytes"]
            print(f"  {item['id']}  {size:,} bytes  {item['zip_filename'] or '(unnamed)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
