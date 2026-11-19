# vinted-tool

A personal command-line tool that searches **Vinted Ireland** (vinted.ie, EUR), works out what each
listing actually is, looks up the current **buy-new retail price**, and shows how much cheaper the
Vinted listing is. Results go to a CSV and a local HTML report, sorted by saving %.

It never invents a price: every retail price has a source link and the date it was checked, and
items it can't identify well enough say **"no reliable price"** instead of guessing.

## Setup

Needs Python 3.11+. From the `vinted-tool` folder:

```bash
./setup.sh
```

That creates `.venv`, installs `requirements.txt`, installs Playwright's Chromium, creates `.env`
from `.env.example` if you don't have one, and runs the tests. By hand it's:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m playwright install chromium
```

Then activate the venv for the commands below (`source .venv/bin/activate`), or prefix them with
`.venv/bin/`.

`.env` (git-ignored, never printed or logged). Put it in `vinted-tool/.env`; a `.env` at the
repo root is also read:

| Variable | Needed for | If missing |
|---|---|---|
| `VINTED_EMAIL`, `VINTED_PASSWORD` | Typed into the login form for you during `login` | You type them yourself |
| `ANTHROPIC_API_KEY` | Photo-based identification with Claude | Text-only identification (title, description, brand, category); the run says so |
| `SERPAPI_KEY` | Google Shopping price lookups (the first and best price source) | Brand sites and retailers only; the run says so |

Optional: `VINTED_TOOL_CLAUDE_MODEL` to change the Claude model (default `claude-opus-5-5`).

## Commands

All commands are run from the `vinted-tool` folder with the venv active.

### Search (no login needed)

```bash
python -m vintedtool search "salomon xt-6"
```

```bash
python -m vintedtool search "salomon xt-6" --max-price 120 --size 42 --condition very_good --condition new_without_tags
```

```bash
python -m vintedtool search "air max 90" --brand nike --limit 20 --no-details
```

Options:

| Option | Meaning |
|---|---|
| `--max-price 120` | Max item price in EUR |
| `--size 42` | Size exactly as Vinted shows it (`42` won't match `42.5`; `M` matches `M / 38 / 10`) |
| `--brand nike` | Only listings of that brand (also added to the search text) |
| `--condition X` | Repeatable: `new_with_tags`, `new_without_tags`, `very_good`, `good`, `satisfactory` |
| `--limit 50` | Max listings (default 50) |
| `--no-details` | Don't open each item page: faster, but no description, colour or postage |
| `--no-prices` | Skip retail price lookups |
| `--no-cache` | Ignore the 24-hour cache |
| `--headed` | Show the browser window |
| `--out DIR` | Where to write reports (default `output/`) |

### Login (once, by hand)

```bash
python -m vintedtool login
```

Opens a **visible** browser on vinted.ie. Log in yourself (choose *Log in → email*). If your
`.env` has `VINTED_EMAIL`/`VINTED_PASSWORD` they're typed into the form when it appears, but you
press the button, and you solve any captcha yourself; the tool never touches captchas. When you can
see you're logged in, go back to the terminal and press **Enter**. The session is saved to
`session/vinted_session.json` (git-ignored, file mode 600) and reused by later runs. Run `login`
again whenever the tool says your session looks logged out.

### Favourites (needs `login` first)

```bash
python -m vintedtool favourites
```

Reads your Vinted favourites with the saved session and runs them through the same identify +
price pipeline, producing the same CSV/HTML report.

### Tests

```bash
python -m pytest -q
```

Tests run offline against saved pages in `tests/fixtures/` (a real vinted.ie search page and item
page, a real Foot Locker IE results page and product page, a Cloudflare challenge page, and a
hand-made SerpAPI response).

A real example report from 2026-11-19 is in `examples/salomon-xt-6-sample.html` (and `.csv`).

## How it works

1. **Search** – a normal Chromium session (Playwright) loads the vinted.ie search page. The results
   are embedded in the page as structured JSON (Next.js server-rendered data), which the tool
   decodes. Then each item page is opened for the description, colour, category and postage.
2. **Identify** – brand from Vinted's brand field; model/product line by matching the title, then
   the description, against `vintedtool/data/products.json` (Salomon, Nike, Jordan, adidas, New
   Balance, ASICS, HOKA, On, The North Face, Arc'teryx, Patagonia, Dr. Martens, Veja, Converse).
   Handles `XT-6`/`xt6`/`XT 6`, variants like GTX/Gore-Tex, and French/German/Italian/Spanish/Dutch/
   Polish colour words. With `ANTHROPIC_API_KEY`, the main photo plus the text goes to Claude, which
   can fill in a model the text doesn't name (it can raise confidence, never lower it).
3. **Price** – sources in this order, stopping at the first one with a good enough match:
   Google Shopping via SerpAPI → the brand's own Irish then UK site → Zalando IE, Foot Locker IE,
   JD Sports IE, Life Style Sports, ASOS, END. Second-hand and resale sellers (eBay, Vinted, StockX,
   GOAT…) and kids' sizes are ignored. The chosen product page is opened to confirm the price from its
   structured data. The **lowest current new price** for the matched product is used (a sale price
   counts; the pre-sale price is shown as RRP). GBP prices are converted at the fixed
   `GBP_TO_EUR` rate in `vintedtool/config.py` and flagged.
4. **Report** – CSV + HTML in `output/`, sorted by saving %, highest first.

Politeness: one page at a time, a random 2–5 s pause between live requests, 50 listings by
default, and a 24-hour on-disk cache (`.cache/`) so repeat runs don't re-hit any site. If a site
returns 403/429 or a captcha/bot-check page, the tool stops using that site for the run, writes a
line to `BLOCKERS.md`, and carries on with everything else. Vinted item pages are the exception:
Vinted shows an occasional bot-check on single item pages, so a challenged item page is skipped
(that row keeps its search-page data), the tool pauses 20 s, and it only stops reading item pages
after 3 blocks in a row. It never waits on, clicks or solves a challenge.

## Confidence levels

| Level | Meaning | Price shown? |
|---|---|---|
| **high** | Exact product/model identified, and the retail match is the same model and variant | Yes |
| **medium** | Brand and product line known but exact model unclear, *or* the closest retail match is a different variant (e.g. listing is XT-6, retailer only has XT-6 GTX), *or* a collaboration (e.g. "x Maison Margiela") | Yes, flagged |
| **low** | Only brand and item type known | No – "no reliable price" |

The confidence in the report is the lower of the identification confidence and the retail-match
confidence.

## Output columns (CSV; the HTML shows the same data)

| Column | Meaning |
|---|---|
| `thumbnail` | URL of the listing's main photo (shown as a thumbnail in the HTML) |
| `title` | Listing title on Vinted |
| `vinted_url` | Link to the listing |
| `brand`, `size`, `condition` | As listed on Vinted |
| `item_price_eur` | Seller's asking price |
| `buyer_protection_eur` | Vinted's Buyer Protection fee |
| `postage_eur` | Cheapest postage shown on the item page (blank if not shown / item page not read) |
| `vinted_total_eur` | What you'd pay: item + Buyer Protection + postage (postage left out if not shown, and the notes say so) |
| `identified_product` | What the tool thinks it is, e.g. "Salomon XT-6 GTX" |
| `item_type`, `colour` | Item type (trainers, jacket, …) and colour |
| `confidence` | high / medium / low (above) |
| `identified_from` | `text` or `text+photo (Claude)` |
| `retail_price_eur` | Lowest current buy-new price found, in EUR. Blank = no reliable price |
| `retail_price_original` | That price as shown by the shop, in its own currency |
| `converted_from_gbp` | `yes` if converted from GBP at the fixed rate |
| `retail_rrp_eur` | Full pre-sale price, when the shop shows the item on sale |
| `retail_product` | The retail product name that was matched |
| `retail_source` | Where the price came from (shop, or "Google Shopping: shop") |
| `retail_url` | Source link for the price |
| `retail_checked` | Date the price was checked |
| `saving_eur` | `retail_price_eur − vinted_total_eur` (negative = Vinted is dearer) |
| `saving_pct` | Saving as a % of the retail price |
| `status` | `price found`, `closest retail match is a different variant`, `no retail match found`, `no reliable price (…)`, `discontinued; last retail price found`, … |
| `notes` | Anything else: sale price, out of stock, converted currency, postage missing, collab, … |

## Files

```
vintedtool/        the package (cli, vinted, identify, pricing, report, browser, cache, config)
vintedtool/data/products.json   brand → product line → model list used for identification
tests/             offline tests + saved sample pages
output/            reports (git-ignored)
.cache/            24 h cache (git-ignored)
session/           saved Vinted login (git-ignored)
DECISIONS.md       choices made while building it
BLOCKERS.md        what blocked the tool, when
```
