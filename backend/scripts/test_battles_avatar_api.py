"""Battle and dog-avatar API checks using a private temporary SQLite database.

Run from backend/: python scripts/test_battles_avatar_api.py
Runner execution is mocked at the internal adapter boundary; no real code is run.
"""
from __future__ import annotations
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

_TEMP = tempfile.TemporaryDirectory(prefix="codeleaf-battles-avatar-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_TEMP.name) / 'battles.db').as_posix()}"
os.environ["JWT_SECRET"] = "battles-avatar-test-secret-not-for-deployment"
os.environ["APP_ENV"] = "test"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jwt  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select, func, event  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.auth_security import token_digest  # noqa: E402
from app.models import AuthSession, CodingBattle, User, UserAchievement, UserAvatarInventory, UserAvatarProfile, XPTransaction  # noqa: E402
from app.main import TOKEN_ALGORITHM, app, get_leaderboard  # noqa: E402
import app.main as main_module  # noqa: E402
import app.games_routes as games_routes  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def make_user(suffix: str) -> User:
    with SessionLocal() as db:
        user = User(
            email=f"{suffix}-{uuid4().hex[:8]}@example.invalid",
            username=f"{suffix}_{uuid4().hex[:12]}",
            display_name=f"{suffix.title()} Learner",
            password_hash="test-only-hash",
            is_email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def client_for(user: User) -> TestClient:
    token = jwt.encode(
        {"sub": str(user.id), "iat": int(datetime.now(timezone.utc).timestamp()), "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
        settings.jwt_secret,
        algorithm=TOKEN_ALGORITHM,
    )
    with SessionLocal() as db:
        db.add(AuthSession(token_hash=token_digest(token), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
        db.commit()
    client = TestClient(app)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


async def fake_available_languages() -> set[str]:
    return {"python", "javascript"}


async def fake_battle_provider(language: str) -> str:
    # Keep this legacy Runner-path regression independent of external providers.
    return "codeleaf-runner"


async def fake_run_test_case(*, db, user, language, source_code, stdin, expected_output, idempotency_key):
    # The route must invoke every hidden case; `pass` is accepted, other code is rejected.
    return source_code == "pass", ("Test passed." if source_code == "pass" else "The program output did not match."), True


def main() -> None:
    Base.metadata.create_all(bind=engine)
    original_available = games_routes._available_battle_languages
    original_test_runner = games_routes._run_test_case
    original_battle_provider = games_routes._battle_provider_for_language
    original_require_feature = main_module.require_feature
    main_module.require_feature = lambda db, user, feature: None
    games_routes._available_battle_languages = fake_available_languages
    games_routes._battle_provider_for_language = fake_battle_provider
    games_routes._run_test_case = fake_run_test_case
    user_a = make_user("battle_a")
    user_b = make_user("battle_b")
    user_c = make_user("battle_c")
    client_a = client_for(user_a)
    client_b = client_for(user_b)
    client_c = client_for(user_c)
    try:
        challenges = client_a.get("/api/battles/challenges?language=python")
        check(challenges.status_code == 200 and challenges.json()["challenges"], "challenge catalogue is available for Runner-supported languages")
        check(all("hidden" not in challenge for challenge in challenges.json()["challenges"]), "hidden challenge cases are never sent to the frontend")

        waiting = client_a.post("/api/battles/matchmake", json={"language": "python", "difficulty": "easy"})
        check(waiting.status_code == 201 and waiting.json()["battle"]["status"] == "waiting", "first learner creates a waiting-room battle")
        battle_id = waiting.json()["battle"]["id"]
        current = client_a.get("/api/me/battles/current")
        check(current.status_code == 200 and current.json()["battle"]["id"] == battle_id, "current waiting battle can be restored after page refresh")
        check("hidden" not in current.text, "waiting battle response keeps hidden test data private")

        joined = client_b.post("/api/battles/matchmake", json={"language": "python", "difficulty": "easy"})
        check(joined.status_code == 201 and joined.json()["battle"]["status"] == "active", "second learner joins the same matchmaking queue")
        check(joined.json()["battle"]["id"] == battle_id, "both participants receive the same battle ID")
        check(joined.json()["battle"]["challenge"]["id"] == waiting.json()["battle"]["challenge"]["id"], "both participants receive the identical coding challenge")
        check(waiting.json()["battle"]["my_avatar"] is not None and joined.json()["battle"]["opponent"]["dog_avatar"] is not None, "both battle participants receive persistent dog avatars")
        check(client_c.get(f"/api/battles/{battle_id}").status_code == 404, "a third account cannot read another battle")

        wrong = client_b.post(f"/api/battles/{battle_id}/submit", json={"source_code": "wrong", "request_key": "wrong-attempt-001"})
        check(wrong.status_code == 200 and wrong.json()["submission"]["status"] == "rejected" and wrong.json()["submission"]["passed"] is False, "incorrect solution is rejected and cannot win")
        accepted = client_a.post(f"/api/battles/{battle_id}/submit", json={"source_code": "pass", "request_key": "accepted-attempt-001"})
        check(accepted.status_code == 200 and accepted.json()["submission"]["status"] == "accepted", "fully correct hidden-test evaluation is accepted")
        result = accepted.json()["battle"]
        check(result["status"] == "completed" and result["winner_id"] == str(user_a.id) and result["you_won"], "server records the accepted participant as the single winner")
        repeat = client_a.post(f"/api/battles/{battle_id}/submit", json={"source_code": "pass", "request_key": "accepted-attempt-001"})
        check(repeat.status_code == 200 and repeat.json()["submission"]["status"] == "accepted", "retrying the same request key returns the original submission")
        loser_view = client_b.get(f"/api/battles/{battle_id}")
        check(loser_view.status_code == 200 and loser_view.json()["battle"]["you_won"] is False, "opponent receives the authoritative defeated result")
        late = client_b.post(f"/api/battles/{battle_id}/submit", json={"source_code": "pass", "request_key": "late-attempt-001"})
        check(late.status_code == 409, "a second winner cannot be recorded after battle completion")

        with SessionLocal() as db:
            win_xp = db.scalars(select(XPTransaction).where(XPTransaction.user_id == user_a.id, XPTransaction.source_type == "battle_win", XPTransaction.source_id == battle_id)).all()
            achievement = db.scalar(select(UserAchievement).where(UserAchievement.user_id == user_a.id, UserAchievement.achievement_id == "first-battle-win"))
            item = db.scalar(select(UserAvatarInventory).where(UserAvatarInventory.user_id == user_a.id, UserAvatarInventory.item_id == "battle-champion-cap"))
            check(len(win_xp) == 1 and win_xp[0].awarded_points == 10, "battle winner receives exactly one 10 XP reward")
            check(achievement is not None and item is not None, "first battle win unlocks its designated avatar cosmetic")
            total_battle_awards = db.scalar(select(func.count(XPTransaction.id)).where(XPTransaction.user_id == user_a.id, XPTransaction.source_type == "battle_win"))
            check(total_battle_awards == 1, "battle retry cannot duplicate XP")

        avatar_query_statements = []
        def count_avatar_queries(_conn, _cursor, statement, _parameters, _context, _executemany):
            if statement.lstrip().lower().startswith("select"):
                avatar_query_statements.append(statement)
        event.listen(engine, "before_cursor_execute", count_avatar_queries)
        avatar = client_a.get("/api/me/avatar")
        event.remove(engine, "before_cursor_execute", count_avatar_queries)
        check(avatar.status_code == 200 and len(avatar.json()["catalog"]) >= 30, "authenticated avatar API returns the 30+ item catalogue")
        check("classic-collar" in avatar.json()["owned_item_ids"], "new users receive the free starter collar")
        check(len(avatar_query_statements) <= 30, "avatar profile load uses a bounded query count instead of per-course achievement queries")
        denied = client_b.put("/api/me/avatar/equipment", json={"slot": "headwear", "item_id": "starter-cap"})
        check(denied.status_code == 403, "locked cosmetic cannot be equipped by another learner")
        collar_equipped = client_a.put("/api/me/avatar/equipment", json={"slot": "collar", "item_id": "classic-collar"})
        check(collar_equipped.status_code == 200 and collar_equipped.json()["equipment"]["collar"] == "classic-collar", "owned starter collar can be equipped")
        with SessionLocal() as db:
            db.add(UserAvatarInventory(user_id=user_a.id, item_id="blue-hoodie", acquired_via="test"))
            db.add(UserAvatarInventory(user_id=user_a.id, item_id="warrior-outfit", acquired_via="test"))
            db.commit()
        outfit_equipped = client_a.put("/api/me/avatar/equipment", json={"slot": "outfit", "item_id": "warrior-outfit"})
        check(outfit_equipped.status_code == 200 and outfit_equipped.json()["equipment"].get("outfit") == "warrior-outfit", "full outfit can be equipped")
        shirt_equipped = client_a.put("/api/me/avatar/equipment", json={"slot": "shirt", "item_id": "blue-hoodie"})
        check(shirt_equipped.status_code == 200 and shirt_equipped.json()["equipment"].get("shirt") == "blue-hoodie" and "outfit" not in shirt_equipped.json()["equipment"], "equipping a jacket clears an overlapping full outfit so the picture matches the selected item")
        outfit_re_equipped = client_a.put("/api/me/avatar/equipment", json={"slot": "outfit", "item_id": "warrior-outfit"})
        check(outfit_re_equipped.status_code == 200 and outfit_re_equipped.json()["equipment"].get("outfit") == "warrior-outfit" and "shirt" not in outfit_re_equipped.json()["equipment"], "equipping a full outfit clears an overlapping shirt")
        equipped = client_a.put("/api/me/avatar/equipment", json={"slot": "shirt", "item_id": "blue-hoodie"})
        check(equipped.status_code == 200 and equipped.json()["equipment"].get("shirt") == "blue-hoodie", "the selected jacket remains the single active clothing layer")
        appearance = client_a.patch("/api/me/avatar/appearance", json={"breed": "husky", "fur_color": "snow", "eye_color": "blue"})
        persisted = client_a.get("/api/me/avatar")
        check(appearance.status_code == 200 and persisted.json()["appearance"]["breed"] == "husky" and persisted.json()["equipment"]["collar"] == "classic-collar" and persisted.json()["equipment"]["shirt"] == "blue-hoodie", "appearance and equipment persist on the account")
        catalog_items = {item["id"]: item for item in persisted.json()["catalog"]}
        check(catalog_items["blue-hoodie"]["equipped"] is True and catalog_items["warrior-outfit"]["equipped"] is False, "catalog equipped labels match the actual visible clothing layer")

        with SessionLocal() as db:
            leaderboard = get_leaderboard(period="all_time", limit=20, user=user_a, db=db)
            ranked_self = next((item for item in leaderboard["items"] if item["username"] == user_a.username), None)
            check(ranked_self is not None and ranked_self["dog_avatar"]["appearance"]["breed"] == "husky", "leaderboard returns each learner's saved dog profile picture")
            check(ranked_self["dog_avatar"]["equipment"].get("collar") == "classic-collar", "leaderboard includes only the equipped dog cosmetic slots")
    finally:
        client_a.close(); client_b.close(); client_c.close()
        games_routes._available_battle_languages = original_available
        games_routes._battle_provider_for_language = original_battle_provider
        main_module.require_feature = original_require_feature
        games_routes._run_test_case = original_test_runner
        engine.dispose()
        _TEMP.cleanup()
    print("Battle and avatar API tests passed.")


if __name__ == "__main__":
    main()
