"""Authenticated dog-avatar and server-authoritative coding-battle APIs."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth_security import require_user
from .db import get_db
from .gamification import (
    ACHIEVEMENTS,
    XP_REWARDS,
    AVATAR_ITEMS,
    BREEDS,
    EYE_COLORS,
    FUR_COLORS,
    ITEM_BY_ID,
    ensure_avatar_records,
    evaluate_achievements,
)
from .models import (
    BattleSubmission,
    CodingBattle,
    User,
    UserAchievement,
    UserActivityDay,
    UserAvatarInventory,
    UserAvatarProfile,
    XPTransaction,
)
from .plan_entitlements import (
    effective_plan_id,
    finalize_daily_usage,
    plan_limits,
    reserve_daily_usage,
)
from .runner_client import RunnerServiceError, runner_request_json, runner_service_configured

router = APIRouter()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    """Normalize database datetimes (SQLite may drop timezone metadata)."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MatchmakeInput(StrictModel):
    language: Literal["python", "javascript"] = "python"
    difficulty: Literal["easy", "medium"] = "easy"


class BattleSubmissionInput(StrictModel):
    source_code: str = Field(min_length=1, max_length=16_000)
    request_key: str = Field(min_length=8, max_length=100)


class AvatarAppearanceInput(StrictModel):
    breed: Literal["classic", "shiba", "husky", "retriever", "corgi", "bulldog"]
    fur_color: Literal["golden", "cream", "chocolate", "charcoal", "snow", "copper"]
    eye_color: Literal["brown", "blue", "green", "amber"]


class AvatarEquipmentInput(StrictModel):
    slot: str = Field(min_length=2, max_length=24, pattern=r"^[a-z][a-z0-9_-]*$")
    item_id: str | None = Field(default=None, max_length=80)


