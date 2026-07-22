# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

MINOLA is a Hebrew-language (RTL) personalized-gifts business. The repo holds two unrelated-but-cohabiting things:

1. **A static storefront** — `index.html` (catalog/landing page), `finder.html` (gift-finder quiz), and `products.js` (shared product catalog). There is no backend, cart, or checkout: every "buy" action is a `https://wa.me/972502733773?text=...` deep link that opens a pre-filled WhatsApp order message.
2. **A Flask WhatsApp chatbot** — `main.py`, using the Meta WhatsApp Business Cloud API (v17.0). It runs a Hebrew "mystery/reveal" guessing game.

There is also `michali-os.html`, a standalone gamified personal life-management app ("מיכלי OS") unrelated to the store.

Everything is Hebrew-first: pages use `dir="rtl"`, UI strings and code comments are in Hebrew.

## Commands

```bash
# Install bot dependencies
pip install -r requirements.txt

# Run the bot locally (dev server)
python main.py

# Run the bot with gunicorn (production-style)
gunicorn main:app

# Preview the static pages (any static server works)
python -m http.server 8080   # then open /index.html, /finder.html, /michali-os.html
```

There is no build system, bundler, test suite, or linter. The HTML pages are single-file vanilla JS/CSS (fonts loaded from Google Fonts).

## Working With Large Files — Important

`index.html` (~1.7 MB) and `products.js` (~1.6 MB) are huge because product images are embedded as base64 data URIs. **Never read these files whole** — use Grep, or Read with `offset`/`limit`. The actual JavaScript logic is a small fraction of each file:

- `index.html`: markup/styles first; scripts start around line 979, and the chat-widget logic follows `<script src="products.js">` near line 1017.
- `products.js`: one `DATA = [...]` array on a single enormous line, followed by a short normalization block at the end of the file.

## Architecture

### products.js — single source of truth for products

Loaded by both `index.html` and `finder.html`. To add/edit products, edit the `DATA` array here only (the file's header comment says exactly this, in Hebrew).

Each product uses short field names, normalized at load time into aliases the finder expects:

| Short field | Alias(es) | Meaning |
|---|---|---|
| `n` | `title` | Product name (Hebrew) |
| `p` | `price` | Price string, e.g. `"₪89"` |
| `t` | `tags`, `productCategory` (first tag) | Category tags (Hebrew) |
| `aud` | — | Audience keys: `woman`, `man`, `kid`, `teen`, `baby`, `family`, `boss`, `teacher` |
| `img` | `thumbnailUrl` | Base64 data URI **or** `images/NN.jpg` path |
| `wa` | — | Pre-built `wa.me` order link with URL-encoded Hebrew order template |

Normalization also stamps `id` (`p0`, `p1`, …), `showClient: true`, and `brandFeatured: false` defaults, then exposes globals: `window.MINOLA_PHONE` (`"972502733773"`), `window.MINOLA_PRODUCTS`, and `window.MINOLA_ITEMS` (same array; the name `finder.html` reads).

**Gotcha:** roughly half the products reference `images/NN.jpg`, but there is no `images/` directory in this repo — those thumbnails 404 unless the images are deployed alongside the pages. The rest embed base64 data URIs.

### index.html — catalog / landing page

Static marketing page plus product sections with hardcoded `wa.me` order links. At the bottom is an embedded chat-widget "gift assistant" (`#mbot`): a scripted quick-reply flow (recipient → budget) that filters `MINOLA_PRODUCTS` by `aud` and parsed price, shows up to 6 matches, and falls back to a human-handoff WhatsApp link. The `RC` map in that script maps recipient keys to category tags.

### finder.html — gift-finder quiz

A mobile-phone-styled (393px shell) multi-screen quiz app: splash → questions → results. Reads `window.MINOLA_ITEMS`, filters by answers, and builds a WhatsApp order link from `window.MINOLA_PHONE`. Screens are `.screen` divs toggled with a `.hidden` class via `showScreen()`.

### michali-os.html — "מיכלי OS" life-game app

Fully self-contained, mobile-only, no relation to the store or `products.js`. All state lives in `localStorage` under key `michali_os_v1` — daily tasks, moods, score/streak, stickers. `defaultState()`/`freshDaily()` define the state shape; a new-day rollover runs on load. To reset, clear the localStorage key (there is an in-app reset that does this).

### main.py — WhatsApp bot

All bot logic in one file. No database — state is the module-level dict `reveal_state`, so it resets on process restart and is not thread-safe under concurrent workers.

- `GET /webhook` — Meta's verification challenge. Returns `hub.challenge` if `hub.verify_token` matches `VERIFY_TOKEN`, else 403.
- `POST /webhook` — extracts sender and text from the Meta event payload, runs `get_reveal_logic()`, replies via `send_whatsapp_message()` (POST to `https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages`). Errors are swallowed by a bare `except: pass`.
- `get_reveal_logic()` — game activates when the message contains `"תעלומה"` or `"משחק"`; two hints, then the reveal at guess ≥ 3. `reveal_state["answer"]` and `reveal_state["mystery"]` are hardcoded — change them to customize the game.

## Environment Variables (bot only)

The static pages need none. `main.py` reads four env vars at runtime:

| Variable | Purpose |
|---|---|
| `VERIFY_TOKEN` | Shared secret for Meta's webhook verification handshake (GET `/webhook`) |
| `PHONE_NUMBER_ID` | Meta WhatsApp Business phone number ID (used in the send URL) |
| `ACCESS_TOKEN` | Meta access token for the WhatsApp API |
| `PORT` | HTTP port (defaults to `10000` if unset) |

## Deployment

- The bot targets a platform like Render or Railway (binds `0.0.0.0` on `$PORT`, `gunicorn` in requirements).
- The static pages need any static host. A GitHub Pages deploy workflow was added and then removed (the token couldn't auto-enable Pages) — there is currently no CI/CD in the repo.

## Conventions

- Hebrew UI text and Hebrew code comments; all pages `lang="he" dir="rtl"`.
- Single-file pages: each HTML file carries its own CSS and JS inline; no frameworks, no modules — globals shared via `window.*`.
- The business WhatsApp number `972502733773` is the ordering channel everywhere; prefer `window.MINOLA_PHONE` over hardcoding it in new code.
- Order links follow a fixed URL-encoded Hebrew template (product name, customization, name for printing, photo yes/no, notes) — keep new `wa` links consistent with it.
