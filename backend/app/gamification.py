"""Server-owned XP and dog-avatar achievement catalogue.

All catalogue metadata lives in code; ownership, unlocked achievements and equipped
slots are persisted in PostgreSQL. This keeps the client from declaring rewards.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .plan_entitlements import effective_plan_id, plan_limits
from .models import (
    BattleSubmission,
    CodingBattle,
    Course,
    Exercise,
    ExerciseProgress,
    Lesson,
    LessonProgress,
    Module,
    UserAchievement,
    User,
    UserActivityDay,
    UserAvatarInventory,
    UserAvatarProfile,
    XPTransaction,
)

BREEDS = ["classic", "shiba", "husky", "retriever", "corgi", "bulldog"]
FUR_COLORS = ["golden", "cream", "chocolate", "charcoal", "snow", "copper"]
EYE_COLORS = ["brown", "blue", "green", "amber"]

# Server-owned reward policy. Frontend values are display-only.
XP_REWARDS = {"lesson": 10, "exercise": 10, "project": 100, "battle": 10, "achievement": 10}


def xp_amount_for_json(value: Any) -> int | float:
    """Serialize an exact two-decimal XP amount without unnecessary .0 suffixes."""
    amount = Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount == amount.to_integral_value():
        return int(amount)
    return float(amount)


def calculate_xp_award(db: Session, user_id: UUID, activity_type: str) -> tuple[int, Decimal, bool]:
    """Calculate an XP reward from trusted active subscription entitlements."""
    if activity_type not in XP_REWARDS:
        raise ValueError(f"Unsupported XP activity type: {activity_type}")
    base_points = XP_REWARDS[activity_type]
    plan_id = effective_plan_id(db, user_id)
    multiplier = Decimal(str(plan_limits(plan_id).get("xp_multiplier", 1.0)))
    awarded_points = (Decimal(base_points) * multiplier).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return base_points, awarded_points, multiplier > Decimal("1.0")

# Each achievement reward maps to one unique item and one compatible equipment slot.
AVATAR_ITEMS: list[dict[str, Any]] = [
    {"id": "starter-cap", "name": "Starter Cap", "category": "Headwear", "slot": "headwear", "icon": "🧢", "rarity": "common"},
    {"id": "developer-glasses", "name": "Developer Glasses", "category": "Glasses", "slot": "glasses", "icon": "🤓", "rarity": "common"},
    {"id": "blue-hoodie", "name": "Blue Hoodie", "category": "Shirts", "slot": "shirt", "icon": "🧥", "rarity": "common"},
    {"id": "programmer-collar", "name": "Programmer Collar", "category": "Collars", "slot": "collar", "icon": "🦴", "rarity": "common"},
    {"id": "golden-crown", "name": "Golden Crown", "category": "Headwear", "slot": "headwear", "icon": "👑", "rarity": "rare"},
    {"id": "explorer-backpack", "name": "Explorer Backpack", "category": "Accessories", "slot": "back", "icon": "🎒", "rarity": "rare"},
    {"id": "wizard-hat", "name": "Wizard Hat", "category": "Headwear", "slot": "headwear", "icon": "🪄", "rarity": "epic"},
    {"id": "coding-headset", "name": "Coding Headset", "category": "Headwear", "slot": "headwear", "icon": "🎧", "rarity": "common"},
    {"id": "developer-jacket", "name": "Developer Jacket", "category": "Shirts", "slot": "shirt", "icon": "🧥", "rarity": "rare"},
    {"id": "master-headphones", "name": "Master Headphones", "category": "Headwear", "slot": "headwear", "icon": "🎧", "rarity": "epic"},
    {"id": "cyber-visor", "name": "Cyber Visor", "category": "Glasses", "slot": "glasses", "icon": "🕶️", "rarity": "epic"},
    {"id": "battle-champion-cap", "name": "Battle Champion Cap", "category": "Headwear", "slot": "headwear", "icon": "🏆", "rarity": "rare"},
    {"id": "warrior-outfit", "name": "Warrior Outfit", "category": "Full Outfits", "slot": "outfit", "icon": "🛡️", "rarity": "epic"},
    {"id": "golden-battle-glasses", "name": "Golden Battle Glasses", "category": "Glasses", "slot": "glasses", "icon": "🥽", "rarity": "epic"},
    {"id": "legendary-battle-costume", "name": "Legendary Battle Costume", "category": "Full Outfits", "slot": "outfit", "icon": "⚔️", "rarity": "legendary"},
    {"id": "diamond-crown", "name": "Diamond Crown", "category": "Headwear", "slot": "headwear", "icon": "💎", "rarity": "legendary"},
    {"id": "streak-bandana", "name": "Streak Bandana", "category": "Neck Accessories", "slot": "neckwear", "icon": "🥇", "rarity": "common"},
    {"id": "fire-collar", "name": "Fire Collar", "category": "Collars", "slot": "collar", "icon": "🔥", "rarity": "rare"},
    {"id": "legendary-streak-costume", "name": "Legendary Streak Costume", "category": "Full Outfits", "slot": "outfit", "icon": "🔥", "rarity": "legendary"},
    {"id": "moon-hoodie", "name": "Moon Hoodie", "category": "Shirts", "slot": "shirt", "icon": "🌙", "rarity": "epic"},
    {"id": "graduation-hat", "name": "Graduation Hat", "category": "Headwear", "slot": "headwear", "icon": "🎓", "rarity": "common"},
    {"id": "scholar-outfit", "name": "Scholar Outfit", "category": "Full Outfits", "slot": "outfit", "icon": "📚", "rarity": "rare"},
    {"id": "galaxy-cape", "name": "Galaxy Cape", "category": "Special Items", "slot": "back", "icon": "🌌", "rarity": "legendary"},
    {"id": "xp-champion-accessory", "name": "XP Champion Badge", "category": "Special Items", "slot": "face", "icon": "⚡", "rarity": "common"},
    {"id": "xp-master-costume", "name": "XP Master Costume", "category": "Full Outfits", "slot": "outfit", "icon": "🌟", "rarity": "epic"},
    {"id": "legendary-dog-outfit", "name": "Legendary Dog Outfit", "category": "Full Outfits", "slot": "outfit", "icon": "🐉", "rarity": "legendary"},
    {"id": "pixel-wings", "name": "Pixel Wings", "category": "Special Items", "slot": "back", "icon": "🪽", "rarity": "legendary"},
    {"id": "hero-cape", "name": "Hero Cape", "category": "Special Items", "slot": "back", "icon": "🦸", "rarity": "legendary"},
    {"id": "compiler-crown", "name": "Compiler Crown", "category": "Headwear", "slot": "headwear", "icon": "💻", "rarity": "legendary"},
    {"id": "grandmaster-outfit", "name": "Grandmaster Outfit", "category": "Full Outfits", "slot": "outfit", "icon": "🏅", "rarity": "legendary"},
    {"id": "comet-bandana", "name": "Comet Bandana", "category": "Neck Accessories", "slot": "neckwear", "icon": "☄️", "rarity": "legendary"},
    {"id": "emerald-dog-suit", "name": "Emerald Dog Suit", "category": "Full Outfits", "slot": "outfit", "icon": "💚", "rarity": "legendary"},
    {"id": "floppy-ears", "name": "Cloud Ears", "category": "Ears", "slot": "ears", "icon": "🐰", "rarity": "rare"},
    {"id": "starry-eyes", "name": "Starry Eyes", "category": "Eyes", "slot": "eyes", "icon": "✨", "rarity": "epic"},
    {"id": "pixel-pants", "name": "Pixel Pants", "category": "Pants", "slot": "pants", "icon": "👖", "rarity": "rare"},
    {"id": "sprint-shoes", "name": "Sprint Shoes", "category": "Shoes", "slot": "shoes", "icon": "👟", "rarity": "common"},
    {"id": "classic-collar", "name": "Classic Collar", "category": "Collars", "slot": "collar", "icon": "🔴", "rarity": "starter", "free": True},
    {"id": "leaf-bandana", "name": "Leaf Bandana", "category": "Neck Accessories", "slot": "neckwear", "icon": "🍃", "rarity": "starter", "free": True},
    {"id": "aurora-background", "name": "Aurora Background", "category": "Backgrounds", "slot": "background", "icon": "🌌", "rarity": "starter", "free": True},
    {"id": "forest-background", "name": "Forest Background", "category": "Backgrounds", "slot": "background", "icon": "🌲", "rarity": "starter", "free": True},
    {"id": "pixel-lab-background", "name": "Pixel Lab Background", "category": "Backgrounds", "slot": "background", "icon": "🟪", "rarity": "starter", "free": True},
]
ITEM_BY_ID = {item["id"]: item for item in AVATAR_ITEMS}

ACHIEVEMENTS: list[dict[str, Any]] = [
    {"id": "first-task", "name": "First Steps", "description": "Complete your first learning task.", "requirement_type": "tasks_completed", "threshold": 1, "reward_item_id": "starter-cap"},
    {"id": "five-tasks", "name": "Getting Warmed Up", "description": "Complete 5 learning tasks.", "requirement_type": "tasks_completed", "threshold": 5, "reward_item_id": "developer-glasses"},
    {"id": "ten-tasks", "name": "Consistent Learner", "description": "Complete 10 learning tasks.", "requirement_type": "tasks_completed", "threshold": 10, "reward_item_id": "blue-hoodie"},
    {"id": "twenty-five-tasks", "name": "Practice Habit", "description": "Complete 25 learning tasks.", "requirement_type": "tasks_completed", "threshold": 25, "reward_item_id": "programmer-collar"},
    {"id": "fifty-tasks", "name": "Dedicated Learner", "description": "Complete 50 learning tasks.", "requirement_type": "tasks_completed", "threshold": 50, "reward_item_id": "golden-crown"},
    {"id": "hundred-tasks", "name": "Trailblazer", "description": "Complete 100 learning tasks.", "requirement_type": "tasks_completed", "threshold": 100, "reward_item_id": "explorer-backpack"},
    {"id": "two-hundred-tasks", "name": "Learning Legend", "description": "Complete 200 learning tasks.", "requirement_type": "tasks_completed", "threshold": 200, "reward_item_id": "wizard-hat"},
    {"id": "first-code-challenge", "name": "Code Starter", "description": "Complete your first coded exercise.", "requirement_type": "coding_challenges_completed", "threshold": 1, "reward_item_id": "coding-headset"},
    {"id": "ten-code-challenges", "name": "Code Builder", "description": "Complete 10 coded exercises.", "requirement_type": "coding_challenges_completed", "threshold": 10, "reward_item_id": "developer-jacket"},
    {"id": "twenty-code-challenges", "name": "Code Crafter", "description": "Complete 20 coded exercises.", "requirement_type": "coding_challenges_completed", "threshold": 20, "reward_item_id": "master-headphones"},
    {"id": "fifty-code-challenges", "name": "Code Master", "description": "Complete 50 coded exercises.", "requirement_type": "coding_challenges_completed", "threshold": 50, "reward_item_id": "cyber-visor"},
    {"id": "first-battle-win", "name": "First Victory", "description": "Win your first coding battle.", "requirement_type": "battle_wins", "threshold": 1, "reward_item_id": "battle-champion-cap"},
    {"id": "five-battle-wins", "name": "Battle Regular", "description": "Win 5 coding battles.", "requirement_type": "battle_wins", "threshold": 5, "reward_item_id": "warrior-outfit"},
    {"id": "ten-battle-wins", "name": "Battle Expert", "description": "Win 10 coding battles.", "requirement_type": "battle_wins", "threshold": 10, "reward_item_id": "golden-battle-glasses"},
    {"id": "twenty-five-battle-wins", "name": "Battle Champion", "description": "Win 25 coding battles.", "requirement_type": "battle_wins", "threshold": 25, "reward_item_id": "legendary-battle-costume"},
    {"id": "hundred-battle-wins", "name": "Battle Grandmaster", "description": "Win 100 coding battles.", "requirement_type": "battle_wins", "threshold": 100, "reward_item_id": "diamond-crown"},
    {"id": "three-day-streak", "name": "Three-Day Streak", "description": "Keep a 3-day learning streak.", "requirement_type": "current_streak", "threshold": 3, "reward_item_id": "streak-bandana"},
    {"id": "seven-day-streak", "name": "On Fire", "description": "Keep a 7-day learning streak.", "requirement_type": "current_streak", "threshold": 7, "reward_item_id": "fire-collar"},
    {"id": "thirty-day-streak", "name": "Streak Legend", "description": "Keep a 30-day learning streak.", "requirement_type": "current_streak", "threshold": 30, "reward_item_id": "legendary-streak-costume"},
    {"id": "sixty-day-streak", "name": "Unstoppable", "description": "Keep a 60-day learning streak.", "requirement_type": "current_streak", "threshold": 60, "reward_item_id": "moon-hoodie"},
    {"id": "first-course", "name": "Course Graduate", "description": "Complete your first course.", "requirement_type": "courses_completed", "threshold": 1, "reward_item_id": "graduation-hat"},
    {"id": "five-courses", "name": "Scholar", "description": "Complete 5 courses.", "requirement_type": "courses_completed", "threshold": 5, "reward_item_id": "scholar-outfit"},
    {"id": "fifty-courses", "name": "Knowledge Explorer", "description": "Complete 50 courses.", "requirement_type": "courses_completed", "threshold": 50, "reward_item_id": "galaxy-cape"},
    {"id": "one-thousand-xp", "name": "XP Champion", "description": "Earn 1,000 XP.", "requirement_type": "total_xp", "threshold": 1000, "reward_item_id": "xp-champion-accessory"},
    {"id": "five-thousand-xp", "name": "XP Master", "description": "Earn 5,000 XP.", "requirement_type": "total_xp", "threshold": 5000, "reward_item_id": "xp-master-costume"},
    {"id": "ten-thousand-xp", "name": "XP Legend", "description": "Earn 10,000 XP.", "requirement_type": "total_xp", "threshold": 10000, "reward_item_id": "legendary-dog-outfit"},
    {"id": "fifteen-thousand-xp", "name": "Pixel Hero", "description": "Earn 15,000 XP.", "requirement_type": "total_xp", "threshold": 15000, "reward_item_id": "pixel-wings"},
    {"id": "five-hundred-tasks", "name": "CodeLeaf Hero", "description": "Complete 500 learning tasks.", "requirement_type": "tasks_completed", "threshold": 500, "reward_item_id": "hero-cape"},
    {"id": "hundred-code-challenges", "name": "Compiler Champion", "description": "Complete 100 coded exercises.", "requirement_type": "coding_challenges_completed", "threshold": 100, "reward_item_id": "compiler-crown"},
    {"id": "two-hundred-fifty-wins", "name": "Grandmaster", "description": "Win 250 coding battles.", "requirement_type": "battle_wins", "threshold": 250, "reward_item_id": "grandmaster-outfit"},
    {"id": "hundred-day-streak", "name": "Comet Streak", "description": "Keep a 100-day learning streak.", "requirement_type": "current_streak", "threshold": 100, "reward_item_id": "comet-bandana"},
    {"id": "twenty-five-thousand-xp", "name": "Emerald Legend", "description": "Earn 25,000 XP.", "requirement_type": "total_xp", "threshold": 25000, "reward_item_id": "emerald-dog-suit"},
    {"id": "three-hundred-tasks", "name": "Dogged Determination", "description": "Complete 300 learning tasks.", "requirement_type": "tasks_completed", "threshold": 300, "reward_item_id": "floppy-ears"},
    {"id": "seventy-five-code-challenges", "name": "Syntax Star", "description": "Complete 75 coded exercises.", "requirement_type": "coding_challenges_completed", "threshold": 75, "reward_item_id": "starry-eyes"},
    {"id": "ten-courses", "name": "Course Collector", "description": "Complete 10 courses.", "requirement_type": "courses_completed", "threshold": 10, "reward_item_id": "pixel-pants"},
    {"id": "fifty-battle-wins", "name": "Arena Elite", "description": "Win 50 coding battles.", "requirement_type": "battle_wins", "threshold": 50, "reward_item_id": "sprint-shoes"},
]
ACHIEVEMENT_BY_ID = {item["id"]: item for item in ACHIEVEMENTS}


def ensure_avatar_records(db: Session, user_id: UUID) -> UserAvatarProfile:
    profile = db.get(UserAvatarProfile, user_id)
    if profile is None:
        profile = UserAvatarProfile(user_id=user_id, breed="classic", fur_color="golden", eye_color="brown", equipment={})
        db.add(profile)
        db.flush()
    for item_id in ("classic-collar", "leaf-bandana", "aurora-background", "forest-background", "pixel-lab-background"):
        owned = db.scalar(select(UserAvatarInventory.id).where(
            UserAvatarInventory.user_id == user_id,
            UserAvatarInventory.item_id == item_id,
        ))
        if owned is None:
            db.add(UserAvatarInventory(user_id=user_id, item_id=item_id, acquired_via="starter"))
    db.flush()
    return profile


def _current_streak(db: Session, user_id: UUID) -> int:
    activity_rows = db.execute(
        select(UserActivityDay.activity_date, UserActivityDay.timezone_name)
        .where(UserActivityDay.user_id == user_id)
        .order_by(UserActivityDay.activity_date.desc())
        .limit(400)
    ).all()
    dates = {row.activity_date for row in activity_rows}
    if not dates:
        return 0
    timezone_name = activity_rows[0].timezone_name or "UTC"
    try:
        today = datetime.now(ZoneInfo(timezone_name)).date()
    except (ZoneInfoNotFoundError, ValueError):
        today = date.today()
    cursor = today if today in dates else today - timedelta(days=1)
    if cursor not in dates:
        return 0
    count = 0
    while cursor in dates:
        count += 1
        cursor -= timedelta(days=1)
    return count


def _completed_course_count(db: Session, user_id: UUID) -> int:
    courses = db.scalars(select(Course.id).where(Course.published.is_(True))).all()
    completed = 0
    for course_id in courses:
        total = int(db.scalar(
            select(func.count(Lesson.id)).join(Module, Module.id == Lesson.module_id).where(
                Module.course_id == course_id, Lesson.is_published.is_(True)
            )
        ) or 0)
        if not total:
            continue
        done = int(db.scalar(
            select(func.count(LessonProgress.id)).join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .join(Module, Module.id == Lesson.module_id)
            .where(
                LessonProgress.user_id == user_id,
                LessonProgress.completed.is_(True),
                Module.course_id == course_id,
                Lesson.is_published.is_(True),
            )
        ) or 0)
        if done >= total:
            completed += 1
    return completed


def evaluate_achievements(db: Session, user_id: UUID) -> list[dict[str, str]]:
    """Unlock every newly met achievement once and grant exactly its one catalog item."""
    # Serialize progress-triggered unlocks for an account. Unique constraints remain
    # the final guard, while this lock prevents routine concurrent completions from
    # racing each other into avoidable integrity errors.
    db.scalar(select(User.id).where(User.id == user_id).with_for_update())
    ensure_avatar_records(db, user_id)
    lessons = int(db.scalar(select(func.count(LessonProgress.id)).where(
        LessonProgress.user_id == user_id, LessonProgress.completed.is_(True)
    )) or 0)
    exercises = int(db.scalar(select(func.count(ExerciseProgress.id)).where(
        ExerciseProgress.user_id == user_id, ExerciseProgress.completed.is_(True)
    )) or 0)
    coding_challenges = int(db.scalar(
        select(func.count(ExerciseProgress.id)).join(Exercise, Exercise.id == ExerciseProgress.exercise_id)
        .where(
            ExerciseProgress.user_id == user_id,
            ExerciseProgress.completed.is_(True),
            func.lower(Exercise.exercise_type).in_(["code", "coding_challenge", "code_challenge", "codechallenge"]),
        )
    ) or 0)
    battle_wins = int(db.scalar(select(func.count(CodingBattle.id)).where(
        CodingBattle.winner_id == user_id, CodingBattle.status == "completed"
    )) or 0)
    total_xp = Decimal(str(db.scalar(select(func.coalesce(func.sum(XPTransaction.awarded_points), 0)).where(
        XPTransaction.user_id == user_id
    )) or 0))
    values = {
        "tasks_completed": lessons + exercises,
        "coding_challenges_completed": coding_challenges,
        "battle_wins": battle_wins,
        "current_streak": _current_streak(db, user_id),
        "courses_completed": _completed_course_count(db, user_id),
        "total_xp": total_xp,
    }
    unlocked: list[dict[str, str]] = []
    for achievement in ACHIEVEMENTS:
        if values[achievement["requirement_type"]] < achievement["threshold"]:
            continue
        current = db.scalar(select(UserAchievement).where(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement["id"],
        ))
        # Achievement XP is one-time, server-owned and tied to the achievement ID.
        # The unique XP event key prevents repeated evaluator calls from paying twice.
        achievement_xp = db.scalar(select(XPTransaction.id).where(
            XPTransaction.user_id == user_id,
            XPTransaction.source_type == "achievement_completed",
            XPTransaction.source_id == achievement["id"],
        ))
        base_points = XP_REWARDS["achievement"]
        awarded_points = Decimal(base_points)
        boost_applied = False
        if achievement_xp is None:
            base_points, awarded_points, boost_applied = calculate_xp_award(db, user_id, "achievement")
            db.add(XPTransaction(
                user_id=user_id,
                source_type="achievement_completed",
                source_id=achievement["id"],
                base_points=base_points,
                awarded_points=awarded_points,
                boost_applied=boost_applied,
            ))
        if current is None:
            current = UserAchievement(
                user_id=user_id,
                achievement_id=achievement["id"],
                reward_item_id=achievement["reward_item_id"],
            )
            db.add(current)
            db.flush()
            unlocked.append({"achievement_id": achievement["id"], "achievement_name": achievement["name"], "item_id": achievement["reward_item_id"], "item_name": ITEM_BY_ID[achievement["reward_item_id"]]["name"], "item_slot": ITEM_BY_ID[achievement["reward_item_id"]]["slot"], "item_icon": ITEM_BY_ID[achievement["reward_item_id"]]["icon"], "xp_awarded": xp_amount_for_json(awarded_points if achievement_xp is None else 0)})
        inventory = db.scalar(select(UserAvatarInventory.id).where(
            UserAvatarInventory.user_id == user_id,
            UserAvatarInventory.item_id == achievement["reward_item_id"],
        ))
        if inventory is None:
            db.add(UserAvatarInventory(
                user_id=user_id,
                item_id=achievement["reward_item_id"],
                acquired_via="achievement",
                source_achievement_id=achievement["id"],
            ))
    db.flush()
    return unlocked
