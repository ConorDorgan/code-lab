"""Build result rows and write the CSV + HTML report."""
from __future__ import annotations

import csv
import datetime as dt
import html
import re
from pathlib import Path

from . import config
from .identify import Identification
from .pricing import PriceResult
from .vinted import Listing

COLUMNS = [
    ("thumbnail", "Photo thumbnail URL"),
    ("title", "Vinted listing title"),
    ("vinted_url", "Link to the listing"),
    ("brand", "Brand as listed on Vinted"),
    ("size", "Size as listed"),
    ("condition", "Condition as listed"),
    ("item_price_eur", "Seller's asking price"),
    ("buyer_protection_eur", "Vinted Buyer Protection fee"),
    ("postage_eur", "Cheapest postage shown on the item page (blank = not shown)"),
    ("vinted_total_eur", "What you'd pay: item + Buyer Protection + postage"),
    ("identified_product", "What the tool thinks the item is"),
    ("item_type", "Item type"),
    ("colour", "Colour"),
    ("confidence", "high / medium / low (see README)"),
    ("identified_from", "text, or text+photo (Claude)"),
    ("retail_price_eur", "Lowest current buy-new price found (EUR)"),
    ("retail_price_original", "Retail price as shown, in its own currency"),
    ("converted_from_gbp", "yes if the retail price was converted from GBP at the fixed config rate"),
    ("retail_rrp_eur", "Full (pre-sale) retail price, if the shop showed one"),
    ("retail_product", "Retail product name that was matched"),
    ("retail_source", "Where the price came from"),
    ("retail_url", "Source link for the retail price"),
    ("retail_checked", "Date the retail price was checked"),
    ("saving_eur", "Retail price minus Vinted total"),
    ("saving_pct", "Saving as % of the retail price"),
    ("status", "Price lookup outcome"),
    ("notes", "Anything worth knowing about this row"),
]


def _r(x):
    return None if x is None else round(float(x), 2)


def build_row(listing: Listing, ident: Identification, price: PriceResult | None) -> dict:
    notes = list(ident.notes)
    total = listing.total_cost
    if listing.shipping is None:
        notes.append("postage not shown; total excludes postage")
    row = {
        "id": listing.id,
        "thumbnail": listing.thumbnail or (listing.photos[0] if listing.photos else ""),
        "title": listing.title,
        "vinted_url": listing.url,
        "brand": listing.brand,
        "size": listing.size,
        "condition": listing.condition,
        "item_price_eur": _r(listing.price),
        "buyer_protection_eur": _r(listing.service_fee),
        "postage_eur": _r(listing.shipping),
        "vinted_total_eur": _r(total),
        "identified_product": ident.product_name,
        "item_type": ident.item_type,
        "colour": ident.colour,
        "confidence": ident.confidence,
        "identified_from": ident.source,
        "retail_price_eur": None, "retail_price_original": "", "converted_from_gbp": "",
        "retail_rrp_eur": None, "retail_product": "", "retail_source": "", "retail_url": "",
        "retail_checked": "", "saving_eur": None, "saving_pct": None,
        "status": "price lookup skipped" if price is None else price.status,
        "notes": "",
    }
    if price is not None:
        row["confidence"] = price.confidence
        if price.discontinued:
            notes.append("discontinued model")
    if price is not None and price.offer is not None:
        o = price.offer
        sym = "£" if o.currency == "GBP" else "€"
        row.update(
            retail_price_eur=o.price_eur,
            retail_price_original=f"{sym}{o.price:.2f}",
            converted_from_gbp="yes" if o.converted else "",
            retail_rrp_eur=_r(o.original_price * (config.GBP_TO_EUR if o.converted else 1)) if o.original_price else None,
            retail_product=o.title,
            retail_source=o.source,
            retail_url=o.url,
            retail_checked=o.checked,
        )
        if o.converted:
            notes.append(f"converted from GBP at {config.GBP_TO_EUR} EUR/GBP")
        if o.in_stock is False:
            notes.append("retail product shown as out of stock")
        if o.original_price:
            notes.append("retailer price is a sale price")
        notes += o.notes
        if total is not None and o.price_eur > 0:
            row["saving_eur"] = round(o.price_eur - total, 2)
            row["saving_pct"] = round((o.price_eur - total) / o.price_eur * 100, 1)
    row["notes"] = "; ".join(dict.fromkeys(n for n in notes if n))
    return row


def sort_rows(rows: list[dict]) -> list[dict]:
    """Highest saving % first; rows without a reliable price go to the bottom."""
    return sorted(rows, key=lambda r: (r["saving_pct"] is None, -(r["saving_pct"] or 0)))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "search"


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[c for c, _ in COLUMNS], extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})


