# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

MINOLA is a Hebrew-language (RTL) personalized-gifts business. The repo holds two unrelated-but-cohabiting things, plus a third standalone app:

1. **A static storefront** — `index.html` (catalog/landing page), `finder.html` (gift-finder quiz), and `products.js` (shared product catalog). There is no backend, cart, or checkout: every "buy" action is a `https://wa.me/972502733773?text=...` deep link that opens a pre-filled WhatsApp order message.
2. **A Flask WhatsApp chatbot** — `main.py`, using the Meta WhatsApp Business Cloud API (v17.0). It runs a Hebrew "mystery/reveal" guessing game. It is entirely unrelated to the storefront.
3. **`michali-os.html`** — a standalone gamified personal life-management app ("מיכלי OS"), unrelated to the store.

Everything is Hebrew-first: pages use `dir="rtl"`, UI strings and code comments are in Hebrew.

Whole repo, at a glance:

| File | Size | What |
|---|---|---|
| `index.html` | ~1.7 MB | Catalog/landing page + embedded chat widget (base64 images inline) |
| `products.js` | ~1.6 MB | 105-product `DATA` array + normalization (base64 images inline) |
| `finder.html` | ~28 KB | Gift-finder quiz |
| `michali-os.html` | ~55 KB | "מיכלי OS" life-game app |
| `main.py` | ~3 KB | Flask WhatsApp bot |
| `requirements.txt` | 3 lines | `flask`, `requests`, `gunicorn` |

There is no `README`, no `.github/` directory, no CI/CD, no `images/` directory, and no lockfile.

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

There is no build system, bundler, test suite, or linter. The HTML pages are single-file vanilla JS/CSS (fonts loaded from Google Fonts). Verify changes by opening the page in a browser — nothing else will catch a mistake.

## Working With Large Files — Important

`index.html` (~1.7 MB) and `products.js` (~1.6 MB) are huge because product images are embedded as base64 data URIs. **Never read these files whole** — use Grep, or Read with `offset`/`limit`. The actual code is a small fraction of each file:

- `index.html` — 1041 lines. Styles and markup first; the hardcoded product grid starts at line 130; catalog search/chip-filter script at line 979; `<script src="products.js">` at line 1017 followed by the chat-widget script (lines 1018-1041). Careless greps will match base64 noise (e.g. `grep -o RC index.html` returns 359 hits, 358 of them inside image data) — anchor patterns or restrict to the script line ranges.
- `products.js` — 23 lines, but line 6 is a single ~1.64 MB line holding the whole `DATA` array. Read lines 1-5 for the header, `tail -c` for the normalization block at the end, and use `python3`/Grep for anything in between.

## Architecture

### products.js — single source of truth for the *finder* and the *chat widget*

Loaded by both `index.html` (line 1017) and `finder.html` (line 221). To add/edit products, edit the `DATA` array here — the file's header comment says exactly this, in Hebrew. **Caveat:** the visible product grid in `index.html` is hardcoded HTML and does *not* read this file (see below), so a product added here appears in the finder and the chat widget but not in the catalog grid.

105 products. Each uses short field names, normalized at load time into aliases the finder expects:

| Short field | Alias(es) | Meaning |
|---|---|---|
| `n` | `title` | Product name (Hebrew) |
| `p` | `price` | Price string — format is inconsistent, see below |
| `t` | `tags`, `productCategory` (first tag) | Category tags (Hebrew) |
| `aud` | — | Audience keys: `woman`, `man`, `kid`, `teen`, `baby`, `family`, `boss`, `teacher` |
| `img` | `thumbnailUrl` | Base64 data URI, `images/NN.jpg` path, or `""` |
| `wa` | — | Pre-built `wa.me` order link with URL-encoded Hebrew order template |

Normalization also stamps `id` (`p0`, `p1`, …), `showClient: true`, and `brandFeatured: false` defaults, then exposes globals: `window.MINOLA_PHONE` (`"972502733773"`), `window.MINOLA_PRODUCTS`, and `window.MINOLA_ITEMS` (same array; the name `finder.html` reads).

The eight tags in use, by frequency: `לבית` (51), `כוסות ובקבוקים` (17), `אירועים ומזכרות` (16), `ילדים` (13), `מארזים` (13), `חגים` (11), `מורות וגננות` (3), `אהבה וזוגיות` (2).

**Gotcha — missing images.** 47 products reference `images/NN.jpg`, but there is no `images/` directory in this repo — those thumbnails 404 unless the images are deployed alongside the pages. 53 products embed base64 data URIs, and 5 have `"img": ""` (both the finder and the widget handle an empty image, showing a placeholder or nothing).

**Gotcha — price strings are not uniform.** 39 distinct values across three shapes: `"₪89"` (most), bare digits `"119"`, and non-numeric `"מחיר בהתאמה"` / `"בהתאמה"` / `"עד ₪100"` / `"עד ₪60"`. Both budget filters parse with the same rule — strip every non-digit and `parseInt` — so `"עד ₪100"` reads as 100, and anything with no digits parses to `null` and is treated as *matching every budget*. Keep new prices in the `"₪NN"` shape.

### index.html — catalog / landing page

