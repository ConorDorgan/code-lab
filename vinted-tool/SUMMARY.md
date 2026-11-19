# Summary

Built 2026-11-19 in `vinted-tool/` (branch `claude/zealous-tesla-aqt3yy`). Setup, commands and
output columns are in `README.md`, the reasoning behind each choice is in `DECISIONS.md`, and
what got blocked is in `BLOCKERS.md`.

## Your first three commands

From the root of your `code-lab` checkout:

```bash
git fetch origin claude/zealous-tesla-aqt3yy && git checkout claude/zealous-tesla-aqt3yy && cd vinted-tool && ./setup.sh
```

```bash
.venv/bin/python -m vintedtool login
```

```bash
.venv/bin/python -m vintedtool search "salomon xt-6"
```

`setup.sh` creates the virtualenv, installs everything (including Playwright's Chromium) and runs
the tests. `login` opens a visible browser: log in by hand, then press Enter in the terminal.
Your `.env` can sit in `vinted-tool/` or at the repo root. After `login`, try
`.venv/bin/python -m vintedtool favourites`. The report opens from `output/*.html`.

## What works (tested for real on 2026-11-19)

- **Vinted Ireland search**: the real end-to-end run for "salomon xt-6" returned 50 listings,
  with filters for max price, size, brand and condition. Search pages loaded every time in a normal
  Playwright browser. Data comes from the structured JSON embedded in the page: price,
  Buyer Protection fee, total, brand, size, condition and photos.
- **Item pages**: description, colour, category, material and postage. In the final run, 44 of 50
  were read. The other 6 hit an intermittent Vinted bot-check; they were skipped, logged, and those
  rows used search-page data.
- **Identification**: 46 of 50 at high confidence (exact model: XT-6, XT-6 GTX, XT-6 Expanse) and
  4 at medium (XT-6 S/LAB, priced against the plain XT-6 because no S/LAB was on sale). It handles
  "XT-6" / "xt6" / "XT 6", "gore-tex" / "gor-tex" → GTX, and French colour words.
  Collaborations ("x Maison Margiela") are capped at medium.
- **Retail prices**: all 50 rows got a price, each with a source link and check date. All came
  from Foot Locker IE (XT-6 €179.99, XT-6 GTX €199.99, XT-6 Expanse €164.99), confirmed on the
  product page's structured data. Cheaper sale colourways (from €120) are mentioned in the notes
  rather than used.
- **Output**: CSV plus a local HTML report, sorted by saving %. The best deal in the final run was an
  XT-6 GTX at €81.49 all-in against €199.99 new (59% saving). A copy is in `examples/`.
- **Politeness**: a random 2–5 s pause between requests, 50 listings by default, a 24-hour cache, and
  ads/images/trackers are never downloaded.
- **Missing keys**: each run reports which optional feature is off and why, then carries on.
- **Tests**: 44 offline tests (`python -m pytest -q`), all passing. They run against saved real pages
  from Vinted and Foot Locker plus a hand-made SerpAPI sample.

## What doesn't work, or isn't tested

- **Brand sites and most big retailers block this cloud server**: Salomon IE/UK, Zalando and ASOS
  return 403. All prices in the test run came from Foot Locker IE. From your home connection these
  may well work: the tool tries them first and falls back automatically.
- **Google Shopping (SerpAPI) wasn't tested live**: there was no `SERPAPI_KEY`. The parsing is tested on a
  hand-made sample of SerpAPI's response format. Once you add the key it becomes the first price
  source, and it should give much better coverage than scraping shops.
- **Photo identification (Claude) wasn't tested live**: there was no `ANTHROPIC_API_KEY`. The request and
  response handling is tested with the API call replaced by a fake. It sends the listing's photo by
  URL. If Anthropic can't fetch Vinted's image URL, the run says so and falls back to text-only.
- **`login` and `favourites` haven't been run**: they need you at a visible browser. The favourites
  page URL was checked: it exists and redirects to sign-up when logged out, which the tool detects.
  The favourites page layout when logged in is a best guess: the tool collects every `/items/<id>`
  link there and reads each item page. If it finds nothing, tell me what the page looks like.
- **Your item 4 was "[FILL IN]"**, so I chose favourites. Saved searches and messages aren't built.
- **Discontinued detection is limited**: it uses a `discontinued` flag in
  `vintedtool/data/products.json` (e.g. Speedcross 5, 990v5) or a shop marking a product as
  discontinued. There's no live check.
- **Products outside the built-in list**: the list covers Salomon, Nike, Jordan, adidas,
  New Balance, ASICS, HOKA, On, The North Face, Arc'teryx, Patagonia, Dr. Martens, Veja and
  Converse. Anything else is low confidence ("no reliable price") unless Claude photo ID is on.
  Add models to `products.json` as you need them.
- **Colourway isn't matched**: prices are per model and variant (e.g. XT-6 GTX), not per colourway.
  Limited or collab colourways (e.g. "BSTN Iridescent") are priced as the base model and can show
  large negative savings.

## Blockers (details in BLOCKERS.md)

- vinted.ie item pages: an intermittent Cloudflare check (403) on roughly 1 in 5–10 pages from
  this server. Handled per page: skip it, pause 20 s, and stop after 3 in a row. Search pages were
  never blocked. The tool never waits on, interacts with or solves a challenge.
- Plain HTTP on vinted.ie gets a Cloudflare JS challenge, and the old `/api/v2/catalog/items` JSON
  endpoint returns 404/403. That's why the tool uses a real browser and reads the page's embedded
  JSON.
- 403s from Salomon IE/UK (PerimeterX), Zalando, ASOS (Akamai) and Schuh (Cloudflare).
- No `SERPAPI_KEY` or `ANTHROPIC_API_KEY` here, so those two features are untested live.
