"""Command-line entry point: python -m vintedtool {search,login,favourites}."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from . import config
from .blockers import Blocked
from .browser import Browser
from .cache import Cache
from .identify import ClaudeIdentifier, identify_listing
from .pricing import PriceFinder
from .report import build_row, output_paths, sort_rows, write_csv, write_html
from .vinted import Listing, listing_from_item_page, search


def _feature_notes(no_prices: bool) -> tuple[list[str], ClaudeIdentifier | None, str | None]:
    notes = []
    claude = None
    key = config.env("ANTHROPIC_API_KEY")
    if key:
        claude = ClaudeIdentifier(key, cache=Cache())
        notes.append(f"Photo identification: on (Claude, {config.CLAUDE_MODEL}).")
    else:
        notes.append("Photo identification: OFF — ANTHROPIC_API_KEY not set in .env; using title/description/brand only.")
    serp = config.env("SERPAPI_KEY")
    if no_prices:
        notes.append("Retail prices: skipped (--no-prices).")
    elif serp:
        notes.append("Google Shopping (SerpAPI): on.")
    else:
        notes.append("Google Shopping (SerpAPI): OFF — SERPAPI_KEY not set in .env; using brand sites and retailers only.")
    return notes, claude, serp


def run_pipeline(listings: list[Listing], browser: Browser, label: str, args, meta: list[str]) -> list[dict]:
    feature_notes, claude, serp = _feature_notes(args.no_prices)
    for n in feature_notes:
        print("• " + n)
    finder = None if args.no_prices else PriceFinder(browser, Cache(enabled=not args.no_cache), serp)
    rows = []
    print(f"Identifying and pricing {len(listings)} listings…")
    for i, it in enumerate(listings, 1):
        ident = identify_listing(it, claude)
        price = finder.find(ident) if finder else None
        row = build_row(it, ident, price)
        rows.append(row)
        pct = f"{row['saving_pct']:.0f}%" if row["saving_pct"] is not None else "—"
        print(f"  [{i:>2}/{len(listings)}] {ident.confidence:6} {ident.product_name[:40]:40} saving {pct}")
    rows = sort_rows(rows)
    csv_path, html_path = output_paths(label, Path(args.out) if args.out else None)
    if finder and finder.blocked_sources:
        feature_notes.append("Blocked price sources this run: " + ", ".join(sorted(finder.blocked_sources))
                             + " (see BLOCKERS.md).")
    meta = meta + feature_notes + [f"GBP prices converted at a fixed {config.GBP_TO_EUR} EUR/GBP."]
    write_csv(rows, csv_path)
    write_html(rows, html_path, label, meta)
    priced = sum(r["retail_price_eur"] is not None for r in rows)
    print(f"\n{len(rows)} listings, {priced} with a retail price.")
    print(f"CSV:  {csv_path}\nHTML: {html_path}")
    return rows


def cmd_search(args) -> int:
    import datetime as dt
    conditions = args.condition or []
    with Browser(cache=Cache(enabled=not args.no_cache), headless=not args.headed) as b:
        print(f"Searching vinted.ie for “{args.query}”…")
        try:
            listings = search(b, args.query, limit=args.limit, max_price=args.max_price, size=args.size,
                              brand=args.brand, conditions=conditions, details=not args.no_details)
        except Blocked as e:
            print(f"✗ Vinted blocked the search ({e.reason}). Logged to BLOCKERS.md.")
            return 2
        print(f"Found {len(listings)} matching listings.")
        if not listings:
            return 0
        filters = [f"max €{args.max_price:g}" if args.max_price else "", f"size {args.size}" if args.size else "",
                   f"brand {args.brand}" if args.brand else "", ", ".join(conditions)]
        meta = [f"Vinted Ireland search: “{args.query}” {' · '.join(f for f in filters if f)}".strip(),
                f"Run {dt.datetime.now():%Y-%m-%d %H:%M}. Sorted by saving %, highest first."]
        run_pipeline(listings, b, f"Vinted {args.query}", args, meta)
    return 0


# ------------------------------------------------------------------ login / favourites

LOGIN_URL = f"{config.VINTED_BASE}/member/signup/select_type?ref_url=%2F"


def cmd_login(args) -> int:
    """Open a visible browser, let the user log in by hand, save the session for later runs."""
    from playwright.sync_api import sync_playwright
    email, password = config.env("VINTED_EMAIL"), config.env("VINTED_PASSWORD")
    config.SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    print("Opening a browser window on vinted.ie.")
    print("Log in by hand (choose 'Log in' → 'email'). Solve any captcha yourself — the tool never does.")
    if email and password:
        print("Your email/password from .env will be typed into the login form when it appears;"
              " you still press the button.")
    print("When you can see you're logged in, come back here and press Enter.")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(locale="en-IE", viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        if email and password:
            _offer_autofill(page, email, password)
        input()
        ctx.storage_state(path=str(config.SESSION_FILE))
        cookies = {c["name"] for c in ctx.cookies()}
        browser.close()
    config.SESSION_FILE.chmod(0o600)
    print(f"Session saved to {config.SESSION_FILE} (git-ignored).")
    if "access_token_web" not in cookies:
        print("Warning: no Vinted access token cookie found — you may not be logged in. Run `login` again if favourites fails.")
    return 0


_AUTOFILL_JS = """(([email, password]) => {
  const fill = () => {
    const empty = el => el && el.offsetParent !== null && !el.value;
    const u = document.querySelector('input[name="username"], input[name="login"], input[type="email"]');
    const p = document.querySelector('input[type="password"]');
    const set = (el, v) => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, v);
      el.dispatchEvent(new Event('input', {bubbles: true}));
    };
    if (empty(u)) set(u, email);
    if (empty(p)) set(p, password);
  };
  setInterval(fill, 1000);
})"""


def _offer_autofill(page, email: str, password: str) -> None:
    """Type the .env credentials into the login form when it appears. Never submits the form and
    never touches captchas. Values are passed as arguments, not printed or written anywhere."""
    import json
    script = f"{_AUTOFILL_JS}({json.dumps([email, password])})"
    page.context.add_init_script(script)   # survives navigation inside the login flow
    try:
        page.evaluate(script)
    except Exception:
        pass


FAVOURITES_URLS = [
    f"{config.VINTED_BASE}/member/items/favourite_list",
]


def cmd_favourites(args) -> int:
    import datetime as dt
    if not config.SESSION_FILE.exists():
        print("No saved session. Run `python -m vintedtool login` first.")
        return 1
    with Browser(cache=Cache(enabled=not args.no_cache), headless=not args.headed,
                 storage_state=config.SESSION_FILE) as b:
        links: list[str] = []
        for url in FAVOURITES_URLS:
            try:
                # Personal page: never cached, scrolled so lazy-loaded items appear.
                hrefs = b.fetch(url, site="Vinted favourites", use_cache=False, settle_ms=4000,
                                evaluate="""async () => { for (let i=0;i<8;i++){ window.scrollBy(0, 2000);
                                  await new Promise(r=>setTimeout(r,700)); }
                                  return { url: location.href, text: document.body.innerText.slice(0, 3000),
                                    links: [...document.querySelectorAll('a[href*="/items/"]')].map(a=>a.href) }; }""")
            except Blocked as e:
                print(f"✗ Vinted blocked the favourites page ({e.reason}). Logged to BLOCKERS.md.")
                return 2
            if re.search(r"/member/(signup|login)|/session", hrefs["url"]) or "Log in" in hrefs["text"][:400]:
                print("Your saved session looks logged out. Run `python -m vintedtool login` again.")
                return 1
            links += [h for h in hrefs["links"] if re.search(r"/items/\d+", h)]
        seen, uniq = set(), []
        for h in links:
            iid = re.search(r"/items/(\d+)", h).group(1)
            if iid not in seen:
                seen.add(iid)
                uniq.append(h.split("?")[0])
        uniq = uniq[: args.limit]
        print(f"Found {len(uniq)} favourites. Fetching item pages…")
        listings = []
        for h in uniq:
            try:
                html = b.fetch(h, site="Vinted item page", namespace="vinted_item")
            except Blocked as e:
                print(f"  ! item page blocked ({e.reason}); stopping item fetches")
                break
            it = listing_from_item_page(h, html)
            if it:
                listings.append(it)
        if not listings:
            print("No favourites could be read.")
            return 0
        meta = [f"Your Vinted favourites ({len(listings)} items)", f"Run {dt.datetime.now():%Y-%m-%d %H:%M}."]
        run_pipeline(listings, b, "Vinted favourites", args, meta)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m vintedtool",
                                 description="Search Vinted Ireland and compare listings to new retail prices.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--limit", type=int, default=config.DEFAULT_LIMIT, help="max listings (default 50)")
        p.add_argument("--no-prices", action="store_true", help="skip retail price lookups")
        p.add_argument("--no-cache", action="store_true", help="ignore the 24h cache")
        p.add_argument("--headed", action="store_true", help="show the browser window")
        p.add_argument("--out", help="output folder (default ./output)")

    s = sub.add_parser("search", help="search vinted.ie")
    s.add_argument("query")
    s.add_argument("--max-price", type=float, help="max item price in EUR")
    s.add_argument("--size", help='size as Vinted shows it, e.g. "42" or "M"')
    s.add_argument("--brand", help="brand name, e.g. salomon")
    s.add_argument("--condition", action="append", choices=list(config.CONDITIONS),
                   help="repeatable: new_with_tags, new_without_tags, very_good, good, satisfactory")
    s.add_argument("--no-details", action="store_true",
                   help="don't open each item page (faster; no description/colour/postage)")
    common(s)
    s.set_defaults(func=cmd_search)

    lg = sub.add_parser("login", help="log in by hand in a visible browser and save the session")
    lg.set_defaults(func=cmd_login)

    fv = sub.add_parser("favourites", help="price-check your Vinted favourites (needs `login` first)")
    common(fv)
    fv.set_defaults(func=cmd_favourites)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
