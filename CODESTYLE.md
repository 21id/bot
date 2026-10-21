# 21ID Bot — Code Style

Match the existing code. When unsure, open the nearest neighbour (same folder, same
kind of file) and copy its shape. The smallest diff that solves the task wins.

## Formatting & tooling

- Python 3.14, **Black** (line length **88**), **flake8** (`.flake8`: annotations,
  Google docstrings, bugbear, return, complexity), **mypy** (`mypy.ini`, strict).
- Install dev tools with `pip install -r requirements-dev.txt`.
- Every `def` has type hints; void handlers return `-> None` explicitly.
- Google-style docstring on every public function/class — one line is fine
  (`"""Handling chat joins."""`).
- No bare `except:`. Catch `TelegramAPIError`, `aiosmtplib.SMTPException`, or
  `Exception as e` and report with `sentry_sdk.capture_exception(e)`.

## Imports

Order used throughout the repo (blank line between groups):

```python
import html                                   # 1. stdlib

from app.bootstrap import Container           # 2. app.* (project)
from app.bot.i18n.core import I18nContext
from app.bot.routers.user.search.router import router

from aiogram import Bot, F                    # 3. third-party
from aiogram.types import Message
```

Long `app.*` imports wrap with parentheses aligned to the opening bracket:

```python
from app.bot.routers.user.registration.keyboards import (nickname_back as
                                                         nickname_back_kb)
```

## Naming

- `snake_case` everywhere; handlers are named after the action
  (`nickname`, `code_verification`, `join_request`, `inline_query`).
- A local that shadows the handler name gets a trailing underscore (`nickname_`).
- Keyboard modules expose `get(...) -> InlineKeyboardMarkup`; import them as
  `<name>_kb` (`menu_kb.get(i18n)`).
- `CallbackData` classes are PascalCase nouns/verbs with a short `prefix=`
  (`StartRegistration`, `SendNotification`).
- i18n keys are kebab-case, prefixed by feature: `nickname-…`, `verification-…`,
  `migration-otp-…`, `inline-…`, `btn-…`.

## Handlers

Write handlers at the density of `nickname.py`, `verification.py`, `inline.py`:

- sequential checks with **early `return`**;
- local `text` / `keyboard` variables, one reply at the end;
- no helper functions for 2–3 line operations, no new base classes;
- duplication between sibling handlers is acceptable (see `set_join_rules.py`).

```python
@router.callback_query(SendNotification.filter())
async def notify_user(
    callback: CallbackQuery, callback_data: SendNotification,
    container: Container, bot: Bot, i18n: I18nContext,
) -> None:
    """Sending notification to the searched user."""
    sender = await container.user_service.get_by_telegram_id(callback.from_user.id)
    if not sender:
        await callback.answer(i18n.get("notify-not-registered"), show_alert=True)
        return
    ...
```

- Dependencies come from handler parameters: `container: Container`, `bot: Bot`,
  `state: FSMContext`, `i18n: I18nContext`, `callback_data: ...`. Never globals,
  never `os.getenv` inside handlers (use `container.admin_id`).
- Handlers that serve both `Message` and `CallbackQuery` reply through
  `app/bot/utilities/reply_edit.answer(request, text=..., reply_markup=...)`.
- Bot API methods without a shortcut: `await bot(ApproveChatJoinRequest(...))`.
- FSM data is serialised with `model_dump(mode="json")`.

## Filters

- Router-wide filters go in `register_filters()` of the feature's `router.py`.
- Combine **magic filters** with operators: `F.text.regexp(...) & ...`, `~F.x`.
- Combine **class filters** with `and_f` / `or_f` / `invert_f` from
  `aiogram.filters`. Never use Python `and` / `or` on filters — it silently drops
  one side.
- Nicknames are validated with `^[A-Za-z]{1,8}$` and lower-cased before use.

## User-facing text

- All text goes through `i18n.get("key", **placeholders)`; add the key to **every**
  file in `app/bot/locales/` (en, ru, uz, uz_new, tg) with the same placeholders.
- Style: emoji prefix (👋 ⚠️ ❗️ 🪪 ✅ ❌ ℹ️), short sentences, numbered steps when
  the user must act, support contact `@megaplov`.
- Never put exception text (`str(e)`) into user messages. Users see a generic text
  plus the error UUID; details go to Sentry/Bugsink and the admin.
- Anything sent with `ParseMode.HTML` escapes data with `html.escape(...)`.

## Domain & infrastructure

- Domain models extend `BaseModel_` (Pydantic v2); Mongo aliases live on the model
  (`login → nickname`, `className → wave_name`).
- Repositories return raw `dict`s; services build and return domain models.
- Handlers call services/clients from `Container`, never repositories.
- Datetimes are timezone-aware UTC: `datetime.now(UTC)`.
- User-facing failures raise `BaseError` subclasses (`client_message`,
  `support_details`, `notify_user`).
- Schema/data changes ship as a migration module in
  `app/infrastructure/mongodb/migrations/` (`mNNN_name.py`), registered in the
  runner list.

## Errors & observability

- `sentry_sdk` (reporting to Bugsink) is the only error/log sink — no stdlib
  `logging`, no `print` (except "Started/Stopped polling").
- Use `capture_exception` for swallowed errors that matter, `add_breadcrumb` for
  retries/reconnects. No PII (emails, OTPs) in messages or breadcrumbs.

## Comments

Explain non-obvious business logic only (`# Telegram unreachable — fall back to
email automatically`). Use `# TODO:` sparingly, in place.

## Tests

- Live in `app/tests/` (`unit/`, `integration/`). Integration tests use
  testcontainers for Mongo/Redis.
- Run with `scripts/test.sh` (all) or `scripts/test.sh <module>`.
