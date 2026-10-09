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
| `index.html` | ~21 KB | Catalog/landing page — grid rendered from `products.js` — + embedded chat widget |
| `products.js` | ~1.6 MB | 105-product `DATA` array + normalization (base64 images inline) |
| `finder.html` | ~29 KB | Gift-finder quiz |
| `michali-os.html` | ~55 KB | "מיכלי OS" life-game app |
| `main.py` | ~3 KB | Flask WhatsApp bot |
| `requirements.txt` | 3 lines | `flask`, `requests`, `gunicorn` |
| `images/` | README only | Where the 52 missing product photos go; `README.md` lists every required filename |

There is no `README` at the repo root, no `.github/` directory, no CI/CD, and no lockfile. `logo.png` is referenced but absent; both `<img>` tags that use it have working `onerror` handlers, so the header falls back to a text logo.

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

`products.js` (~1.6 MB) is huge because product images are embedded as base64 data URIs. **Never read it whole** — use Grep, or Read with `offset`/`limit`:

- `products.js` — 23 lines, but line 6 is a single ~1.6 MB line holding the whole `DATA` array. Read lines 1-5 for the header, `tail -c` for the normalization block at the end, and use `python3`/Grep for anything in between. Careless greps match base64 noise, so anchor patterns on field names (`"n":`, `"img":`) rather than bare substrings.
- To edit the array programmatically, parse it as JSON rather than regex-patching the line: locate the line starting with `var DATA =`, slice between its first `[` and last `]`, `json.loads`, mutate, then `json.dumps(..., ensure_ascii=False)` back into place. A greedy `\[.*\]` over the whole file overshoots the array and fails to parse.
- `index.html` is now ~19 KB and safe to read whole — the base64 lives only in `products.js`.

## Architecture

### products.js — the single source of truth for every surface

Loaded by `index.html` and `finder.html` (line 221). To add/edit products, edit the `DATA` array here and nowhere else — the file's header comment says exactly this, in Hebrew. All three consumers read it: the catalog grid, the chat widget, and the finder.

105 products. Each uses short field names, normalized at load time into aliases the finder expects:

| Short field | Alias(es) | Meaning |
|---|---|---|
| `n` | `title` | Product name (Hebrew) |
| `d` | `desc` | One-line product description (Hebrew), shown on the catalog card |
| `p` | `price` | Price string — format is inconsistent, see below |
| `t` | `tags`, `productCategory` (first tag) | Category tags (Hebrew) |
| `aud` | — | Audience keys: `woman`, `man`, `kid`, `teen`, `baby`, `family`, `boss`, `teacher` |
| `img` | `thumbnailUrl` | Base64 data URI (53 products) or an `images/NN.jpg` path (52). Never empty |
| `wa` | — | Pre-built `wa.me` order link with URL-encoded Hebrew order template |
| `bundle` | — | Optional `true` on the 3 "מארז" products — styles the card and switches its CTA to "לבניית מארז בוואטסאפ" |

Normalization also stamps `id` (`p0`, `p1`, …), `showClient: true`, and `brandFeatured: false` defaults, then exposes globals: `window.MINOLA_PHONE` (`"972502733773"`), `window.MINOLA_PRODUCTS`, and `window.MINOLA_ITEMS` (same array; the name `finder.html` reads).

The eight tags in use, by frequency: `לבית` (51), `כוסות ובקבוקים` (17), `אירועים ומזכרות` (16), `ילדים` (13), `מארזים` (13), `חגים` (11), `מורות וגננות` (3), `אהבה וזוגיות` (2).

**Gotcha — half the photos are missing.** 53 products embed a base64 data URI; the other 52 point at `images/NN.jpg`, and those files are not in the repo, so every one of them 404s until the photos are added. Nothing breaks: each surface falls back to an icon, so a missing photo never shows a broken-image icon.

- **Catalog grid**: the designed `.ph` card — category icon, product name, and a "תמונה בקרוב" chip on a rose-to-plum gradient.
- **Finder**: the category icon on a gradient tile (`.prod-thumb.empty`).
- **Chat widget**: the small 💝 tile (`.mprod .ph`).

`images/README.md` lists every required filename grouped by category. Dropping a correctly named file into `images/` is all it takes — no code change, because every product already carries its path.

