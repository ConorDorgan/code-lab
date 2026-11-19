# Blockers

Things that stopped part of the tool working. The tool never tries to bypass captchas or bot
protection: when it meets one it stops that part, logs it here and carries on.

## Summary (as of 2026-11-19, tested from a cloud server, not a home connection)

| What | What happened | Effect | Likely at home? |
|---|---|---|---|
| **vinted.ie item pages** | About 1 in 5–10 item pages returned HTTP 403 with a Cloudflare "Just a moment…" check; the next page usually loaded fine | Those rows use search-page data only (no description, colour or postage). Search pages themselves always worked | Probably much rarer on a home connection, which bot checks trust more than a datacentre address |
| **Plain HTTP clients on vinted.ie** | `/catalog` behind a Cloudflare JS challenge; `/api/v2/catalog/items` gives 404/403 | Tool uses a real (Playwright) browser instead | n/a |
| **Salomon IE / UK site** (salomon.com) | HTTP 403 "Access to this page has been denied" (PerimeterX) on every page | Brand-site prices unavailable; fell back to retailers | Possibly works from home |
| **Zalando IE** | HTTP 403 | Skipped | Possibly works from home |
| **ASOS** | HTTP 403 "Access Denied" (Akamai) | Skipped | Possibly works from home |
| **JD Sports IE** | HTTP 403 in early probes; in later runs its search page loaded but had no match for the query | Usually no price from JD | Possibly works from home |
| **Schuh IE** | Cloudflare "Just a moment…" check | Not included as a source | — |
| **SerpAPI / Claude** | Not tested live: no `SERPAPI_KEY` / `ANTHROPIC_API_KEY` in this environment | Features skipped, runs said so | Should work once keys are in `.env` |
| **Login + favourites** | Not run: needs you to log in by hand in a visible browser | Untested end to end; the favourites URL was confirmed to exist (redirects to login when logged out) | Run `login` then `favourites` |

## Log (appended automatically by the tool)

- 2026-11-19 10:41 — **Vinted item page**: HTTP 403. URL: https://www.vinted.ie/items/10775656585-salomon-xt-6-white-lunar-rock-white
- 2026-11-19 10:46 — **Salomon IE**: HTTP 403. URL: https://www.salomon.com/en-ie/search?q=Salomon+XT-6
- 2026-11-19 10:47 — **Zalando IE**: HTTP 403. URL: https://www.zalando.ie/catalogue/?q=Salomon+XT-6
- 2026-11-19 10:48 — **ASOS**: HTTP 403. URL: https://www.asos.com/search/?q=Salomon+XT-6+S%2FLAB
- 2026-11-19 11:29 — **Vinted search**: HTTP 403. URL: https://www.vinted.ie/catalog?search_text=nanamica+gore+tex&order=relevance&price_to=100&currency=EUR
- 2026-11-19 11:30 — **Vinted search**: HTTP 403. URL: https://www.vinted.ie/catalog?search_text=nanamica+gore+tex&order=relevance&price_to=100&currency=EUR
- 2026-11-19 11:31 — **Vinted search**: HTTP 403 on 3 pages in a row; stopped using this site for the run. URL: https://www.vinted.ie/catalog?search_text=arcteryx+gore+tex&order=relevance&price_to=100&currency=EUR