Static marketing page (hero, USP strip, footer) plus a product grid of **102 hardcoded `<article class="card">` elements** with inline `wa.me` order links and `data-tags` / `data-name` attributes. The line-979 script is a pure DOM filter: a search box (`#q`) plus category chips (`.chip[data-cat]`, nine categories) that show/hide cards by substring match on those attributes. It never touches `products.js`.

This means **the catalog grid and `products.js` are two independent copies of the catalog** (102 cards vs 105 products) and can drift. A product change usually needs editing in both places.

At the bottom is the embedded chat-widget "gift assistant" (`#mbot`, lines 992-1041): a scripted quick-reply flow (recipient → budget) that filters `window.MINOLA_PRODUCTS` by the `aud` array and parsed price, shows up to 6 matches as `wa.me` links, and falls back to a human-handoff WhatsApp link when nothing matches. Note the `RC` map at the top of that script (recipient key → category tags) is **dead code** — it is assigned and never read; the widget filters on `aud`, not tags.

### finder.html — gift-finder quiz

A mobile-phone-styled (393px shell) multi-screen quiz app: splash → 3 questions → results. Screens are `.screen` divs toggled with a `.hidden` class via `showScreen()`.

- Questions are declared in the `QUESTIONS` array: `recipient` (9 options), `quantity` (4), `budget` (5).
- `renderResults()` filters `window.MINOLA_ITEMS` by `showClient`, by `RECIPIENT_CATS[recipient]` matched against `item.tags`, and by budget. **It filters on tags, not on `aud`** — the opposite of the `index.html` widget, even though `RECIPIENT_CATS` and the widget's dead `RC` map hold identical data. Results sort `brandFeatured` first and cap at 30 cards.
- The `quantity` answer does not affect results at all; it only appears in the WhatsApp message.
- Tapping cards toggles them into `pickedIds`; `updateWA()` rebuilds the WhatsApp link from `window.MINOLA_PHONE` with recipient/quantity/budget labels plus the picked product names.
- If `window.MINOLA_ITEMS` is missing, the empty state says "השרת לא זמין" ("server unavailable") — misleading, since there is no server; it means `products.js` failed to load.

`index.html` links to `finder.html` once; `finder.html` links back twice.

### michali-os.html — "מיכלי OS" life-game app

Fully self-contained, mobile-only, no relation to the store or `products.js`. Five bottom tabs (`go(scr)`): `today` / `home` / `money` / `noam` / `more`, with extra render targets for food, summer, decision, and emergency views. All state lives in `localStorage` under key `michali_os_v1` (`STORE_KEY`).

`defaultState()` holds cumulative fields (`score`, `streak`, `bestStreak`, `daysActive`, `noamStickers`, `noamSurprises`, `decision`, `lastSurpriseAt`) and a `daily` object from `freshDaily()` (date, mode, mood/energy, per-area task/eased/skipped flags, sticky task indices). `load()` runs a new-day rollover when `daily.date` isn't today (advancing or resetting the streak) and expires a locked `decision`. To reset, clear the localStorage key — there is an in-app reset that does this.

### main.py — WhatsApp bot

All bot logic is in one file. There is no database: the module-level `reveal_state` is global and shared by every sender, resets on process restart, and is not safe under concurrent workers.

- `GET /webhook` — Meta's verification challenge. Returns `hub.challenge` if `hub.verify_token` matches `VERIFY_TOKEN`, else 403.
- `POST /webhook` — extracts sender and text from the Meta event payload, runs `get_reveal_logic()`, replies via `send_whatsapp_message()` (POST to `https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages`). Errors are swallowed by a bare `except: pass`, and the route always returns `200 OK`.
- `get_reveal_logic()` — the game activates when the message contains `"תעלומה"` or `"משחק"`; then two hints, then the reveal at guess ≥ 3 (`target_guesses`). Outside the game, every message gets the same canned reply. `reveal_state["answer"]` and `reveal_state["mystery"]` are hardcoded — change them to customize the game.
- `random` is imported but unused.

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
- The static pages need any static host — plus an `images/` directory for the 47 path-referenced thumbnails.
- A GitHub Pages deploy workflow was added and then removed (the token couldn't auto-enable Pages) — there is currently no CI/CD in the repo.

## Conventions

- Hebrew UI text and Hebrew code comments; all pages `lang="he" dir="rtl"`.
- Single-file pages: each HTML file carries its own CSS and JS inline; no frameworks, no modules, no imports — globals shared via `window.*`.
- The business WhatsApp number `972502733773` is the ordering channel everywhere; prefer `window.MINOLA_PHONE` over hardcoding it in new code.
- Order links follow a fixed URL-encoded Hebrew template — keep new `wa` links consistent with it:

  ```
  היי, אשמח להזמין:
  מוצר: <product name>
  אפשרות מיתוג:
  שם להדפסה:
  תמונה: כן / לא
  הערות:
  ```

- Storefront styling shares a palette defined as CSS custom properties in each page's `:root` (rose `#EC4899`, plum `#7C3AED`, cream `#FAF8FF`, ink `#2D2640`), with `Assistant` for body text and `Frank Ruhl Libre` for headings.