**Gotcha — price strings are not uniform.** 39 distinct values across three shapes: `"₪89"` (most), bare digits `"119"`, and non-numeric `"מחיר בהתאמה"` / `"בהתאמה"` / `"עד ₪100"` / `"עד ₪60"`. Both budget filters parse with the same rule — strip every non-digit and `parseInt` — so `"עד ₪100"` reads as 100, and anything with no digits parses to `null` and is treated as *matching every budget*. Keep new prices in the `"₪NN"` shape.

### index.html — catalog / landing page

Static marketing page (hero, USP strip, footer) plus `<div class="grid" id="grid">`, which ships **empty** and is filled at runtime.

Three scripts run in order, and that order matters:

1. `<script src="products.js">` — populates `window.MINOLA_PRODUCTS`.
2. **The grid renderer** — maps every product to an `<article class="card">` carrying the same `data-tags` / `data-name` attributes the filter relies on, plus its `wa.me` order link. Bundles get `class="card bundle"` and the "לבניית מארז בוואטסאפ" CTA. It then attaches an `error` listener to each image so a 404 becomes the designed `.ph` card, and fills the hero collage with the first four products that have an embedded base64 image, so the hero never depends on a file that might be missing.
3. **The search/chip filter** — a pure DOM filter over the rendered cards: a search box (`#q`) plus category chips (`.chip[data-cat]`, nine categories) that show/hide by substring match on those attributes.

The filter captures `document.querySelectorAll('.card')` once at parse time, so it **must stay after the renderer**. Moving the `products.js` include back to the bottom of the page (where it used to live) silently yields an empty catalog.

At the bottom is the embedded chat-widget "gift assistant" (`#mbot`): a scripted quick-reply flow (recipient → budget) that filters `window.MINOLA_PRODUCTS` by the `aud` array and parsed price, shows up to 6 matches as `wa.me` links, and falls back to a human-handoff WhatsApp link when nothing matches.

**Don't remove `#mbot[hidden]{display:none}`.** The panel is markup-hidden with the `hidden` attribute, but `#mbot{...display:flex}` is an author rule and beats the user-agent `[hidden]{display:none}`. Without that one line the chat panel is stuck open on every page load, covering a fifth of the desktop viewport and 94% of a phone screen.

### finder.html — gift-finder quiz

A mobile-phone-styled (393px shell) multi-screen quiz app: splash → 3 questions → results. Screens are `.screen` divs toggled with a `.hidden` class via `showScreen()`.

- Questions are declared in the `QUESTIONS` array: `recipient` (9 options), `quantity` (4), `budget` (5).
- `renderResults()` filters `window.MINOLA_ITEMS` by `showClient`, by `RECIPIENT_CATS[recipient]` matched against `item.tags`, and by budget. **It filters on tags, while the `index.html` chat widget filters the same nine recipients on `aud`** — two different mechanisms for the same question, so the same answer can yield different products on the two surfaces. Results sort `brandFeatured` first and cap at 30 cards.
- The `quantity` answer does not affect results at all; it only appears in the WhatsApp message.
- Tapping cards toggles them into `pickedIds`; `updateWA()` rebuilds the WhatsApp link from `window.MINOLA_PHONE` with recipient/quantity/budget labels plus the picked product names.
- Each thumbnail gets an `error` handler that swaps the `<img>` for the category icon from `THUMB_ICON` on a gradient tile, so a missing photo never shows as broken.
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
- The static pages need any static host. Deploy `images/` alongside them once the photos exist; until then the pages render fine without it.
- A GitHub Pages deploy workflow was added and then removed (the token couldn't auto-enable Pages) — there is currently no CI/CD in the repo.

## Conventions

- Hebrew UI text and Hebrew code comments; all pages `lang="he" dir="rtl"`.
- Single-file pages: each HTML file carries its own CSS and JS inline; no frameworks, no modules, no imports — globals shared via `window.*`. `products.js` is the one shared file.
- **Adding or changing a product is a one-file edit: `products.js`.** It flows to the catalog grid, the chat widget, and the finder. Give every product an `n`, `d`, `p`, `t`, `aud`, `img`, and `wa`; add `bundle: true` only for build-your-own-box products.
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
