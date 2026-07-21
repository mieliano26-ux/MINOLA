# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Three independent codebases live side by side in this repo — they do not share code or talk to each other (except that the storefront pages share `products.js`):

1. **WhatsApp chatbot** (`main.py`) — Flask + Meta WhatsApp Business Cloud API (v17.0). Runs a Hebrew "mystery/reveal" guessing game. Deployed on a platform like Render or Railway (uses a `PORT` env var).
2. **MINOLA storefront** (`index.html`, `finder.html`, `products.js`) — a static Hebrew site for a personalized-gifts business. There is no backend or cart: every "buy" action is a pre-filled `wa.me` WhatsApp link.
3. **מיכלי OS** (`michali-os.html`) — a standalone gamified daily-routine mobile-style app, unrelated to the other two.

All user-facing text is Hebrew and every page uses `<html lang="he" dir="rtl">` — keep RTL in mind for any UI change.

## Commands

```bash
# Bot: install and run
pip install -r requirements.txt
python main.py          # dev server
gunicorn main:app       # production-style

# Static pages: no build step, no bundler — open the .html file
# directly in a browser, or serve the repo root:
python -m http.server
```

There are no tests and no linter configured in this project.

## WhatsApp Bot (`main.py`)

### Environment Variables

| Variable | Purpose |
|---|---|
| `VERIFY_TOKEN` | Shared secret for Meta's webhook verification handshake (GET `/webhook`) |
| `PHONE_NUMBER_ID` | Meta WhatsApp Business phone number ID (used in the send URL) |
| `ACCESS_TOKEN` | Meta permanent or temporary access token for the WhatsApp API |
| `PORT` | HTTP port (defaults to `10000` if unset) |

### Architecture

All bot logic lives in `main.py`. There is no database — state is held in the module-level dict `reveal_state`, meaning it resets on every process restart and is not thread-safe under concurrent workers.

**Webhook flow:**
- `GET /webhook` — Meta's verification challenge. Returns `hub.challenge` if `hub.verify_token` matches `VERIFY_TOKEN`, else 403.
- `POST /webhook` — Receives message events from Meta, extracts the sender number and message body, passes the text through `get_reveal_logic()`, and calls `send_whatsapp_message()` to reply via the Graph API.

**Game logic (`get_reveal_logic`):**
- Activated when the user message contains `"תעלומה"` or `"משחק"`.
- Tracks guess count in `reveal_state["guesses"]`; gives two hints before the final reveal at guess ≥ 3.
- `reveal_state["answer"]` and `reveal_state["mystery"]` are hardcoded strings — change these to customize the game.

**Sending messages (`send_whatsapp_message`):**
- POSTs to `https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages` with a JSON text payload.

## MINOLA Storefront

### `products.js` — single source of truth for products

An IIFE loaded by both `index.html` and `finder.html` that sets three globals: `window.MINOLA_PHONE`, `window.MINOLA_PRODUCTS`, and `window.MINOLA_ITEMS` (an alias of the same array that the finder reads). Per the file's own header comment, product edits belong in its `DATA` array only.

Each raw product uses short keys: `n` (name), `p` (price string like `"₪89"`), `t` (Hebrew category tags), `aud` (audience keys: `baby`/`kid`/`teen`/`woman`/`man`/`boss`/`teacher`/`family`), `img` (base64 data URI or relative path), and `wa` (a pre-filled `wa.me` order link with a URL-encoded Hebrew order template). A normalization pass at the bottom of the file adds the aliases the finder expects (`id`, `title`, `price`, `tags`, `thumbnailUrl`, `productCategory`, `showClient`, `brandFeatured`).

The file is ~1.6 MB because most product images are inlined as base64 data URIs.

### `index.html` — catalog page

Self-contained page (inline CSS/JS) with two separate product systems:

- **The visible catalog grid is hardcoded HTML** — product cards are not rendered from `products.js`. Search and category-chip filtering operate on each card's `data-name`/`data-tags` attributes. A new product must be added both as a card here and as a `DATA` entry in `products.js` to appear everywhere.
- **The floating "gift assistant" chat widget (`#mbot`)** does read `window.MINOLA_PRODUCTS`: a guided recipient → budget flow that filters by `aud` and by the price parsed out of the `p` string, then renders up to 6 product links.

### `finder.html` — gift-finder wizard

A phone-shell-styled quiz that loads `products.js` and reads `window.MINOLA_ITEMS`. Linked from the "מצא לי מתנה" button on `index.html`.

### Ordering convention

Every purchase path ends at `https://wa.me/972502733773?text=...` with a URL-encoded Hebrew order template. The number lives in `products.js` as `MINOLA_PHONE`, but is also hardcoded in many `index.html` links — a phone-number change must touch both.

## מיכלי OS (`michali-os.html`)

A single self-contained file: tab-based screens (`#scr-today`, `#scr-money`, `#scr-home`, `#scr-noam`, `#scr-more`, plus sub-screens for food/summer/decision/emergency), a points-and-ranks system, and all state persisted to `localStorage` under `STORE_KEY`. Content data lives in top-level `const` arrays (`CRITERIA`, `FOOD`, `HOME_TASKS`, `MAIN_TABS`, etc.).