# Input/output contract challenges are deliberately language-neutral. Each test is
# executed by the configured isolated Runner; hidden test data never leaves this API.
CHALLENGES: list[dict[str, Any]] = [
    {
        "id": "reverse-number", "title": "Reverse a Number", "difficulty": "easy",
        "description": "Read one integer and print its digits in reverse order. Do not preserve leading zeroes in the result. Negative values should keep their sign.",
        "input_format": "One integer n.", "output_format": "The reversed integer.",
        "constraints": "-1,000,000,000 ≤ n ≤ 1,000,000,000",
        "samples": [{"input": "1200\n", "output": "21"}],
        "hidden": [{"input": "-540\n", "output": "-45"}, {"input": "7\n", "output": "7"}, {"input": "100000\n", "output": "1"}],
    },
    {
        "id": "palindrome-number", "title": "Palindrome Number", "difficulty": "easy",
        "description": "Read one integer. Print YES when its decimal representation is a palindrome; otherwise print NO. Negative values are not palindromes.",
        "input_format": "One integer n.", "output_format": "YES or NO.",
        "constraints": "-1,000,000,000 ≤ n ≤ 1,000,000,000",
        "samples": [{"input": "121\n", "output": "YES"}],
        "hidden": [{"input": "-121\n", "output": "NO"}, {"input": "10\n", "output": "NO"}, {"input": "0\n", "output": "YES"}],
    },
    {
        "id": "factorial", "title": "Calculate Factorial", "difficulty": "easy",
        "description": "Read a non-negative integer n and print n factorial. Remember that 0! is 1.",
        "input_format": "One integer n.", "output_format": "One integer containing n!.",
        "constraints": "0 ≤ n ≤ 12",
        "samples": [{"input": "5\n", "output": "120"}],
        "hidden": [{"input": "0\n", "output": "1"}, {"input": "1\n", "output": "1"}, {"input": "10\n", "output": "3628800"}],
    },
    {
        "id": "largest-number", "title": "Find the Largest Number", "difficulty": "easy",
        "description": "Read n followed by n integers. Print the largest value.",
        "input_format": "First line: n. Second line: n space-separated integers.", "output_format": "The maximum integer.",
        "constraints": "1 ≤ n ≤ 100; -100,000 ≤ values ≤ 100,000",
        "samples": [{"input": "5\n1 7 3 9 2\n", "output": "9"}],
        "hidden": [{"input": "1\n-3\n", "output": "-3"}, {"input": "4\n-8 -2 -9 -4\n", "output": "-2"}, {"input": "3\n100 100 99\n", "output": "100"}],
    },
    {
        "id": "even-or-odd", "title": "Even or Odd", "difficulty": "easy",
        "description": "Read one integer and print EVEN if it is divisible by 2, otherwise print ODD.",
        "input_format": "One integer n.", "output_format": "EVEN or ODD.",
        "constraints": "-1,000,000 ≤ n ≤ 1,000,000",
        "samples": [{"input": "14\n", "output": "EVEN"}],
        "hidden": [{"input": "0\n", "output": "EVEN"}, {"input": "-3\n", "output": "ODD"}, {"input": "999999\n", "output": "ODD"}],
    },
    {
        "id": "sum-array", "title": "Sum Array Elements", "difficulty": "easy",
        "description": "Read n followed by n integers. Print the sum of all array elements.",
        "input_format": "First line: n. Second line: n space-separated integers.", "output_format": "One integer containing the sum.",
        "constraints": "1 ≤ n ≤ 1,000; -10,000 ≤ values ≤ 10,000",
        "samples": [{"input": "5\n1 2 3 4 5\n", "output": "15"}],
        "hidden": [{"input": "1\n-20\n", "output": "-20"}, {"input": "4\n0 0 0 0\n", "output": "0"}, {"input": "3\n100 -50 25\n", "output": "75"}],
    },
    {
        "id": "count-vowels", "title": "Count Vowels", "difficulty": "easy",
        "description": "Read one line of text and count the vowels a, e, i, o, u without distinguishing uppercase and lowercase.",
        "input_format": "One line of text.", "output_format": "One integer: the vowel count.",
        "constraints": "Line length ≤ 1,000 characters.",
        "samples": [{"input": "CodeLeaf Academy\n", "output": "6"}],
        "hidden": [{"input": "rhythm\n", "output": "0"}, {"input": "AEIOU\n", "output": "5"}, {"input": "Hello, World!\n", "output": "3"}],
    },
    {
        "id": "reverse-string", "title": "Reverse a String", "difficulty": "easy",
        "description": "Read one line of text and print the same characters in reverse order. Preserve spaces and punctuation.",
        "input_format": "One line of text.", "output_format": "The reversed line.",
        "constraints": "Line length ≤ 1,000 characters.",
        "samples": [{"input": "code leaf\n", "output": "fael edoc"}],
        "hidden": [{"input": "a\n", "output": "a"}, {"input": "hello!\n", "output": "!olleh"}, {"input": "two words\n", "output": "sdrow owt"}],
    },
    {
        "id": "prime-number", "title": "Check Prime Number", "difficulty": "medium",
        "description": "Read one integer and print PRIME if it is a prime number; otherwise print NOT PRIME.",
        "input_format": "One integer n.", "output_format": "PRIME or NOT PRIME.",
        "constraints": "-1,000,000 ≤ n ≤ 1,000,000",
        "samples": [{"input": "17\n", "output": "PRIME"}],
        "hidden": [{"input": "1\n", "output": "NOT PRIME"}, {"input": "2\n", "output": "PRIME"}, {"input": "49\n", "output": "NOT PRIME"}, {"input": "-7\n", "output": "NOT PRIME"}],
    },
    {
        "id": "fibonacci", "title": "Fibonacci Numbers", "difficulty": "medium",
        "description": "Read n and print the first n Fibonacci numbers starting with 0 and 1, separated by one space.",
        "input_format": "One integer n.", "output_format": "The first n terms on one line, separated by spaces. For n = 0, print an empty line.",
        "constraints": "0 ≤ n ≤ 40",
        "samples": [{"input": "6\n", "output": "0 1 1 2 3 5"}],
        "hidden": [{"input": "0\n", "output": ""}, {"input": "1\n", "output": "0"}, {"input": "2\n", "output": "0 1"}, {"input": "10\n", "output": "0 1 1 2 3 5 8 13 21 34"}],
    },
]
CHALLENGE_BY_ID = {item["id"]: item for item in CHALLENGES}


def _public_challenge(challenge: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in challenge.items() if key != "hidden"}


