# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A WhatsApp chatbot built with Flask and the Meta WhatsApp Business API (Cloud API v17.0). The bot runs a Hebrew-language "mystery/reveal" game: users trigger a guessing game by messaging trigger words, and the bot counts guesses before revealing an answer. It is deployed on a platform like Render or Railway (uses a `PORT` env var).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (dev server)
python main.py

# Run with gunicorn (production-style)
gunicorn main:app
```

There are no tests or a linter configured in this project.

## Environment Variables

The app reads four env vars at runtime — these must be set before running:

| Variable | Purpose |
|---|---|
| `VERIFY_TOKEN` | Shared secret for Meta's webhook verification handshake (GET `/webhook`) |
| `PHONE_NUMBER_ID` | Meta WhatsApp Business phone number ID (used in the send URL) |
| `ACCESS_TOKEN` | Meta permanent or temporary access token for the WhatsApp API |
| `PORT` | HTTP port (defaults to `10000` if unset) |

## Architecture

All logic lives in `main.py`. There is no database — state is held in the module-level dict `reveal_state`, meaning it resets on every process restart and is not thread-safe under concurrent workers.

**Webhook flow:**
- `GET /webhook` — Meta's verification challenge. Returns `hub.challenge` if `hub.verify_token` matches `VERIFY_TOKEN`, else 403.
- `POST /webhook` — Receives message events from Meta, extracts the sender number and message body, passes the text through `get_reveal_logic()`, and calls `send_whatsapp_message()` to reply via the Graph API.

**Game logic (`get_reveal_logic`):**
- Activated when the user message contains `"תעלומה"` or `"משחק"`.
- Tracks guess count in `reveal_state["guesses"]`; gives two hints before the final reveal at guess ≥ 3.
- `reveal_state["answer"]` and `reveal_state["mystery"]` are hardcoded strings — change these to customize the game.

**Sending messages (`send_whatsapp_message`):**
- POSTs to `https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages` with a JSON text payload.
