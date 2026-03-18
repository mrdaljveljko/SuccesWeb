from __future__ import annotations

from pathlib import Path

APP_NAME = "AstroAi"
SECRET_KEY = "dev-secret-change-me"
DATABASE_PATH = Path("instance/astroai.db")

DEFAULT_PLAN = "free"
PLAN_PREMIUM = "premium"

DAILY_LOGIN_REWARD_TOKENS = 5
TOKEN_COSTS = {
    "natal_chart": 25,
    "astrology_reading": 15,
    "extra_question": 10,
    "extra_horoscope": 10,
}

FEATURE_HOROSCOPE = "horoscope"
FEATURE_QUESTION = "question"
FEATURE_MEDITATION = "meditation"
FEATURE_LOGIN_REWARD = "login_reward"
FEATURE_TOKEN_SPEND = "token_spend"

SOURCE_DAILY_LOGIN = "daily_login"
SOURCE_NATAL_CHART = "natal_chart"
SOURCE_ASTROLOGY_READING = "astrology_reading"
SOURCE_EXTRA_QUESTION = "extra_question"
SOURCE_FREE_DAY1 = "free_day1"
SOURCE_PREMIUM_DAILY = "premium_daily"
SOURCE_TOKEN_UNLOCK = "token_unlock"
SOURCE_CURATED_BANK = "curated_bank"

WEEK_START = 0  # Monday
SESSION_USER_KEY = "user_id"

PREMIUM_FEATURES = [
    "Daily horoscope for your sign",
    "1 included AstroAi question every day",
    "Premium badge and elevated access",
    "Priority for future premium meditations and readings",
]

FREE_FEATURES = [
    "Day-1 horoscope and 1 day-1 AstroAi question",
    "1 meditation each week",
    "Daily login streak rewards",
    "Spend Astro Tokens on premium-style unlocks",
]
