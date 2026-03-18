from __future__ import annotations

from datetime import date, timedelta

ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

MOCK_HOROSCOPE_TEMPLATES = {
    "Aries": ("Spark the first move", "Today rewards brave action, but only after a moment of stillness. Trust your momentum and protect your peace."),
    "Taurus": ("Root into abundance", "Your calm presence becomes magnetic today. Create beauty around you and let practical choices guide emotional clarity."),
    "Gemini": ("Words become portals", "A timely conversation opens a fresh path. Ask better questions, listen twice, and let curiosity become your compass."),
    "Cancer": ("Softness is strength", "Nurture your inner world before giving to others. Boundaries built with compassion become a source of healing today."),
    "Leo": ("Radiance with purpose", "You are noticed when you lead from the heart. Share your light generously, but save energy for what truly matters."),
    "Virgo": ("Align the details", "Order brings relief. Small refinements made today create spiritual spaciousness and make tomorrow feel much easier."),
    "Libra": ("Choose what feels balanced", "Harmony returns when you stop overexplaining. Let elegance and honesty coexist in every decision you make."),
    "Scorpio": ("Transform quietly", "Something hidden becomes clear. Protect your intuition, release what has expired, and let mystery work in your favor."),
    "Sagittarius": ("Expand with intention", "Adventure is calling, but discernment sharpens the reward. Follow what inspires you without ignoring the practical next step."),
    "Capricorn": ("Build what lasts", "Steady effort is sacred today. Your discipline creates more freedom than you realize, especially in love and money."),
    "Aquarius": ("Vision meets timing", "Your future-facing ideas need a grounded ritual. Share the unusual insight and let community mirror its value back to you."),
    "Pisces": ("Intuition in motion", "Dreamy clarity arrives through action. Move gently, trust symbolic nudges, and let your imagination become guidance."),
}

MOCK_MEDITATIONS = [
    {
        "title": "Moon Breath Reset",
        "description": "A grounding 6-minute breathing ritual for emotional clarity.",
        "duration": "6 min",
        "content_type": "text",
        "text_content": "Close your eyes. Inhale for four, hold for four, exhale for six. Visualize a silver moon above your crown with each breath.",
    },
    {
        "title": "Solar Confidence Scan",
        "description": "A confidence-building body scan with warm, radiant imagery.",
        "duration": "8 min",
        "content_type": "text",
        "text_content": "Imagine golden light moving from your chest to your fingertips. Release self-doubt with every exhale and call your energy back.",
    },
    {
        "title": "Starlight Sleep Journal",
        "description": "A gentle evening reflection practice with journaling prompts.",
        "duration": "10 min",
        "content_type": "text",
        "text_content": "Write down what felt aligned today, what felt heavy, and what you want the stars to hold overnight.",
    },
]

MOCK_CONTENT_LIBRARY = [
    {
        "category": "faq",
        "title": "What should I focus on this week?",
        "question_text": "What should I focus on this week?",
        "answer_text": "Focus on one relationship, one habit, and one financial choice. Small alignment creates the biggest spiritual signal.",
        "content_period": "evergreen",
        "priority": 10,
        "tags": "weekly,focus,guidance",
        "status": "active",
    },
    {
        "category": "seasonal",
        "title": "How can I move through a transition?",
        "question_text": "How can I move through a transition?",
        "answer_text": "Transitions ask for gentleness and rhythm. Notice what is leaving, bless it, and give the new chapter a ritual welcome.",
        "content_period": "seasonal",
        "priority": 9,
        "tags": "transitions,seasonal,healing",
        "status": "active",
    },
    {
        "category": "faq",
        "title": "What energy surrounds my love life?",
        "question_text": "What energy surrounds my love life?",
        "answer_text": "Love responds to clarity today. Say what you mean softly, receive what is offered honestly, and let mutual effort guide you.",
        "content_period": "monthly",
        "priority": 8,
        "tags": "love,relationships,clarity",
        "status": "active",
    },
]

MOCK_CONTENT_VERSIONS = [
    {
        "name": "MVP Evergreen Guidance",
        "description": "Starter placeholder answer bank for early MVP testing.",
        "active_from": date.today().isoformat(),
        "active_until": (date.today() + timedelta(days=365)).isoformat(),
        "status": "active",
    }
]
