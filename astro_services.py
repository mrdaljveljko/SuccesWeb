from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from astro_config import (
    DAILY_LOGIN_REWARD_TOKENS,
    FEATURE_HOROSCOPE,
    FEATURE_LOGIN_REWARD,
    FEATURE_MEDITATION,
    FEATURE_QUESTION,
    FEATURE_TOKEN_SPEND,
    PLAN_PREMIUM,
    SOURCE_ASTROLOGY_READING,
    SOURCE_CURATED_BANK,
    SOURCE_DAILY_LOGIN,
    SOURCE_EXTRA_QUESTION,
    SOURCE_FREE_DAY1,
    SOURCE_NATAL_CHART,
    SOURCE_PREMIUM_DAILY,
    SOURCE_TOKEN_UNLOCK,
    TOKEN_COSTS,
    WEEK_START,
)
from astro_content import MOCK_CONTENT_LIBRARY, MOCK_CONTENT_VERSIONS, MOCK_HOROSCOPE_TEMPLATES, MOCK_MEDITATIONS


@dataclass
class FeatureAccessResult:
    allowed: bool
    source_type: str | None
    message: str
    requires_tokens: bool = False
    token_cost: int = 0


class AstroService:
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection
        self.conn.row_factory = sqlite3.Row

    def initialize(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                zodiac_sign TEXT NOT NULL,
                birth_date TEXT,
                birth_time TEXT,
                birth_place TEXT,
                natal_chart_data TEXT,
                plan_type TEXT NOT NULL DEFAULT 'free',
                astro_token_balance INTEGER NOT NULL DEFAULT 0,
                streak_count INTEGER NOT NULL DEFAULT 0,
                last_login_date TEXT,
                reset_token TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS horoscopes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                zodiac_sign TEXT NOT NULL,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                content_batch TEXT,
                seasonal_period TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(zodiac_sign, date)
            );

            CREATE TABLE IF NOT EXISTS meditations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                duration TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content_url TEXT,
                text_content TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS question_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                source_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                feature_type TEXT NOT NULL,
                usage_date TEXT NOT NULL,
                week_key TEXT,
                tokens_added INTEGER,
                tokens_spent INTEGER,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS token_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                source TEXT NOT NULL,
                amount INTEGER NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_type TEXT NOT NULL,
                status TEXT NOT NULL,
                provider TEXT,
                provider_reference TEXT,
                started_at TEXT NOT NULL,
                ends_at TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS content_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                question_text TEXT,
                answer_text TEXT NOT NULL,
                zodiac_sign TEXT,
                content_period TEXT,
                active_from TEXT,
                active_until TEXT,
                priority INTEGER,
                tags TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS content_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                active_from TEXT,
                active_until TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self.seed_mock_data()
        self.conn.commit()

    def utcnow(self) -> datetime:
        return datetime.utcnow().replace(microsecond=0)

    def today_str(self) -> str:
        return self.utcnow().date().isoformat()

    def current_week_key(self, on_date: date | None = None) -> str:
        active_date = on_date or self.utcnow().date()
        start = active_date - timedelta(days=(active_date.weekday() - WEEK_START) % 7)
        return start.isoformat()

    def is_same_day(self, first: str | None, second: str | None) -> bool:
        return bool(first and second and first == second)

    def is_next_day(self, previous: str | None, current: str) -> bool:
        if not previous:
            return False
        return date.fromisoformat(previous) + timedelta(days=1) == date.fromisoformat(current)

    def seed_mock_data(self) -> None:
        if self.conn.execute("SELECT COUNT(*) FROM meditations").fetchone()[0] == 0:
            now = self.utcnow().isoformat()
            self.conn.executemany(
                """
                INSERT INTO meditations (title, description, duration, content_type, content_url, text_content, created_at)
                VALUES (:title, :description, :duration, :content_type, NULL, :text_content, :created_at)
                """,
                [{**meditation, "created_at": now} for meditation in MOCK_MEDITATIONS],
            )
        if self.conn.execute("SELECT COUNT(*) FROM content_library").fetchone()[0] == 0:
            now = self.utcnow().isoformat()
            self.conn.executemany(
                """
                INSERT INTO content_library (
                    category, title, question_text, answer_text, zodiac_sign, content_period,
                    active_from, active_until, priority, tags, status, created_at, updated_at
                ) VALUES (
                    :category, :title, :question_text, :answer_text, NULL, :content_period,
                    NULL, NULL, :priority, :tags, :status, :created_at, :updated_at
                )
                """,
                [{**item, "created_at": now, "updated_at": now} for item in MOCK_CONTENT_LIBRARY],
            )
        if self.conn.execute("SELECT COUNT(*) FROM content_versions").fetchone()[0] == 0:
            now = self.utcnow().isoformat()
            self.conn.executemany(
                """
                INSERT INTO content_versions (name, description, active_from, active_until, status, created_at)
                VALUES (:name, :description, :active_from, :active_until, :status, :created_at)
                """,
                [{**item, "created_at": now} for item in MOCK_CONTENT_VERSIONS],
            )

    def get_user(self, user_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    def get_user_by_email(self, email: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,)).fetchone()

    def create_user(self, *, name: str, email: str, password_hash: str, zodiac_sign: str, birth_date: str | None) -> sqlite3.Row:
        now = self.utcnow().isoformat()
        cursor = self.conn.execute(
            """
            INSERT INTO users (name, email, password_hash, zodiac_sign, birth_date, plan_type, astro_token_balance, streak_count, last_login_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'free', 0, 0, NULL, ?, ?)
            """,
            (name, email, password_hash, zodiac_sign, birth_date, now, now),
        )
        self.conn.execute(
            "INSERT INTO subscriptions (user_id, plan_type, status, provider, provider_reference, started_at, ends_at, updated_at) VALUES (?, 'free', 'active', 'internal', 'mvp-free', ?, NULL, ?)",
            (cursor.lastrowid, now, now),
        )
        self.conn.commit()
        return self.get_user(cursor.lastrowid)

    def update_profile(self, user_id: int, *, name: str, zodiac_sign: str, birth_date: str | None) -> None:
        self.conn.execute(
            "UPDATE users SET name = ?, zodiac_sign = ?, birth_date = ?, updated_at = ? WHERE id = ?",
            (name, zodiac_sign, birth_date, self.utcnow().isoformat(), user_id),
        )
        self.conn.commit()

    def record_login_reward(self, user_id: int) -> dict[str, Any]:
        user = self.get_user(user_id)
        today = self.today_str()
        if self.has_used_feature_today(user_id, FEATURE_LOGIN_REWARD):
            return {"claimed": False, "tokens": 0, "streak": user["streak_count"], "message": "Today’s login reward has already been claimed."}

        previous_login = user["last_login_date"]
        if self.is_same_day(previous_login, today):
            streak = user["streak_count"]
        elif self.is_next_day(previous_login, today):
            streak = user["streak_count"] + 1
        else:
            streak = 1

        now = self.utcnow().isoformat()
        self.conn.execute(
            "UPDATE users SET astro_token_balance = astro_token_balance + ?, streak_count = ?, last_login_date = ?, updated_at = ? WHERE id = ?",
            (DAILY_LOGIN_REWARD_TOKENS, streak, today, now, user_id),
        )
        self.conn.execute(
            "INSERT INTO token_transactions (user_id, type, source, amount, metadata, created_at) VALUES (?, 'earn', ?, ?, ?, ?)",
            (user_id, SOURCE_DAILY_LOGIN, DAILY_LOGIN_REWARD_TOKENS, json.dumps({"streak": streak}), now),
        )
        self.conn.execute(
            "INSERT INTO usage_logs (user_id, feature_type, usage_date, week_key, tokens_added, tokens_spent, metadata, created_at) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
            (user_id, FEATURE_LOGIN_REWARD, today, self.current_week_key(), DAILY_LOGIN_REWARD_TOKENS, json.dumps({"streak": streak}), now),
        )
        self.conn.commit()
        return {"claimed": True, "tokens": DAILY_LOGIN_REWARD_TOKENS, "streak": streak, "message": f"You earned {DAILY_LOGIN_REWARD_TOKENS} Astro Tokens."}

    def has_used_feature_today(self, user_id: int, feature_type: str) -> bool:
        today = self.today_str()
        result = self.conn.execute(
            "SELECT 1 FROM usage_logs WHERE user_id = ? AND feature_type = ? AND usage_date = ? LIMIT 1",
            (user_id, feature_type, today),
        ).fetchone()
        return result is not None

    def has_used_feature_this_week(self, user_id: int, feature_type: str) -> bool:
        week_key = self.current_week_key()
        result = self.conn.execute(
            "SELECT 1 FROM usage_logs WHERE user_id = ? AND feature_type = ? AND week_key = ? LIMIT 1",
            (user_id, feature_type, week_key),
        ).fetchone()
        return result is not None

    def is_day_one_user(self, user: sqlite3.Row) -> bool:
        return user["created_at"][:10] == self.today_str()

    def get_or_create_horoscope(self, zodiac_sign: str, active_date: str | None = None) -> sqlite3.Row:
        horoscope_date = active_date or self.today_str()
        existing = self.conn.execute(
            "SELECT * FROM horoscopes WHERE zodiac_sign = ? AND date = ?",
            (zodiac_sign, horoscope_date),
        ).fetchone()
        if existing:
            return existing
        title, content = MOCK_HOROSCOPE_TEMPLATES[zodiac_sign]
        now = self.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO horoscopes (zodiac_sign, date, title, content, content_batch, seasonal_period, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (zodiac_sign, horoscope_date, title, content, "mvp-evergreen", "all-season", now),
        )
        self.conn.commit()
        return self.conn.execute(
            "SELECT * FROM horoscopes WHERE zodiac_sign = ? AND date = ?",
            (zodiac_sign, horoscope_date),
        ).fetchone()

    def horoscope_access(self, user: sqlite3.Row) -> FeatureAccessResult:
        if user["plan_type"] == PLAN_PREMIUM:
            if self.has_used_feature_today(user["id"], FEATURE_HOROSCOPE):
                return FeatureAccessResult(False, None, "You already used today’s included horoscope. Come back tomorrow.")
            return FeatureAccessResult(True, SOURCE_PREMIUM_DAILY, "Premium daily horoscope unlocked.")
        if self.is_day_one_user(user):
            if self.has_used_feature_today(user["id"], FEATURE_HOROSCOPE):
                return FeatureAccessResult(False, None, "Your free day-1 horoscope has been used. Spend tokens for another reading.", True, TOKEN_COSTS["extra_horoscope"])
            return FeatureAccessResult(True, SOURCE_FREE_DAY1, "Your day-1 horoscope is ready.")
        return FeatureAccessResult(False, None, "Free users get a day-1 horoscope only. Spend Astro Tokens for an extra reading.", True, TOKEN_COSTS["extra_horoscope"])

    def question_access(self, user: sqlite3.Row) -> FeatureAccessResult:
        if user["plan_type"] == PLAN_PREMIUM:
            if self.has_used_feature_today(user["id"], FEATURE_QUESTION):
                return FeatureAccessResult(False, None, "You already used today’s included AstroAi question. You can unlock an extra one with tokens.", True, TOKEN_COSTS["extra_question"])
            return FeatureAccessResult(True, SOURCE_PREMIUM_DAILY, "Premium daily question unlocked.")
        if self.is_day_one_user(user):
            if self.has_used_feature_today(user["id"], FEATURE_QUESTION):
                return FeatureAccessResult(False, None, "Your free day-1 question has been used. Spend tokens for another answer.", True, TOKEN_COSTS["extra_question"])
            return FeatureAccessResult(True, SOURCE_FREE_DAY1, "Your day-1 AstroAi question is ready.")
        return FeatureAccessResult(False, None, "Free users get one question on day 1. Spend Astro Tokens for more questions.", True, TOKEN_COSTS["extra_question"])

    def meditation_access(self, user: sqlite3.Row) -> FeatureAccessResult:
        if user["plan_type"] == PLAN_PREMIUM:
            return FeatureAccessResult(True, SOURCE_PREMIUM_DAILY, "Premium access includes the current meditation library.")
        if self.has_used_feature_this_week(user["id"], FEATURE_MEDITATION):
            return FeatureAccessResult(False, None, "You already used this week’s free meditation. Reset happens weekly.")
        return FeatureAccessResult(True, SOURCE_FREE_DAY1, "Your weekly meditation is ready.")

    def spend_tokens(self, user_id: int, source: str, amount: int, metadata: dict[str, Any] | None = None) -> tuple[bool, str]:
        user = self.get_user(user_id)
        if user["astro_token_balance"] < amount:
            return False, f"You need {amount} Astro Tokens for this unlock."
        now = self.utcnow().isoformat()
        self.conn.execute(
            "UPDATE users SET astro_token_balance = astro_token_balance - ?, updated_at = ? WHERE id = ?",
            (amount, now, user_id),
        )
        self.conn.execute(
            "INSERT INTO token_transactions (user_id, type, source, amount, metadata, created_at) VALUES (?, 'spend', ?, ?, ?, ?)",
            (user_id, source, amount, json.dumps(metadata or {}), now),
        )
        self.conn.execute(
            "INSERT INTO usage_logs (user_id, feature_type, usage_date, week_key, tokens_added, tokens_spent, metadata, created_at) VALUES (?, ?, ?, ?, NULL, ?, ?, ?)",
            (user_id, FEATURE_TOKEN_SPEND, self.today_str(), self.current_week_key(), amount, json.dumps({"source": source, **(metadata or {})}), now),
        )
        self.conn.commit()
        return True, f"{amount} Astro Tokens spent successfully."

    def consume_horoscope(self, user_id: int, source_type: str, metadata: dict[str, Any] | None = None) -> None:
        now = self.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO usage_logs (user_id, feature_type, usage_date, week_key, tokens_added, tokens_spent, metadata, created_at) VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)",
            (user_id, FEATURE_HOROSCOPE, self.today_str(), self.current_week_key(), json.dumps({"source_type": source_type, **(metadata or {})}), now),
        )
        self.conn.commit()

    def consume_meditation(self, user_id: int, meditation_id: int) -> None:
        now = self.utcnow().isoformat()
        self.conn.execute(
            "INSERT INTO usage_logs (user_id, feature_type, usage_date, week_key, tokens_added, tokens_spent, metadata, created_at) VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)",
            (user_id, FEATURE_MEDITATION, self.today_str(), self.current_week_key(), json.dumps({"meditation_id": meditation_id}), now),
        )
        self.conn.commit()

    def generate_answer(self, user: sqlite3.Row, question_text: str) -> tuple[str, str]:
        content_item = self.conn.execute(
            "SELECT * FROM content_library WHERE status = 'active' ORDER BY priority DESC, id ASC LIMIT 1"
        ).fetchone()
        base_answer = content_item["answer_text"] if content_item else "Your energy invites reflection, grounding, and one brave next step."
        answer = (
            f"{base_answer} \n\nAstroAi senses that {user['zodiac_sign']} energy benefits from focusing on: "
            f"{question_text.strip()[:90] or 'clarity'}, rest, and a simple ritual before bed."
        )
        return answer, SOURCE_CURATED_BANK

    def submit_question(self, user: sqlite3.Row, question_text: str, source_type: str) -> sqlite3.Row:
        answer_text, answer_source = self.generate_answer(user, question_text)
        now = self.utcnow().isoformat()
        stored_source = source_type if source_type != SOURCE_TOKEN_UNLOCK else answer_source
        cursor = self.conn.execute(
            "INSERT INTO question_history (user_id, question_text, answer_text, source_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (user["id"], question_text, answer_text, stored_source, now),
        )
        self.conn.execute(
            "INSERT INTO usage_logs (user_id, feature_type, usage_date, week_key, tokens_added, tokens_spent, metadata, created_at) VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)",
            (user["id"], FEATURE_QUESTION, self.today_str(), self.current_week_key(), json.dumps({"source_type": source_type, "answer_source": answer_source}), now),
        )
        self.conn.commit()
        return self.conn.execute("SELECT * FROM question_history WHERE id = ?", (cursor.lastrowid,)).fetchone()

    def list_meditations(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM meditations ORDER BY id ASC").fetchall()

    def get_meditation(self, meditation_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM meditations WHERE id = ?", (meditation_id,)).fetchone()

    def get_dashboard_state(self, user: sqlite3.Row) -> dict[str, Any]:
        return {
            "today_horoscope_used": self.has_used_feature_today(user["id"], FEATURE_HOROSCOPE),
            "today_question_used": self.has_used_feature_today(user["id"], FEATURE_QUESTION),
            "today_login_claimed": self.has_used_feature_today(user["id"], FEATURE_LOGIN_REWARD),
            "week_meditation_used": self.has_used_feature_this_week(user["id"], FEATURE_MEDITATION),
            "week_key": self.current_week_key(),
        }

    def recent_questions(self, user_id: int, limit: int = 5) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM question_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    def recent_transactions(self, user_id: int, limit: int = 8) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM token_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    def upgrade_to_premium(self, user_id: int) -> None:
        now = self.utcnow().isoformat()
        self.conn.execute("UPDATE users SET plan_type = 'premium', updated_at = ? WHERE id = ?", (now, user_id))
        self.conn.execute("UPDATE subscriptions SET status = 'inactive', updated_at = ? WHERE user_id = ? AND status = 'active'", (now, user_id))
        self.conn.execute(
            "INSERT INTO subscriptions (user_id, plan_type, status, provider, provider_reference, started_at, ends_at, updated_at) VALUES (?, 'premium', 'active', 'mock-stripe-ready', 'premium-mvp', ?, NULL, ?)",
            (user_id, now, now),
        )
        self.conn.commit()

    def forgot_password(self, email: str) -> str:
        user = self.get_user_by_email(email)
        if not user:
            return "If that email exists, a reset link would be sent."
        token = f"reset-{user['id']}-{self.utcnow().timestamp():.0f}"
        self.conn.execute("UPDATE users SET reset_token = ?, updated_at = ? WHERE id = ?", (token, self.utcnow().isoformat(), user["id"]))
        self.conn.commit()
        return f"Reset flow prepared for {email}. MVP token: {token}"

    def token_store_items(self) -> list[dict[str, Any]]:
        return [
            {"key": SOURCE_NATAL_CHART, "label": "Short natal chart reading", "description": "A brief cosmic personality snapshot.", "cost": TOKEN_COSTS["natal_chart"]},
            {"key": SOURCE_ASTROLOGY_READING, "label": "Short astrology reading", "description": "A compact timing and guidance reading.", "cost": TOKEN_COSTS["astrology_reading"]},
            {"key": SOURCE_EXTRA_QUESTION, "label": "Extra AstroAi question", "description": "Unlock an additional answer beyond your plan.", "cost": TOKEN_COSTS["extra_question"]},
        ]
