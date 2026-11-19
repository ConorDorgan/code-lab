"""Vinted Ireland: search URL building and parsing of server-rendered pages.

The vinted.ie web frontend (Next.js App Router) server-renders search results and item pages.
The data is embedded in the HTML as React Server Component "flight" chunks:
    <script>self.__next_f.push([1,"...json-escaped text..."])</script>
We decode and concatenate those chunks, then pull out the JSON objects we need
("productItem" on search pages; "plugins", "pricingServices" and the JSON-LD Product on item
pages). See DECISIONS.md for why this beats the old /api/v2 JSON endpoints.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Iterator
from urllib.parse import urlencode

from . import config

_PUSH_RE = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
_DECODER = json.JSONDecoder()


@dataclass
class Listing:
    id: int
    title: str
    url: str
    price: float | None = None
    service_fee: float | None = None          # Vinted "Buyer Protection fee"
    total_item_price: float | None = None     # price + service fee, as Vinted shows it
    shipping: float | None = None             # cheapest postage shown on the item page
    currency: str = "EUR"
    brand: str = ""
    size: str = ""
    condition: str = ""
    thumbnail: str = ""
    photos: list[str] = field(default_factory=list)
    description: str = ""
    colour: str = ""
    category: str = ""
    material: str = ""
    favourite_count: int | None = None
    is_promoted: bool = False
    details_fetched: bool = False

    @property
    def total_cost(self) -> float | None:
        """What you'd actually pay: item + buyer protection + postage (when known)."""
        base = self.total_item_price
        if base is None and self.price is not None:
            base = self.price + (self.service_fee or 0)
        if base is None:
            return None
        return round(base + (self.shipping or 0), 2)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["total_cost"] = self.total_cost
        return d


# ---------------------------------------------------------------- flight decoding

def extract_flight(html: str) -> str:
    """Decode and join all RSC flight chunks in a Next.js page."""
    parts = []
    for m in _PUSH_RE.finditer(html):
        try:
            parts.append(json.loads('"' + m.group(1) + '"'))
        except json.JSONDecodeError:
            continue
    return "".join(parts)


def iter_objects_after(text: str, key: str, opener: str = "{") -> Iterator:
    """Yield every JSON value that directly follows `"key":` in text."""
    needle = f'"{key}":{opener}'
    start = 0
    while True:
        i = text.find(needle, start)
        if i < 0:
            return
        j = i + len(needle) - 1
        try:
            obj, end = _DECODER.raw_decode(text, j)
        except json.JSONDecodeError:
            start = j + 1
            continue
        yield obj
        start = end


def _money(v) -> float | None:
    if isinstance(v, dict):
        v = v.get("amount")
    try:
        return round(float(v), 2) if v not in (None, "", "$undefined") else None
    except (TypeError, ValueError):
        return None


def _label_field(label: str, name: str) -> str:
    m = re.search(rf"{name}: (.*?)(?:, (?:Brand|Condition|Size): |, [\d.,]+ €|$)", label or "")
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------- search page

def parse_catalog(html: str) -> list[Listing]:
    """Parse a vinted.ie /catalog search results page into Listings (page order kept)."""
    flight = extract_flight(html)
    out: dict[int, Listing] = {}
    for pi in iter_objects_after(flight, "productItem"):
        if not isinstance(pi, dict) or "id" not in pi or "title" not in pi:
            continue
        iid = int(pi["id"])
        if iid in out:
            continue
        box = pi.get("itemBox") or {}
        label = box.get("accessibilityLabel") or ""
        second = (box.get("secondLine") or "").split(" · ")
        size = _label_field(label, "Size") or (second[0] if len(second) == 2 else "")
        condition = _label_field(label, "Condition") or (second[-1] if second and second[-1] else "")
        photos = [p.get("url") for p in pi.get("photos") or [] if isinstance(p, dict) and p.get("url")]
        price = pi.get("priceWithDiscount") or pi.get("price")
        url = pi.get("url") or ""
        out[iid] = Listing(
            id=iid,
            title=pi.get("title", "").strip(),
            url=url if url.startswith("http") else config.VINTED_BASE + url,
            price=_money(price),
            service_fee=_money(pi.get("serviceFee")),
            total_item_price=_money(pi.get("totalItemPrice")),
            currency=(price or {}).get("currencyCode", "EUR") if isinstance(price, dict) else "EUR",
            brand=_label_field(label, "Brand") or (box.get("firstLine") or "").strip(),
            size=size,
            condition=condition,
            thumbnail=pi.get("thumbnailUrl") or "",
            photos=photos,
            favourite_count=pi.get("favouriteCount"),
            is_promoted=bool(pi.get("isPromoted")),
        )
    return list(out.values())


