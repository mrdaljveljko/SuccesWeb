from __future__ import annotations

import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from astro_config import (
    APP_NAME,
    DATABASE_PATH,
    DEFAULT_PLAN,
    FREE_FEATURES,
    PLAN_PREMIUM,
    PREMIUM_FEATURES,
    SECRET_KEY,
    SESSION_USER_KEY,
    TOKEN_COSTS,
)
from astro_content import ZODIAC_SIGNS
from astro_services import AstroService

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["APP_NAME"] = APP_NAME
Path("instance").mkdir(exist_ok=True)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def get_service() -> AstroService:
    if "astro_service" not in g:
        g.astro_service = AstroService(get_db())
        g.astro_service.initialize()
    return g.astro_service


@app.teardown_appcontext
def close_db(_error: Exception | None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.context_processor
def inject_globals():
    user = None
    if session.get(SESSION_USER_KEY):
        user = get_service().get_user(session[SESSION_USER_KEY])
    return {
        "app_name": APP_NAME,
        "current_user": user,
        "plan_free": DEFAULT_PLAN,
        "plan_premium": PLAN_PREMIUM,
        "premium_features": PREMIUM_FEATURES,
        "free_features": FREE_FEATURES,
        "token_costs": TOKEN_COSTS,
        "zodiac_signs": ZODIAC_SIGNS,
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get(SESSION_USER_KEY):
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def build_dashboard_view_model(user, service: AstroService) -> dict:
    state = service.get_dashboard_state(user)
    horoscope_access = service.horoscope_access(user)
    question_access = service.question_access(user)
    meditation_access = service.meditation_access(user)
    return {
        "state": state,
        "horoscope_access": horoscope_access,
        "question_access": question_access,
        "meditation_access": meditation_access,
        "welcome_mode": service.is_day_one_user(user),
        "streak_goal": max(7, ((user["streak_count"] // 7) + 1) * 7),
        "streak_progress": min(100, int((user["streak_count"] / max(7, ((user["streak_count"] // 7) + 1) * 7)) * 100)) if user["streak_count"] else 0,
    }


@app.get("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    service = get_service()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        zodiac_sign = request.form.get("zodiac_sign", "")
        birth_date = request.form.get("birth_date") or None

        if not name or not email or not password or zodiac_sign not in ZODIAC_SIGNS:
            flash("Please complete all required fields and choose a zodiac sign.", "error")
        elif service.get_user_by_email(email):
            flash("An account with that email already exists.", "error")
        else:
            user = service.create_user(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                zodiac_sign=zodiac_sign,
                birth_date=birth_date,
            )
            session[SESSION_USER_KEY] = user["id"]
            reward = service.record_login_reward(user["id"])
            flash("Welcome to AstroAi. Your cosmic profile is ready.", "success")
            if reward["claimed"]:
                flash(reward["message"], "reward")
            return redirect(url_for("dashboard"))
    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    service = get_service()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = service.get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
        else:
            session[SESSION_USER_KEY] = user["id"]
            reward = service.record_login_reward(user["id"])
            flash("Welcome back.", "success")
            if reward["claimed"]:
                flash(reward["message"], "reward")
            else:
                flash(reward["message"], "info")
            return redirect(url_for("dashboard"))
    return render_template("auth/login.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    service = get_service()
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        flash(service.forgot_password(email), "info")
    return render_template("auth/forgot_password.html")


@app.post("/logout")
def logout():
    session.clear()
    flash("You’ve been logged out.", "info")
    return redirect(url_for("landing"))


@app.get("/dashboard")
@login_required
def dashboard():
    service = get_service()
    user = service.get_user(session[SESSION_USER_KEY])
    view_model = build_dashboard_view_model(user, service)
    return render_template(
        "app/dashboard.html",
        user=user,
        transactions=service.recent_transactions(user["id"]),
        recent_questions=service.recent_questions(user["id"]),
        meditations=service.list_meditations(),
        token_items=service.token_store_items(),
        **view_model,
    )


@app.route("/horoscope", methods=["GET", "POST"])
@login_required
def horoscope():
    service = get_service()
    user = service.get_user(session[SESSION_USER_KEY])
    access = service.horoscope_access(user)
    unlocked = None

    if request.method == "POST":
        if request.form.get("action") == "unlock_tokens":
            success, message = service.spend_tokens(user["id"], "extra_horoscope", TOKEN_COSTS["extra_horoscope"], {"feature": "horoscope"})
            if success:
                service.consume_horoscope(user["id"], "token_unlock", {"feature": "horoscope"})
                unlocked = service.get_or_create_horoscope(user["zodiac_sign"])
                flash("Extra horoscope unlocked with Astro Tokens.", "success")
            else:
                flash(message, "error")
        elif access.allowed and access.source_type:
            service.consume_horoscope(user["id"], access.source_type)
            unlocked = service.get_or_create_horoscope(user["zodiac_sign"])
            flash(access.message, "success")
        else:
            flash(access.message, "error")
        user = service.get_user(user["id"])
        access = service.horoscope_access(user)

    if not unlocked and service.has_used_feature_today(user["id"], "horoscope"):
        unlocked = service.get_or_create_horoscope(user["zodiac_sign"])

    return render_template("app/horoscope.html", user=user, access=access, horoscope=unlocked)


@app.route("/ask", methods=["GET", "POST"])
@login_required
def ask():
    service = get_service()
    user = service.get_user(session[SESSION_USER_KEY])
    access = service.question_access(user)
    answer = None

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        unlock_with_tokens = request.form.get("action") == "unlock_tokens"
        if not question_text:
            flash("Ask AstroAi a question first.", "error")
        elif unlock_with_tokens:
            success, message = service.spend_tokens(user["id"], "extra_question", TOKEN_COSTS["extra_question"], {"feature": "question"})
            if success:
                answer = service.submit_question(user, question_text, "token_unlock")
                flash("Extra question unlocked with Astro Tokens.", "success")
            else:
                flash(message, "error")
        elif access.allowed and access.source_type:
            answer = service.submit_question(user, question_text, access.source_type)
            flash(access.message, "success")
        else:
            flash(access.message, "error")
        user = service.get_user(user["id"])
        access = service.question_access(user)

    return render_template("app/ask.html", user=user, access=access, answer=answer, recent_questions=service.recent_questions(user["id"], 6))


@app.route("/meditation", methods=["GET", "POST"])
@login_required
def meditation():
    service = get_service()
    user = service.get_user(session[SESSION_USER_KEY])
    access = service.meditation_access(user)
    meditations = service.list_meditations()
    active = meditations[0] if meditations else None

    if request.method == "POST":
        selected_id = int(request.form.get("meditation_id", 0))
        active = service.get_meditation(selected_id) or active
        if access.allowed and active:
            if user["plan_type"] != PLAN_PREMIUM:
                service.consume_meditation(user["id"], active["id"])
            flash("Meditation unlocked. Breathe in slowly and settle into the moment.", "success")
        else:
            flash(access.message, "error")
        user = service.get_user(user["id"])
        access = service.meditation_access(user)

    return render_template("app/meditation.html", user=user, access=access, meditations=meditations, active=active)


@app.route("/tokens", methods=["GET", "POST"])
@login_required
def tokens():
    service = get_service()
    user = service.get_user(session[SESSION_USER_KEY])
    if request.method == "POST":
        source = request.form.get("source")
        item = next((item for item in service.token_store_items() if item["key"] == source), None)
        if not item:
            flash("Unknown token unlock selected.", "error")
        else:
            success, message = service.spend_tokens(user["id"], item["key"], item["cost"], {"label": item["label"]})
            if success:
                flash(f"Unlocked: {item['label']}", "success")
            else:
                flash(message, "error")
        user = service.get_user(user["id"])
    return render_template("app/tokens.html", user=user, items=service.token_store_items(), transactions=service.recent_transactions(user["id"], 12))


@app.route("/upgrade", methods=["GET", "POST"])
@login_required
def upgrade():
    service = get_service()
    user = service.get_user(session[SESSION_USER_KEY])
    if request.method == "POST" and user["plan_type"] != PLAN_PREMIUM:
        service.upgrade_to_premium(user["id"])
        flash("Premium activated in MVP mode. Stripe-ready structure can be added next.", "success")
        return redirect(url_for("dashboard"))
    return render_template("app/upgrade.html", user=user)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    service = get_service()
    user = service.get_user(session[SESSION_USER_KEY])
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        zodiac_sign = request.form.get("zodiac_sign", "")
        birth_date = request.form.get("birth_date") or None
        if not name or zodiac_sign not in ZODIAC_SIGNS:
            flash("Please keep your name and zodiac sign valid.", "error")
        else:
            service.update_profile(user["id"], name=name, zodiac_sign=zodiac_sign, birth_date=birth_date)
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))
    return render_template("app/profile.html", user=user)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
