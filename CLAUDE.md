# CLAUDE.md

Guidance for Claude Code (and other agents) working in this repository.
Code style lives in [CODESTYLE.md](CODESTYLE.md) — read it before writing code.

## What 21ID is

21ID is an open-source identity system for **School 21** students (built by the
Tashkent and Samarkand campus students). It confirms that a Telegram user is a real
School 21 student by:

1. looking the nickname up in the **School 21 Platform API**, then
2. verifying ownership via a one-time code sent to `{nickname}@student.21-school.ru`.

Verified students can join community Telegram chats (join requests are approved
automatically according to each chat's policy), search peers, notify them and
invite unregistered peers.

**Roadmap** — keep these in mind when designing changes:
- more verification methods (e-mail **+ Face ID**) — the backend has a pluggable
  verification layer (`app/domain/verification/`), the bot UI exposes e-mail only;
- 21ID as an **OAuth server** for outside websites — the user's identity is the
  Mongo `_id`, Telegram is just one linked account. Don't couple domain logic to
  `telegram_id`.

This repo is the Telegram bot. Sibling repos: `../auth-api`, `../21face`.

## Stack

Python 3.14 · aiogram 3 (polling, Redis FSM storage) · MongoDB via Motor · Redis ·
aiosmtplib (Brevo SMTP relay, port 587 STARTTLS) + Jinja2 templates · Pydantic v2 ·
sentry-sdk → **Bugsink** for errors · Docker (non-root), GHCR.

## Layout

```
app/
  __main__.py          env validation, sentry init → bootstrap() → bot.main()
  bootstrap.py         builds infra → repos → services; returns Container (DI)
  bot/                 Telegram layer only (aiogram)
    bot.py             Dispatcher, middlewares, RedisStorage (TTL), polling, shutdown
    i18n/              I18nCore (loads locales/*.json), I18nMiddleware (+ db_user)
    locales/           en, ru, uz (old Latin), uz_new (new Latin), tg — same keys everywhere
    middlewares/       ErrorMiddleware (Sentry + one admin message + user UUID)
    filters/           UserExists, UserVerified, IsAdmin
    routers/
      default/         /cancel, no-op callbacks
      user/            private chat: registration, approve_join, menu, search,
                       invite, migration, language
      chat/            groups: join (welcome/ID card), admins (/base_create, …)
    utilities/         reply_edit.answer, message_split
  domain/              models + thin services (user, chat, campus, verification)
  infrastructure/      mongodb (client, repositories, migrations), s21 API client,
                       mailer, verification providers
  utilities/           random (OTP generators)
  tests/               unit/ and integration/ (testcontainers)
scripts/               build.sh, test.sh
```

Feature folder pattern under `routers/`: `router.py` (+ `register_filters()`),
`callback.py`, `states.py`, `handlers/*.py`, `keyboard(s)/*.py`.

## Key flows

- **Registration**: `/start` → nickname (`^[A-Za-z]{1,8}$`) → S21 API lookup →
  e-mail OTP (rate-limited) → code check (10 attempts) → user verified; pending chat
  join request approved/declined by chat policy (core / intensive).
- **Account migration**: nickname already bound to another Telegram → migration OTP
  to the old account (DM, falls back to e-mail) → on success the account moves, the
  old account is notified. Also a menu flow with 3 confirmations.
- **Invite**: inline search finds an unregistered S21 student → invite e-mail with a
  deeplink OTP (expires in 7 days). Invited-but-unregistered users are treated as
  **non-existent** in search, mentions and notifications.
- **Mass-invite** (*temporary*, isolated in `routers/user/mass_invite/`,
  `domain/mass_invite/`, `mass_invite` collection): owner (`ADMIN_ID`) sends
  `/mass_invite` + nicknames → link `t.me/<bot>?start=mi_<token>` (30 days). Student
  sends his nickname (5 tries/hour); if it's in the list and free → verified without
  OTP (`VerificationMethod.MASS_INVITE`), otherwise asked to contact @megaplov.
- **Errors**: `ErrorMiddleware` catches everything; users only ever see
  `BaseError.client_message` or a generic text plus the error UUID.

## Commands

```bash
pip install -r requirements-dev.txt
python -m app                                       # needs env vars, see materials/.env.sample
docker compose -f docker-compose.dev.yml up -d      # Bugsink + Mongo + Redis for dev
scripts/test.sh                                     # all tests
scripts/test.sh unit | integration | <module>       # subset
flake8 app && black --check app && mypy app
```

Required env vars are listed in `materials/.env.sample` (`BOTAPI_TOKEN`,
`ADMIN_ID`, `MONGO_*`, `REDIS_*`, `S21API_*`, `SMTP_*`, `TEMPLATES_BASEDIR`,
optional `SENTRY_DSN`, `ENVIRONMENT`).

## Rules for changes

- Follow [CODESTYLE.md](CODESTYLE.md): smallest diff, no new abstractions without
  precedent, same density as neighbouring handlers.
- Every new user-facing string → all four locale files, same placeholders.
- DB schema/data change → new migration in `app/infrastructure/mongodb/migrations/`.
  Migration 001 refuses to run when duplicate nicknames/telegram_ids exist — fix
  data by hand.
- Errors go to `sentry_sdk`, never `print`/`logging`; no PII in events.
- Anything that sends e-mail or messages to a third party must be rate-limited via
  Redis (`rl:*` keys, `SET NX EX`).
- Nicknames: ASCII letters only, 1–8 chars; workstation location is not sensitive.
- Branches: work on `develop`; `main` is releases. **Do not commit or push unless the
  maintainer asks** — leave changes for review.