def _normalize_output(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


async def _available_battle_languages() -> set[str]:
    if not runner_service_configured():
        raise HTTPException(status_code=503, detail="Coding Battles require the configured isolated CodeLeaf Runner.")
    try:
        payload = await runner_request_json("GET", "/v1/languages")
    except RunnerServiceError as exc:
        raise HTTPException(status_code=503, detail="The isolated Runner language catalogue is unavailable. No code was executed.") from exc
    rows = payload.get("languages")
    if not isinstance(rows, list):
        raise HTTPException(status_code=503, detail="The Runner returned an invalid language catalogue.")
    return {
        str(row.get("key", "")).strip().lower()
        for row in rows
        if isinstance(row, dict) and row.get("available") is True
    }


async def _run_test_case(
    *, db: Session, user: User, language: str, source_code: str,
    stdin: str, expected_output: str, idempotency_key: str,
) -> tuple[bool, str, bool]:
    """Run one test through the same private Runner contract as normal code jobs.

    Returns (passed, safe_message, provider_accepted). Provider failures never count
    as a wrong answer and never produce a battle victory.
    """
    plan_id = effective_plan_id(db, user.id)
    reservation, duplicate = reserve_daily_usage(
        db, user, metric="code_execution",
        allowance=int(plan_limits(plan_id)["code_executions_per_day"]),
        idempotency_key=idempotency_key,
    )
    if duplicate:
        return False, "This evaluation request was already processed.", False
    try:
        accepted = await runner_request_json(
            "POST", "/v1/jobs", user_id=str(user.id),
            payload={"language": language, "version": "*", "stdin": stdin, "args": [], "source": source_code},
        )
        external_id = accepted.get("job_id")
        if not isinstance(external_id, str) or not external_id:
            finalize_daily_usage(db, reservation.id, success=False)
            return False, "Runner did not accept the execution request.", False
        finalize_daily_usage(db, reservation.id, success=True)
    except RunnerServiceError:
        finalize_daily_usage(db, reservation.id, success=False)
        return False, "The isolated Runner could not accept the submission. Please try again.", False
    except Exception:
        finalize_daily_usage(db, reservation.id, success=False)
        raise

    deadline = asyncio.get_running_loop().time() + 6.5
    last_status = "queued"
    result: dict[str, Any] = {}
    while asyncio.get_running_loop().time() < deadline:
        try:
            snapshot = await runner_request_json("GET", f"/v1/jobs/{external_id}", user_id=str(user.id))
        except RunnerServiceError:
            return False, "The Runner became unavailable while evaluating the solution.", True
        last_status = str(snapshot.get("status") or "queued").lower()
        raw_result = snapshot.get("result")
        result = raw_result if isinstance(raw_result, dict) else {}
        if last_status in {"completed", "failed", "timeout", "output_limit", "cancelled", "expired"}:
            break
        await asyncio.sleep(0.35)
    else:
        return False, "The Runner did not finish this test within the evaluation window.", True

    if last_status != "completed":
        message = str(result.get("error") or "The code did not finish successfully.")[:240]
        return False, message, True
    if int(result.get("exit_code", 1)) != 0:
        return False, "The program exited with an error. Check the terminal output.", True
    actual = _normalize_output(result.get("stdout", ""))
    expected = _normalize_output(expected_output)
    if actual != expected:
        return False, "The program ran, but its output did not match this test.", True
    return True, "Test passed.", True


def _battle_public_view(db: Session, battle: CodingBattle, user_id: UUID) -> dict[str, Any]:
    challenge = CHALLENGE_BY_ID.get(battle.challenge_id)
    other_id = battle.opponent_id if battle.challenger_id == user_id else battle.challenger_id
    opponent = db.get(User, other_id) if other_id else None
    my_avatar = db.get(UserAvatarProfile, user_id)
    opponent_avatar = db.get(UserAvatarProfile, other_id) if other_id else None
    submission_rows = db.scalars(select(BattleSubmission).where(
        BattleSubmission.battle_id == battle.id
    ).order_by(BattleSubmission.created_at.desc()).limit(20)).all()
    my_row = next((row for row in submission_rows if row.user_id == user_id), None)
    opponent_row = next((row for row in submission_rows if row.user_id == other_id), None) if other_id else None
    return {
        "id": str(battle.id),
        "status": battle.status,
        "language": battle.language,
        "difficulty": battle.difficulty,
        "challenge": _public_challenge(challenge) if challenge else None,
        "is_challenger": battle.challenger_id == user_id,
        "my_avatar": ({"breed": my_avatar.breed, "fur_color": my_avatar.fur_color, "eye_color": my_avatar.eye_color, "equipment": my_avatar.equipment or {}} if my_avatar else None),
        "opponent": ({"username": opponent.username, "display_name": opponent.display_name, "avatar": opponent.avatar or {}, "dog_avatar": ({"breed": opponent_avatar.breed, "fur_color": opponent_avatar.fur_color, "eye_color": opponent_avatar.eye_color, "equipment": opponent_avatar.equipment or {}} if opponent_avatar else None)} if opponent else None),
        "winner_id": str(battle.winner_id) if battle.winner_id else None,
        "you_won": battle.winner_id == user_id if battle.winner_id else None,
        "started_at": battle.started_at.isoformat() if battle.started_at else None,
        "expires_at": battle.expires_at.isoformat() if battle.expires_at else None,
        "finished_at": battle.finished_at.isoformat() if battle.finished_at else None,
        "my_submission": ({"status": my_row.status, "passed": my_row.passed, "result": my_row.result_summary} if my_row else None),
        "opponent_submission": ({"status": opponent_row.status, "passed": opponent_row.passed} if opponent_row else None),
        "winner_name": (db.get(User, battle.winner_id).display_name if battle.winner_id else None),
    }


@router.get("/api/battles/challenges")
async def battle_challenge_catalog(
    language: Literal["python", "javascript"] = "python",
    user: User = Depends(require_user),
) -> dict[str, Any]:
    available = await _available_battle_languages()
    if language not in available:
        raise HTTPException(status_code=503, detail=f"{language} is not currently installed on the isolated Runner.")
    return {"language": language, "challenges": [_public_challenge(item) for item in CHALLENGES]}


@router.post("/api/battles/matchmake", status_code=201)
async def battle_matchmake(
    body: MatchmakeInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    available = await _available_battle_languages()
    if body.language not in available:
        raise HTTPException(status_code=503, detail=f"{body.language} is not currently installed on the isolated Runner.")
    # Create the persistent dog profile before the learner enters a waiting room.
    ensure_avatar_records(db, user.id)
    db.commit()
    now = utc_now()
    existing = db.scalar(select(CodingBattle).where(
        CodingBattle.status.in_(["waiting", "active"]),
        ((CodingBattle.challenger_id == user.id) | (CodingBattle.opponent_id == user.id)),
    ).order_by(CodingBattle.created_at.desc()).limit(1))
    if existing is not None:
        if existing.status == "waiting" and now - as_utc(existing.created_at) > timedelta(minutes=3):
            existing.status = "expired"
            db.commit()
        else:
            return {"battle": _battle_public_view(db, existing, user.id), "message": "You already have an open battle."}

    queued = db.scalar(select(CodingBattle).where(
        CodingBattle.status == "waiting",
        CodingBattle.language == body.language,
        CodingBattle.difficulty == body.difficulty,
        CodingBattle.challenger_id != user.id,
        CodingBattle.created_at >= now - timedelta(minutes=3),
    ).order_by(CodingBattle.created_at.asc()).with_for_update(skip_locked=True).limit(1))
    if queued is not None:
        ensure_avatar_records(db, queued.challenger_id)
        queued.opponent_id = user.id
        queued.status = "active"
        queued.started_at = now
        queued.expires_at = now + timedelta(minutes=20)
        db.commit()
        db.refresh(queued)
        return {"battle": _battle_public_view(db, queued, user.id), "message": "Opponent found. The battle has started."}

    challenge_pool = [item for item in CHALLENGES if item["difficulty"] == body.difficulty]
    # Medium difficulty is optional; keep the queue viable while preserving identical challenge data.
    if not challenge_pool:
        challenge_pool = [item for item in CHALLENGES if item["difficulty"] == "easy"]
    challenge = challenge_pool[int(uuid4().int % len(challenge_pool))]
    battle = CodingBattle(
        challenger_id=user.id, language=body.language, difficulty=body.difficulty,
        challenge_id=challenge["id"], status="waiting", created_at=now,
    )
    db.add(battle)
    db.commit()
    db.refresh(battle)
    return {"battle": _battle_public_view(db, battle, user.id), "message": "Searching for an opponent. Keep this page open."}


@router.get("/api/me/battles/current")
def get_my_current_battle(
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return the current waiting/active battle so refreshes do not abandon a match."""
    now = utc_now()
    battle = db.scalar(select(CodingBattle).where(
        CodingBattle.status.in_(["waiting", "active"]),
        ((CodingBattle.challenger_id == user.id) | (CodingBattle.opponent_id == user.id)),
    ).order_by(CodingBattle.created_at.desc()).limit(1))
    if battle is None:
        return {"battle": None}
    if (battle.status == "waiting" and now - as_utc(battle.created_at) > timedelta(minutes=3)) or (battle.status == "active" and battle.expires_at and now >= as_utc(battle.expires_at)):
        battle.status = "expired"
        battle.finished_at = now
        db.commit()
        return {"battle": None}
    return {"battle": _battle_public_view(db, battle, user.id)}


@router.get("/api/battles/{battle_id}")
def get_battle(
    battle_id: UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    battle = db.get(CodingBattle, battle_id)
    if battle is None or user.id not in {battle.challenger_id, battle.opponent_id}:
        raise HTTPException(status_code=404, detail="Battle was not found.")
    now = utc_now()
    if battle.status == "waiting" and now - as_utc(battle.created_at) > timedelta(minutes=3):
        battle.status = "expired"
        battle.finished_at = now
        db.commit()
    elif battle.status == "active" and battle.expires_at and now >= as_utc(battle.expires_at):
        battle.status = "expired"
        battle.finished_at = now
        db.commit()
    return {"battle": _battle_public_view(db, battle, user.id)}


@router.post("/api/battles/{battle_id}/join")
def join_battle(
    battle_id: UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    battle = db.scalar(select(CodingBattle).where(CodingBattle.id == battle_id).with_for_update())
    if battle is None:
        raise HTTPException(status_code=404, detail="Battle was not found.")
    if battle.challenger_id == user.id:
        ensure_avatar_records(db, user.id)
        db.commit()
        return {"battle": _battle_public_view(db, battle, user.id)}
    existing = db.scalar(select(CodingBattle.id).where(
        CodingBattle.status.in_(["waiting", "active"]),
        ((CodingBattle.challenger_id == user.id) | (CodingBattle.opponent_id == user.id)),
        CodingBattle.id != battle.id,
    ).limit(1))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Leave your current battle before joining another one.")
    if battle.status != "waiting" or battle.opponent_id is not None:
        raise HTTPException(status_code=409, detail="This battle is no longer available.")
    if utc_now() - as_utc(battle.created_at) > timedelta(minutes=3):
        battle.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="This battle invitation has expired.")
    ensure_avatar_records(db, battle.challenger_id)
    ensure_avatar_records(db, user.id)
    battle.opponent_id = user.id
    battle.status = "active"
    battle.started_at = utc_now()
    battle.expires_at = battle.started_at + timedelta(minutes=20)
    db.commit()
    db.refresh(battle)
    return {"battle": _battle_public_view(db, battle, user.id), "message": "Battle joined."}


@router.post("/api/battles/{battle_id}/leave")
def leave_battle(
    battle_id: UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    battle = db.scalar(select(CodingBattle).where(CodingBattle.id == battle_id).with_for_update())
    if battle is None or user.id not in {battle.challenger_id, battle.opponent_id}:
        raise HTTPException(status_code=404, detail="Battle was not found.")
    if battle.status in {"waiting", "active"}:
        battle.status = "cancelled"
        battle.finished_at = utc_now()
        db.commit()
    return {"ok": True, "status": battle.status}


@router.post("/api/battles/{battle_id}/run")
async def run_battle_sample(
    battle_id: UUID,
    body: BattleSubmissionInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    battle = db.get(CodingBattle, battle_id)
    if battle is None or user.id not in {battle.challenger_id, battle.opponent_id}:
        raise HTTPException(status_code=404, detail="Battle was not found.")
    if battle.status != "active" or not battle.opponent_id:
        raise HTTPException(status_code=409, detail="The battle has not started.")
    if battle.expires_at and utc_now() >= as_utc(battle.expires_at):
        battle.status = "expired"
        battle.finished_at = utc_now()
        db.commit()
        raise HTTPException(status_code=409, detail="This battle has expired.")
    challenge = CHALLENGE_BY_ID[battle.challenge_id]
    test = challenge["samples"][0]
    passed, message, provider_accepted = await _run_test_case(
        db=db, user=user, language=battle.language, source_code=body.source_code,
        stdin=test["input"], expected_output=test["output"],
        idempotency_key=f"battle-run:{battle.id}:{user.id}:{body.request_key}",
    )
    return {"passed_sample": passed, "message": message, "provider_accepted": provider_accepted}


@router.post("/api/battles/{battle_id}/submit")
async def submit_battle_solution(
    battle_id: UUID,
    body: BattleSubmissionInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    battle = db.scalar(select(CodingBattle).where(CodingBattle.id == battle_id).with_for_update())
    if battle is None or user.id not in {battle.challenger_id, battle.opponent_id}:
        raise HTTPException(status_code=404, detail="Battle was not found.")
    now = utc_now()
    existing = db.scalar(select(BattleSubmission).where(
        BattleSubmission.battle_id == battle.id,
        BattleSubmission.user_id == user.id,
        BattleSubmission.request_key == body.request_key,
    ))
    if existing is not None:
        return {"submission": {"id": str(existing.id), "status": existing.status, "passed": existing.passed, "result": existing.result_summary}}
    if battle.status != "active" or not battle.opponent_id or (battle.expires_at and now >= as_utc(battle.expires_at)):
        if battle.status == "active":
            battle.status = "expired"
            battle.finished_at = now
            db.commit()
        raise HTTPException(status_code=409, detail="This battle is no longer accepting submissions.")
    in_progress = db.scalar(select(BattleSubmission.id).where(
        BattleSubmission.battle_id == battle.id,
        BattleSubmission.user_id == user.id,
        BattleSubmission.status == "evaluating",
    ).limit(1))
    if in_progress is not None:
        raise HTTPException(status_code=409, detail="A solution from you is already being evaluated.")
    previous_count = int(db.scalar(select(func.count(BattleSubmission.id)).where(
        BattleSubmission.battle_id == battle.id, BattleSubmission.user_id == user.id
    )) or 0)
    if previous_count >= 2:
        raise HTTPException(status_code=429, detail="You have used both solution attempts for this battle.")

    submission = BattleSubmission(
        battle_id=battle.id, user_id=user.id, request_key=body.request_key,
        status="evaluating", passed=False, result_summary={}, created_at=now,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    challenge = CHALLENGE_BY_ID[battle.challenge_id]
    test_results: list[dict[str, Any]] = []
    provider_failure = False
    for index, test in enumerate(challenge["hidden"], start=1):
        try:
            passed, message, accepted = await _run_test_case(
                db=db, user=user, language=battle.language, source_code=body.source_code,
                stdin=test["input"], expected_output=test["output"],
                idempotency_key=f"battle-submit:{battle.id}:{submission.id}:{index}",
            )
        except HTTPException as exc:
            provider_failure = True
            message = str(exc.detail)[:240]
            passed, accepted = False, False
        test_results.append({"test": index, "passed": passed, "message": message})
        if not accepted:
            provider_failure = True
        if not passed:
            break

    submission = db.get(BattleSubmission, submission.id)
    submission.evaluated_at = utc_now()
    submission.passed = bool(test_results) and len(test_results) == len(challenge["hidden"]) and all(row["passed"] for row in test_results)
    if provider_failure:
        submission.status = "failed"
        submission.result_summary = {"message": "The isolated Runner could not complete evaluation. This is not counted as an incorrect solution.", "tests_completed": sum(1 for row in test_results if row["passed"])}
    elif submission.passed:
        submission.status = "accepted"
        submission.result_summary = {"message": "All hidden tests passed.", "tests_passed": len(test_results)}
    else:
        submission.status = "rejected"
        submission.result_summary = {"message": "The solution did not pass all hidden tests.", "tests_passed": sum(1 for row in test_results if row["passed"]), "tests_total": len(challenge["hidden"])}

    unlocked: list[dict[str, str]] = []
    if submission.passed:
        # Serialize the winner decision. Exactly one transaction can transition
        # active -> completed and create the unique XP event for this battle.
        battle = db.scalar(select(CodingBattle).where(CodingBattle.id == battle_id).with_for_update())
        if battle is not None and battle.status == "active" and (not battle.expires_at or utc_now() < as_utc(battle.expires_at)):
            battle.winner_id = user.id
            battle.status = "completed"
            battle.finished_at = utc_now()
            existing_xp = db.scalar(select(XPTransaction).where(
                XPTransaction.user_id == user.id,
                XPTransaction.source_type == "battle_win",
                XPTransaction.source_id == str(battle.id),
            ))
            if existing_xp is None:
                db.add(XPTransaction(
                    user_id=user.id, source_type="battle_win", source_id=str(battle.id),
                    base_points=XP_REWARDS["battle"], awarded_points=XP_REWARDS["battle"], boost_applied=False,
                ))
            db.flush()
            unlocked = evaluate_achievements(db, user.id)
            submission.result_summary = {"message": "All hidden tests passed. You won the battle!", "tests_passed": len(test_results), "xp_awarded": XP_REWARDS["battle"] if existing_xp is None else 0, "new_rewards": unlocked}
        else:
            submission.result_summary = {"message": "All tests passed, but the opponent's valid solution was accepted first.", "tests_passed": len(test_results), "xp_awarded": 0}
    db.commit()
    db.refresh(submission)
    return {
        "submission": {"id": str(submission.id), "status": submission.status, "passed": submission.passed, "result": submission.result_summary},
        "battle": _battle_public_view(db, battle, user.id),
    }


@router.get("/api/me/avatar")
def get_my_avatar(user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    # Reconcile achievements already earned before this feature was deployed.
    evaluate_achievements(db, user.id)
    profile = ensure_avatar_records(db, user.id)
    db.commit()
    owned_rows = db.scalars(select(UserAvatarInventory).where(UserAvatarInventory.user_id == user.id)).all()
    owned_ids = {row.item_id for row in owned_rows}
    equipped = profile.equipment if isinstance(profile.equipment, dict) else {}
    unlocked_rows = db.scalars(select(UserAchievement).where(UserAchievement.user_id == user.id)).all()
    achievement_ids = {row.achievement_id for row in unlocked_rows}
    catalog = []
    for item in AVATAR_ITEMS:
        achievement = next((row for row in ACHIEVEMENTS if row["reward_item_id"] == item["id"]), None)
        catalog.append({
            **item,
            "owned": item["id"] in owned_ids,
            "equipped": equipped.get(item["slot"]) == item["id"],
            "achievement_id": achievement["id"] if achievement else None,
            "unlock_requirement": achievement["description"] if achievement else "Available in your starter collection.",
            "achievement_unlocked": bool(achievement and achievement["id"] in achievement_ids),
        })
    achievements = []
    for achievement in ACHIEVEMENTS:
        item = ITEM_BY_ID[achievement["reward_item_id"]]
        achievements.append({
            **achievement,
            "reward_item_name": item["name"],
            "unlocked": achievement["id"] in achievement_ids,
        })
    return {
        "appearance": {"breed": profile.breed, "fur_color": profile.fur_color, "eye_color": profile.eye_color},
        "equipment": equipped,
        "catalog": catalog,
        "achievements": achievements,
        "owned_item_ids": sorted(owned_ids),
        "supported_breeds": BREEDS,
        "supported_fur_colors": FUR_COLORS,
        "supported_eye_colors": EYE_COLORS,
    }


@router.patch("/api/me/avatar/appearance")
def update_avatar_appearance(
    body: AvatarAppearanceInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    profile = ensure_avatar_records(db, user.id)
    profile.breed = body.breed
    profile.fur_color = body.fur_color
    profile.eye_color = body.eye_color
    profile.updated_at = utc_now()
    db.commit()
    return {"ok": True, "appearance": {"breed": profile.breed, "fur_color": profile.fur_color, "eye_color": profile.eye_color}}


@router.put("/api/me/avatar/equipment")
def update_avatar_equipment(
    body: AvatarEquipmentInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    profile = ensure_avatar_records(db, user.id)
    equipment = dict(profile.equipment or {})
    if body.item_id is None:
        equipment.pop(body.slot, None)
    else:
        item = ITEM_BY_ID.get(body.item_id)
        if item is None or item["slot"] != body.slot:
            raise HTTPException(status_code=422, detail="That cosmetic does not fit the selected equipment slot.")
        owned = db.scalar(select(UserAvatarInventory.id).where(
            UserAvatarInventory.user_id == user.id,
            UserAvatarInventory.item_id == body.item_id,
        ))
        if owned is None:
            raise HTTPException(status_code=403, detail="This cosmetic is locked. Complete its achievement to unlock it.")
        equipment[body.slot] = body.item_id
    profile.equipment = equipment
    profile.updated_at = utc_now()
    db.commit()
    return {"ok": True, "equipment": equipment}


@router.post("/api/me/avatar/reset")
def reset_avatar(user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    profile = ensure_avatar_records(db, user.id)
    profile.breed = "classic"
    profile.fur_color = "golden"
    profile.eye_color = "brown"
    profile.equipment = {}
    profile.updated_at = utc_now()
    db.commit()
    return {"ok": True, "appearance": {"breed": profile.breed, "fur_color": profile.fur_color, "eye_color": profile.eye_color}, "equipment": {}}
