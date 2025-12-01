"""
Plan service for managing subscription plans and feature access.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from app.models.user import User


# Plan configuration with features and pricing
PLAN_CONFIG: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "price_yearly": 0,
        "duration_days": None,
        "features": {
            "ai_questions_per_day": 5,
            "has_themes": False,
            "has_weekly_insights": False,
            "has_monthly_insights": False,
            "has_voice_recording": False,
            "has_visual_themes": False,
            "has_visual_effects": False,
        },
    },
    "trial": {
        "name": "Trial",
        "price_monthly": 0,
        "price_yearly": 0,
        "duration_days": 14,  # 14-day trial
        "features": {
            "ai_questions_per_day": None,  # Unlimited
            "has_themes": True,
            "has_weekly_insights": True,
            "has_monthly_insights": True,
            "has_voice_recording": True,
            "has_visual_themes": True,
            "has_visual_effects": True,
        },
    },
    "pro_month": {
        "name": "Pro Monthly",
        "price_monthly": 1990,
        "price_yearly": 0,
        "duration_days": 30,
        "features": {
            "ai_questions_per_day": None,  # Unlimited
            "has_themes": True,
            "has_weekly_insights": True,
            "has_monthly_insights": True,
            "has_voice_recording": True,
            "has_visual_themes": True,
            "has_visual_effects": True,
        },
    },
    "pro_year": {
        "name": "Pro Yearly",
        "price_monthly": 0,
        "price_yearly": 19100,
        "duration_days": 365,
        "features": {
            "ai_questions_per_day": None,  # Unlimited
            "has_themes": True,
            "has_weekly_insights": True,
            "has_monthly_insights": True,
            "has_voice_recording": True,
            "has_visual_themes": True,
            "has_visual_effects": True,
        },
    },
}


def get_plan_config(plan: str) -> Dict[str, Any]:
    """Get configuration for a specific plan."""
    return PLAN_CONFIG.get(plan, PLAN_CONFIG["free"])


def can_use_feature(user: User, feature: str) -> bool:
    """
    Check if user can use a specific feature based on their plan.

    Args:
        user: User instance
        feature: Feature name (e.g., "has_themes", "has_voice_recording")

    Returns:
        True if user can use the feature, False otherwise
    """
    if not is_plan_active(user):
        # If plan is expired, check free plan features
        plan_config = PLAN_CONFIG["free"]
    else:
        plan_config = get_plan_config(user.plan)

    return plan_config["features"].get(feature, False)


def is_plan_active(user: User) -> bool:
    """
    Check if user's current plan is active.

    Args:
        user: User instance

    Returns:
        True if plan is active, False otherwise
    """
    if user.plan == "free":
        return True

    if user.plan_expires_at is None:
        return False

    return datetime.utcnow() < user.plan_expires_at


def get_ai_questions_limit(user: User) -> Optional[int]:
    """
    Get the daily limit for AI questions for a user.

    Args:
        user: User instance

    Returns:
        Daily limit (None means unlimited) or None if plan is expired
    """
    if not is_plan_active(user):
        plan_config = PLAN_CONFIG["free"]
    else:
        plan_config = get_plan_config(user.plan)

    return plan_config["features"].get("ai_questions_per_day")


def can_skip_ai_questions(user: User) -> tuple[bool, str | None, int, int]:
    """
    Check if user can skip AI questions (generate new ones).

    Args:
        user: User instance

    Returns:
        Tuple of (can_skip: bool, error_message: str | None, remaining_skips: int, max_skips: int)
        For pro users: 5 skips per hour
        For free users: 1 skip per day
    """
    from datetime import timedelta

    # Pro users: 5 skips per hour
    if user.plan in ["pro_month", "pro_year"] and is_plan_active(user):
        MAX_SKIPS = 5
        COOLDOWN_HOURS = 1

        # Check if cooldown period has passed
        if user.ai_questions_skips_reset_at:
            cooldown_end = user.ai_questions_skips_reset_at + timedelta(
                hours=COOLDOWN_HOURS
            )
            if datetime.utcnow() < cooldown_end:
                # Still in cooldown, check if user has used all skips
                if user.ai_questions_skips_count >= MAX_SKIPS:
                    time_remaining = cooldown_end - datetime.utcnow()
                    minutes = int(time_remaining.total_seconds() / 60)
                    return False, f"Сброс доступен через {minutes}м", 0, MAX_SKIPS
                else:
                    # Cooldown active but still have skips left (shouldn't happen, but handle it)
                    remaining = MAX_SKIPS - user.ai_questions_skips_count
                    return True, None, remaining, MAX_SKIPS
            else:
                # Cooldown passed, reset counter
                return True, None, MAX_SKIPS, MAX_SKIPS
        else:
            # First time or counter was reset
            return True, None, MAX_SKIPS, MAX_SKIPS

    # Free users: 1 skip per day
    if user.plan == "free":
        MAX_SKIPS = 1
        COOLDOWN_DAYS = 1

        if user.ai_questions_skips_reset_at:
            cooldown_end = user.ai_questions_skips_reset_at + timedelta(
                days=COOLDOWN_DAYS
            )
            if datetime.utcnow() < cooldown_end:
                # Still in cooldown
                if user.ai_questions_skips_count >= MAX_SKIPS:
                    time_remaining = cooldown_end - datetime.utcnow()
                    hours = int(time_remaining.total_seconds() / 3600)
                    minutes = int((time_remaining.total_seconds() % 3600) / 60)
                    return (
                        False,
                        f"Сброс доступен через {hours}ч {minutes}м",
                        0,
                        MAX_SKIPS,
                    )
                else:
                    remaining = MAX_SKIPS - user.ai_questions_skips_count
                    return True, None, remaining, MAX_SKIPS
            else:
                # Cooldown passed, reset counter
                return True, None, MAX_SKIPS, MAX_SKIPS
        else:
            # First time
            return True, None, MAX_SKIPS, MAX_SKIPS

    # Trial users: same as free
    if user.plan == "trial":
        MAX_SKIPS = 1
        COOLDOWN_DAYS = 1

        if user.ai_questions_skips_reset_at:
            cooldown_end = user.ai_questions_skips_reset_at + timedelta(
                days=COOLDOWN_DAYS
            )
            if datetime.utcnow() < cooldown_end:
                if user.ai_questions_skips_count >= MAX_SKIPS:
                    time_remaining = cooldown_end - datetime.utcnow()
                    hours = int(time_remaining.total_seconds() / 3600)
                    minutes = int((time_remaining.total_seconds() % 3600) / 60)
                    return (
                        False,
                        f"Сброс доступен через {hours}ч {minutes}м",
                        0,
                        MAX_SKIPS,
                    )
                else:
                    remaining = MAX_SKIPS - user.ai_questions_skips_count
                    return True, None, remaining, MAX_SKIPS
            else:
                return True, None, MAX_SKIPS, MAX_SKIPS
        else:
            return True, None, MAX_SKIPS, MAX_SKIPS

    return False, "Неизвестный план", 0, 0


def get_plan_price(plan: str) -> float:
    """
    Get the price for a plan.

    Args:
        plan: Plan identifier ("pro_month" or "pro_year")

    Returns:
        Price in KZT
    """
    plan_config = get_plan_config(plan)
    if plan == "pro_month":
        return plan_config["price_monthly"]
    elif plan == "pro_year":
        return plan_config["price_yearly"]
    return 0.0