def _money(v) -> str:
    return "—" if v is None else f"€{v:,.2f}"


def write_html(rows: list[dict], path: Path, title: str, meta: list[str]) -> None:
    e = html.escape
    trs = []
    for r in rows:
        conf = r["confidence"]
        saving = ""
        if r["saving_pct"] is not None:
            cls = "pos" if r["saving_pct"] > 0 else "neg"
            saving = f'<span class="{cls}">{_money(r["saving_eur"])}<br><b>{r["saving_pct"]:.0f}%</b></span>'
        retail = "no reliable price" if r["retail_price_eur"] is None else _money(r["retail_price_eur"])
        if r["converted_from_gbp"]:
            retail += f' <span class="flag" title="Converted from {e(r["retail_price_original"])}">GBP→EUR</span>'
        if r["retail_rrp_eur"]:
            retail += f'<br><small>RRP {_money(r["retail_rrp_eur"])}</small>'
        source = ""
        if r["retail_url"]:
            source = (f'<a href="{e(r["retail_url"])}" target="_blank" rel="noopener">{e(r["retail_source"])}</a>'
                      f'<br><small>{e(r["retail_product"])}<br>checked {e(r["retail_checked"])}</small>')
        else:
            source = f'<small>{e(r["status"])}</small>'
        vinted = _money(r["vinted_total_eur"])
        parts = [f"item {_money(r['item_price_eur'])}", f"fee {_money(r['buyer_protection_eur'])}",
                 f"post {_money(r['postage_eur'])}"]
        thumb = f'<img src="{e(r["thumbnail"])}" loading="lazy" alt="">' if r["thumbnail"] else ""
        trs.append(f"""<tr>
<td class="img">{thumb}</td>
<td><a href="{e(r['vinted_url'])}" target="_blank" rel="noopener">{e(r['title'])}</a>
<br><small>{e(r['brand'])} · {e(r['size'])} · {e(r['condition'])}</small></td>
<td class="num">{vinted}<br><small>{' · '.join(parts)}</small></td>
<td>{e(r['identified_product'])}<br><small>{e(r['item_type'])} {e(r['colour'])}</small></td>
<td><span class="conf {e(conf)}">{e(conf)}</span><br><small>{e(r['identified_from'])}</small></td>
<td class="num">{retail}</td>
<td>{source}</td>
<td class="num">{saving}</td>
<td><small>{e(r['notes'])}</small></td>
</tr>""")
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>
:root {{ --bg:#fff; --fg:#1d1d1f; --muted:#666; --line:#e3e3e3; --pos:#0a7d32; --neg:#b3261e; --chip:#f2f2f2; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#141414; --fg:#eee; --muted:#aaa; --line:#333; --pos:#5fd38a; --neg:#ff8a80; --chip:#262626; }} }}
body {{ font: 14px/1.4 system-ui, -apple-system, Segoe UI, sans-serif; background:var(--bg); color:var(--fg); margin:0; padding:16px; }}
h1 {{ font-size:20px; margin:0 0 4px; }} .meta {{ color:var(--muted); margin:0 0 16px; }}
.wrap {{ overflow-x:auto; }} table {{ border-collapse:collapse; width:100%; min-width:980px; }}
th, td {{ border-bottom:1px solid var(--line); padding:8px; vertical-align:top; text-align:left; }}
th {{ position:sticky; top:0; background:var(--bg); font-size:12px; color:var(--muted); }}
td.num {{ text-align:right; white-space:nowrap; }} small {{ color:var(--muted); }}
td.img img {{ width:72px; height:96px; object-fit:cover; border-radius:6px; background:var(--chip); }}
a {{ color:inherit; }} .pos {{ color:var(--pos); }} .neg {{ color:var(--neg); }}
.conf {{ padding:1px 8px; border-radius:10px; background:var(--chip); font-size:12px; }}
.conf.high {{ color:var(--pos); }} .conf.low {{ color:var(--neg); }}
.flag {{ font-size:11px; padding:0 4px; border:1px solid currentColor; border-radius:4px; }}
</style></head><body>
<h1>{e(title)}</h1>
<p class="meta">{'<br>'.join(e(m) for m in meta)}</p>
<div class="wrap"><table>
<thead><tr><th>Photo</th><th>Listing</th><th>Vinted price</th><th>Identified as</th><th>Confidence</th>
<th>Retail (new)</th><th>Source</th><th>Saving</th><th>Notes</th></tr></thead>
<tbody>
{''.join(trs)}
</tbody></table></div></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")


def output_paths(label: str, out_dir: Path | None = None) -> tuple[Path, Path]:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    base = (out_dir or config.OUTPUT_DIR) / f"{slug(label)}-{stamp}"
    return base.with_suffix(".csv"), base.with_suffix(".html")
