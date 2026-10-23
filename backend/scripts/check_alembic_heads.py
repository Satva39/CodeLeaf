"""Fail when migrations contain multiple heads or no history."""
from __future__ import annotations

import sys
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND_ROOT = Path(__file__).resolve().parents[1]
config = Config(str(BACKEND_ROOT / "alembic.ini"))
config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
script = ScriptDirectory.from_config(config)
heads = script.get_heads()
if len(heads) != 1:
    print(f"FAIL: expected exactly one Alembic head, found {heads!r}", file=sys.stderr)
    raise SystemExit(1)
revisions = list(script.walk_revisions())
if not revisions:
    print("FAIL: no Alembic revisions were found", file=sys.stderr)
    raise SystemExit(1)
print(f"PASS: {len(revisions)} Alembic revisions; single head {heads[0]}")
