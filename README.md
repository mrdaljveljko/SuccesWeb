# AstroAi MVP

AstroAi is a mobile-first astrology and spiritual guidance MVP built with Flask and SQLite. It includes authentication, free vs premium plan logic, daily horoscope gating, AstroAi question handling, meditation access, daily streak rewards, Astro Tokens, and a content-friendly architecture ready for future AI or manually curated expansion.

## Project overview

AstroAi is designed around three product layers:

- **Free plan**: valuable but limited access, including a day-1 horoscope, a day-1 AstroAi question, one weekly meditation, and streak-driven Astro Tokens.
- **Premium plan**: daily horoscope access, one included AstroAi question per day, premium indicators, and a clean upgrade flow.
- **Astro Tokens**: an internal currency earned through daily login streaks and spent on extra readings or unlocked features.

The app uses server-rendered Flask pages with a modern mystical dark UI, subtle animations, and a scalable data model for future content editing and premium expansion.

## Features included now

### Final AstroAi routes

- `/`
- `/register`
- `/login`
- `/forgot-password`
- `/logout`
- `/dashboard`
- `/horoscope`
- `/ask`
- `/meditation`
- `/tokens`
- `/upgrade`
- `/profile`

- Landing page with product positioning
- Register / login / logout / forgot password flow
- Protected app routes
- Dashboard with plan badge, token balance, streak, and usage status
- Daily horoscope page with plan-aware gating
- Ask AstroAi page with usage tracking and placeholder answer generation
- Meditation page with weekly access tracking
- Astro Token rewards and token spend tracking
- Upgrade to Premium page with mock subscription activation
- Profile page with future-ready user fields
- Content library and content version tables for future manual edits

## Tech stack

- Python 3
- Flask
- SQLite
- Werkzeug password hashing

## Setup instructions

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open the app at `http://localhost:8000`.

## Environment instructions

AstroAi currently uses local defaults in `astro_config.py`.

Important values you can change there:

- `SECRET_KEY`
- `DATABASE_PATH`
- `DAILY_LOGIN_REWARD_TOKENS`
- `TOKEN_COSTS`
- plan constants and feature identifiers

If you want to productionize it later, move those constants into environment variables and keep the same config interface.

## How plan logic works

### Free plan

A free user gets:

- **Day 1 only**: 1 free horoscope
- **Day 1 only**: 1 free AstroAi question
- **Every week**: 1 free meditation
- **Every valid daily login**: Astro Tokens from the streak reward

After day 1, free users can continue unlocking extra features using Astro Tokens.

### Premium plan

A premium user gets:

- 1 daily horoscope every day
- 1 included AstroAi question every day
- premium badge / upgraded status in the UI
- tokens still tracked, but included daily features do not depend on token balance

The upgrade flow is currently mock-activated, but the app stores a subscription record so Stripe can be integrated cleanly later.

## How token logic works

Default token economy:

- Daily login reward = **5 Astro Tokens**
- Short natal chart reading = **25 tokens**
- Short astrology reading = **15 tokens**
- Extra AstroAi question = **10 tokens**
- Extra horoscope unlock = **10 tokens**

Server-side rules:

- token balance can never go negative
- all token spending is validated before deduction
- every earn/spend action creates a `token_transactions` record
- important usage events are also mirrored into `usage_logs`

## How streak logic works

- Logging in once per day can claim a reward exactly once per calendar day
- consecutive days increase `streak_count`
- missing a day resets the streak to 1 on the next successful claim
- the login reward updates both the user balance and a token transaction log
- streak and reward logic are centralized in `AstroService.record_login_reward`

## How content is structured for future manual editing

AstroAi intentionally avoids hardcoding final answers into business logic.

Instead, the MVP includes:

- `content_library` table for curated answers, FAQ entries, and seasonal content
- `content_versions` table for batch/version control
- horoscope records stored by `zodiac_sign + date`
- meditation records stored independently from gating logic
- a service-layer answer generator that can later switch between curated content, OpenAI, another LLM, or seasonal logic without rewriting route handlers

Current placeholder content lives in:

- `astro_content.py` for zodiac signs, mock horoscope templates, meditations, and starter content library entries

## Placeholder vs future-ready integrations

### Placeholder in MVP

- horoscope text content
- AstroAi answers
- forgot password delivery
- premium activation billing flow
- meditation content is text-based instead of full audio

### Already structured for future integration

- OpenAI or another LLM for answer generation
- AI-generated daily horoscopes
- admin-editable curated content
- Stripe subscriptions
- richer user birth data and natal chart storage
- audio meditation library
- content rotation by time period or trend

## Data model summary

The MVP creates tables for:

- `users`
- `horoscopes`
- `meditations`
- `question_history`
- `usage_logs`
- `token_transactions`
- `subscriptions`
- `content_library`
- `content_versions`

This structure supports future natal chart data, subscription billing status, curated answer banks, seasonal content batches, and personalization features.

## Run tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## FUTURE UPGRADES

- full natal chart readings
- real AI-generated answers
- real AI-generated horoscopes
- payment integration
- referral system
- push notifications
- audio meditation library
- advanced user birth data inputs
- admin content editing panel
- seasonal and trend-based answer rotation