# ---------------------------------------------------------------- item page

def parse_item(html: str) -> dict:
    """Pull description, attributes, postage and fees out of an item page."""
    flight = extract_flight(html)
    d: dict = {}
    for ld in iter_objects_after(flight, "jsonLd"):
        if isinstance(ld, dict) and ld.get("@type") == "Product":
            d.setdefault("title", ld.get("name", ""))
            d.setdefault("description", ld.get("description", ""))
            d.setdefault("category", ld.get("category", ""))
            d.setdefault("colour", ld.get("color", ""))
            b = ld.get("brand")
            if isinstance(b, dict):
                d.setdefault("brand", b.get("name", ""))
            if ld.get("image"):
                d.setdefault("image", ld["image"])
            offers = ld.get("offers") or {}
            if isinstance(offers, dict):
                d["price"] = _money(offers.get("price"))
                d["currency"] = offers.get("priceCurrency", "EUR")
                d["url"] = offers.get("url", "")
            break
    for plugins in iter_objects_after(flight, "plugins", "["):
        if not isinstance(plugins, list) or not plugins or not isinstance(plugins[0], dict):
            continue
        for p in plugins:
            data = p.get("data") or {}
            if p.get("name") == "attributes":
                for a in data.get("attributes", []):
                    val = (a.get("data") or {}).get("value", "")
                    code = a.get("code")
                    if code == "brand":
                        d["brand"] = val
                    elif code == "size":
                        d["size"] = val
                    elif code == "status":
                        d["condition"] = val
                    elif code == "color":
                        d["colour"] = val
                    elif code == "material":
                        d["material"] = val
            elif p.get("name") == "description" and data.get("description"):
                d["description"] = data["description"]
            elif p.get("name") == "make_offer" and data.get("photos"):
                urls = []
                for ph in data["photos"]:
                    full = ph.get("full_size_url") or ph.get("url")
                    if not full:
                        thumbs = ph.get("thumbnails") or []
                        full = thumbs[-1]["url"] if thumbs else None
                    if full:
                        urls.append(full)
                if urls:
                    d["photos"] = urls
        break
    for ps in iter_objects_after(flight, "pricingServices"):
        services = (ps or {}).get("services") or {}
        bp = services.get("buyerProtection") or {}
        sh = services.get("shipping") or {}
        if bp:
            d["service_fee"] = _money(bp.get("finalPrice"))
        if sh:
            d["shipping"] = 0.0 if sh.get("isFree") else _money(sh.get("finalPrice"))
        break
    return d


def listing_from_item_page(url: str, html: str) -> Listing | None:
    """Build a Listing from an item page alone (used for favourites)."""
    d = parse_item(html)
    m = re.search(r"/items/(\d+)", url)
    if not d.get("title") or not m:
        return None
    photos = d.get("photos") or ([d["image"]] if d.get("image") else [])
    it = Listing(id=int(m.group(1)), title=d["title"], url=d.get("url") or url, price=d.get("price"),
                 currency=d.get("currency", "EUR"), thumbnail=photos[0] if photos else "")
    return apply_details(it, d)


def apply_details(listing: Listing, details: dict) -> Listing:
    for k in ("description", "colour", "category", "material", "size", "condition", "brand"):
        if details.get(k) and not getattr(listing, k):
            setattr(listing, k, details[k])
    if details.get("description"):
        listing.description = details["description"]
    if details.get("photos"):
        listing.photos = details["photos"]
    if details.get("shipping") is not None:
        listing.shipping = details["shipping"]
    if details.get("service_fee") is not None and listing.service_fee is None:
        listing.service_fee = details["service_fee"]
    listing.details_fetched = True
    return listing


# ---------------------------------------------------------------- search + filters

def build_search_url(query: str, max_price: float | None = None, conditions: list[str] | None = None,
                     page: int = 1, order: str = "relevance") -> str:
    params: list[tuple[str, str]] = [("search_text", query), ("order", order)]
    if max_price is not None:
        params += [("price_to", f"{max_price:g}"), ("currency", "EUR")]
    for c in conditions or []:
        params.append(("status_ids[]", str(config.CONDITIONS[c])))
    if page > 1:
        params.append(("page", str(page)))
    return f"{config.VINTED_BASE}/catalog?{urlencode(params)}"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9.]+", " ", (s or "").lower()).strip()


def _brand_ok(item: Listing, brands: list[str]) -> bool:
    from .identify import norm as inorm
    have = inorm(item.brand)
    for b in brands:
        want = inorm(b)
        if want and (want == have or f" {want} " in f" {have} " or (not have and f" {want} " in f" {inorm(item.title)} ")):
            return True
    return False


