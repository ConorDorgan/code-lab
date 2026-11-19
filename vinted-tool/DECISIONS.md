# Decisions

Choices made while building this without being able to ask. One line each on why.

- **Lives in `vinted-tool/` inside the existing `code-lab` repo, on branch `claude/zealous-tesla-aqt3yy`** — the session's repo already existed (a Next.js app), so instead of `git init` I kept the tool self-contained in a subfolder with its own `.gitignore`, venv and requirements.
- **Logged-in feature = favourites** — item 4 of the brief was left as "[FILL IN]"; favourites are the most useful thing to price-check, so `favourites` runs your saved items through the same identify + price pipeline. Saved searches/messages are not implemented.
- **Vinted data comes from server-rendered HTML in a real browser, not the `/api/v2` JSON endpoints** — tested 2026-11-19: the vinted.ie search page no longer calls `/api/v2/catalog/items` (it renders results server-side), and calling that endpoint directly returns 404 (plain HTTP) or 403 (from inside a browser session). Plain HTTP clients (httpx) get a Cloudflare JS challenge on `/catalog`; a normal Playwright Chromium session loads it fine. So: Playwright + parse the embedded Next.js flight data (`self.__next_f.push`), which has structured JSON (price, fee, total, brand, size, condition, photos).
- **Item pages are fetched for every result (on by default)** — the description, colour, category and postage are only on the item page; `--no-details` skips them for a quicker run.
- **Brand and size filters are applied client-side; max price and condition go into the Vinted URL too** — Vinted's brand/size filters need internal numeric IDs (size IDs differ per category), so the tool adds the brand to the search text and checks brand/size on each result. Condition maps to Vinted's `status_ids`, max price to `price_to`.
- **Up to 3 result pages are read to fill 50 filtered results** — client-side filters can drop items; capped at 3 pages to stay polite.
- **"Vinted price" in the report = item + Buyer Protection fee + cheapest shown postage** — the brief asks for the price including fee and postage where shown; the item-only price and fee are in their own CSV columns.
- **Default Claude model for photo ID is `claude-opus-5-5`** (override with `VINTED_TOOL_CLAUDE_MODEL`); only the main photo is sent, to keep cost down.