def matches_filters(item: Listing, max_price: float | None = None, size: str | None = None,
                    brand: str | list[str] | None = None, conditions: list[str] | None = None,
                    item_type: str | None = None) -> bool:
    """Client-side filters (brand and size are matched by text; see DECISIONS.md)."""
    if max_price is not None and item.price is not None and item.price > max_price:
        return False
    brands = [brand] if isinstance(brand, str) else (brand or [])
    if brands and not _brand_ok(item, brands):
        return False
    if item_type:
        from .identify import detect_item_type, norm as inorm
        found = detect_item_type(item.category, inorm(item.title))
        if found and found != item_type:
            return False
    if size:
        want = _norm(size)
        have = _norm(item.size)
        # exact token match: "42" must not match "42.5"; also accept "UK 8" vs "8" style
        tokens = set(have.split()) | {have}
        if want not in tokens and want != have:
            return False
    if conditions:
        labels = {_norm(config.CONDITION_LABELS[c]) for c in conditions}
        if _norm(item.condition) not in labels:
            return False
    return True


def search(browser, query: str | list[str], limit: int = config.DEFAULT_LIMIT, max_price: float | None = None,
           size: str | None = None, brand: str | list[str] | None = None, conditions: list[str] | None = None,
           details: bool = True, max_pages: int = 3, item_type: str | None = None,
           must_mention: list[str] | None = None) -> list[Listing]:
    """Search vinted.ie and return up to `limit` filtered listings (optionally with item details).

    Several queries can be given; their results are merged (round-robin) and de-duplicated.
    `must_mention` drops listings whose title+description mention none of the given words
    (checked again after item pages are read)."""
    from .blockers import Blocked
    from .identify import has_phrase, norm as inorm
    queries = [query] if isinstance(query, str) else list(query)
    brands = [brand] if isinstance(brand, str) else (brand or [])
    pages_each = max_pages if len(queries) == 1 else 1

    def mentions(it: Listing) -> bool:
        if not must_mention:
            return True
        text = inorm(f"{it.title} {it.description}")
        return any(has_phrase(text, w) for w in must_mention)

    per_query: list[list[Listing]] = []
    seen: set[int] = set()
    stop_all = False
    for q in queries:
        if stop_all:
            break
        text = f"{brands[0]} {q}" if len(brands) == 1 and _norm(brands[0]) not in _norm(q) else q
        found: list[Listing] = []
        for page in range(1, pages_each + 1):
            url = build_search_url(text, max_price, conditions, page)
            if len(queries) > 1:
                # Several queries: a bot-check on one is skipped (pause, carry on with the rest).
                try:
                    html = browser.fetch(url, site="Vinted search", namespace="vinted_search",
                                         soft_block_backoff_s=20)
                except Blocked:
                    if browser.is_blocked(url):
                        if any(per_query) or found:
                            print("  ! Vinted keeps blocking searches; continuing with the results so far")
                            stop_all = True
                            break
                        raise
                    print(f"  ! skipped query “{q}” (Vinted bot-check)")
                    break
            else:
                html = browser.fetch(url, site="Vinted search", namespace="vinted_search")
            batch = parse_catalog(html)
            if not batch:
                break
            new = 0
            for it in batch:
                if it.id in seen:
                    continue
                seen.add(it.id)
                new += 1
                if matches_filters(it, max_price, size, brands, conditions, item_type):
                    found.append(it)
            if len(found) >= limit or new == 0:
                break
        per_query.append(found)
    # Round-robin so every query is represented; listings that already mention the required
    # words in their title go first.
    merged: list[Listing] = []
    for i in range(max((len(f) for f in per_query), default=0)):
        for f in per_query:
            if i < len(f):
                merged.append(f[i])
    if must_mention:
        merged.sort(key=lambda it: not mentions(it))
    results = merged[: limit if not must_mention else limit * 2]
    if details:
        skipped = 0
        for it in results:
            if browser.is_blocked(it.url):
                skipped += 1
                continue
            if must_mention and len([r for r in results[:results.index(it)] if mentions(r)]) >= limit:
                break
            try:
                html = browser.fetch(it.url, site="Vinted item page", namespace="vinted_item",
                                     soft_block_backoff_s=20)
            except Blocked:
                skipped += 1
                continue
            apply_details(it, parse_item(html))
        if skipped:
            print(f"  ! {skipped} item page(s) not read (Vinted bot-check); those rows use search-page data only")
    # Re-check with what the item pages added (real brand field, category).
    if item_type or brands:
        results = [it for it in results if matches_filters(it, brand=brands or None, item_type=item_type)]
    if must_mention:
        results = [it for it in results if mentions(it)]
    results = results[:limit]
    return results
