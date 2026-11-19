"""Find a current buy-new retail price for an identified product.

Rules (from the brief):
- Never invent a price: every price carries the URL it came from and the date it was checked.
- Source order: Google Shopping via SerpAPI (if SERPAPI_KEY), then the brand's own IE/UK site,
  then large retailers. EUR preferred; GBP converted at config.GBP_TO_EUR and flagged.
- Low-confidence identifications get "no reliable price" instead of a guess.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import asdict, dataclass, field
from urllib.parse import quote_plus, urljoin, urlparse

from . import config
from .blockers import Blocked, record
from .identify import LEVELS, Identification, has_phrase, knowledge, min_level, norm

# Second-hand marketplaces and resale platforms: not a "buy new at retail" price.
EXCLUDED_SELLERS = ("ebay", "vinted", "depop", "stockx", "goat", "klekt", "laced", "grailed",
                    "vestiaire", "wallapop", "adverts", "donedeal", "facebook", "poshmark",
                    "sellpy", "thredup", "back market", "backmarket", "leboncoin", "kleinanzeigen")
KIDS_WORDS = ("kids", "kid", "junior", "juniors", "youth", "toddler", "toddlers", "infant", "infants",
              "baby", "child", "children", "enfant", "enfants", "gs", "ps", "td", "little kids", "big kids")
ACCESSORY_WORDS = ("laces", "insole", "insoles", "socks", "cleaner", "shoe care", "keyring", "sticker")

_NUM = r"\d{1,5}(?:[.,]\d{3})*(?:[.,]\d{1,2})?"
_PREFIX_PRICE_RE = re.compile(rf"(?P<c>[€£])\s?(?P<n>{_NUM})")
_SUFFIX_PRICE_RE = re.compile(rf"(?<![\d.,])(?P<n>{_NUM})\s?(?P<c>[€£]|EUR\b|GBP\b)")
_PRICE_RE = re.compile(rf"[€£]\s?{_NUM}|{_NUM}\s?(?:[€£]|EUR\b|GBP\b)")
_NOISE_RE = re.compile(r"(save|you save|off|up to|delivery|shipping|over|under|spend)\s*[€£]\s?[\d.,]+"
                       r"|[€£]\s?[\d.,]+\s*(off|delivery)", re.I)


_TILE_NOISE_RE = re.compile(r"(this item is on sale|price dropped|sale price|was price|now only|rrp)\b.*$", re.I)


def today() -> str:
    return dt.date.today().isoformat()


def parse_amount(s: str) -> float | None:
    s = s.strip()
    if re.search(r"[.,]\d{1,2}$", s):
        whole, dec = s[:-3 if s[-3] in ".," else -2], s[-2:].lstrip(".,")
        whole = re.sub(r"[.,]", "", whole)
        try:
            return float(f"{whole}.{dec}")
        except ValueError:
            return None
    try:
        return float(re.sub(r"[.,]", "", s))
    except ValueError:
        return None


def find_prices(text: str) -> list[tuple[float, str]]:
    """All (amount, currency) pairs in a snippet, ignoring 'save €20'-style noise."""
    text = _NOISE_RE.sub(" ", text or "")
    found: list[tuple[int, float, str]] = []
    taken: list[tuple[int, int]] = []
    # "€ 199,99" (symbol first) wins over "199,99 €"; a symbol already used as a prefix can't
    # also be a suffix, so "XT-6 € 199,99" is 199.99, not 6.
    for m in _PREFIX_PRICE_RE.finditer(text):
        found.append((m.start(), parse_amount(m.group("n")), m.group("c")))
        taken.append(m.span())
    for m in _SUFFIX_PRICE_RE.finditer(text):
        if any(a < m.end() and m.start() < b for a, b in taken):
            continue
        found.append((m.start(), parse_amount(m.group("n")), m.group("c")))
    out = []
    for _, amt, cur in sorted(found):
        if amt is None or amt < 1:
            continue
        out.append((amt, "GBP" if cur in ("£", "GBP") else "EUR"))
    return out


@dataclass
class Offer:
    title: str
    price: float
    currency: str
    url: str
    source: str              # e.g. "Foot Locker IE" or "Google Shopping: JD Sports"
    source_kind: str         # "serpapi", "brand", "retailer"
    checked: str = field(default_factory=today)
    original_price: float | None = None   # pre-sale price if the retailer shows one
    in_stock: bool | None = None
    discontinued: bool = False
    match: str = ""          # "high"/"medium"
    notes: list[str] = field(default_factory=list)

    @property
    def converted(self) -> bool:
        return self.currency == "GBP"

    @property
    def price_eur(self) -> float:
        if self.currency == "GBP":
            return round(self.price * config.GBP_TO_EUR, 2)
        return round(self.price, 2)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.update(price_eur=self.price_eur, converted=self.converted)
        return d


@dataclass
class PriceResult:
    offer: Offer | None
    confidence: str          # final confidence for this row
    status: str              # human-readable: price found / no reliable price / why not
    sources_tried: list[str] = field(default_factory=list)
    discontinued: bool = False


# ------------------------------------------------------------------ matching

def _model_patterns(ident: Identification) -> tuple[list[str], dict[str, list[str]]]:
    b = knowledge().get(ident.brand_key) or {}
    line = (b.get("lines") or {}).get(ident.product_line) or {}
    model = (line.get("models") or {}).get(ident.model)
    if model:
        return model["patterns"], model.get("variants") or {}
    return ([ident.model] if ident.model else []), {}


def _brand_present(ident: Identification, t: str) -> bool:
    b = knowledge().get(ident.brand_key)
    aliases = b["aliases"] if b else [ident.brand]
    return any(has_phrase(t, a) for a in aliases if a)


def match_level(ident: Identification, title: str, brand_site: bool = False) -> str | None:
    """How well a retail product title matches the identified item: 'high', 'medium' or None."""
    t = norm(title)
    if not t:
        return None
    if not brand_site and not _brand_present(ident, t):
        return None
    if any(has_phrase(t, w) for w in KIDS_WORDS):
        return None
    if any(has_phrase(t, w) for w in ACCESSORY_WORDS):
        return None
    if ident.model:
        pats, variants = _model_patterns(ident)
        if not any(has_phrase(t, p) for p in pats):
            return None
        if ident.variant:
            wanted = variants.get(ident.variant) or [ident.variant]
            return "high" if any(has_phrase(t, v) for v in wanted) else "medium"
        other = [v for vs in variants.values() for v in vs]
        return "medium" if any(has_phrase(t, v) for v in other) else "high"
    if ident.product_line:
        b = knowledge().get(ident.brand_key) or {}
        line = (b.get("lines") or {}).get(ident.product_line) or {}
        pats = line.get("patterns") or [ident.product_line]
        return "medium" if any(has_phrase(t, p) for p in pats) else None
    return None


def choose(offers: list[Offer], ident: Identification, brand_site: bool = False) -> Offer | None:
    """Best match level first; then EUR over converted GBP; then the cheapest new price."""
    best = None
    for o in offers:
        lvl = match_level(ident, o.title, brand_site)
        if not lvl:
            continue
        o.match = lvl
        key = (-LEVELS[lvl], o.converted, o.price_eur)
        if best is None or key < best[0]:
            best = (key, o)
    return best[1] if best else None


# ------------------------------------------------------------------ parsers

def parse_serpapi(data: dict, checked: str | None = None) -> list[Offer]:
    """Google Shopping results from SerpAPI -> new-item offers (second-hand/resale removed)."""
    offers = []
    for r in (data.get("shopping_results") or []) + (data.get("inline_shopping_results") or []):
        seller = (r.get("source") or "").strip()
        if any(x in seller.lower() for x in EXCLUDED_SELLERS):
            continue
        if r.get("second_hand_condition") or "used" in " ".join(r.get("extensions") or []).lower():
            continue
        price = r.get("extracted_price")
        price_str = r.get("price") or ""
        cur = "GBP" if "£" in price_str else "EUR" if ("€" in price_str or "EUR" in price_str) else None
        if price is None or cur is None:
            continue  # unknown currency: don't guess
        url = r.get("link") or r.get("product_link")
        if not url:
            continue
        o = Offer(title=r.get("title", ""), price=float(price), currency=cur, url=url,
                  source=f"Google Shopping: {seller or 'unknown seller'}", source_kind="serpapi",
                  checked=checked or today())
        if r.get("extracted_old_price"):
            o.original_price = float(r["extracted_old_price"])
        offers.append(o)
    return offers


def extract_tiles(html: str, page_url: str, url_hint: str = "") -> list[Offer]:
    """Generic product-tile scraper for a retailer search page.

    For every link to a product page, climb to the smallest ancestor that shows a price and
    read the name and price(s) from it. Works across most shop layouts without per-site code.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    host = urlparse(page_url).netloc
    seen: dict[str, Offer] = {}
    for a in soup.find_all("a", href=True):
        href = urljoin(page_url, a["href"]).split("#")[0]
        if urlparse(href).netloc != host or (url_hint and url_hint not in href) or "search" in href:
            continue
        if href in seen:
            continue
        el, text = a, ""
        for _ in range(6):
            text = el.get_text(" ", strip=True)
            if find_prices(text) or el.parent is None:
                break
            el = el.parent
        prices = find_prices(text)
        if not prices or len(text) > 500:
            continue
        name = (a.get("title") or a.get("aria-label") or a.get_text(" ", strip=True) or "").strip()
        if len(norm(name)) < 4 or find_prices(name):
            name = _PRICE_RE.sub(" ", _NOISE_RE.sub(" ", text))
        name = _TILE_NOISE_RE.sub(" ", name)
        name = re.sub(r"\s+", " ", name).strip()[:200]
        cur = prices[0][1]
        amounts = sorted(p for p, c in prices if c == cur)
        o = Offer(title=name, price=amounts[0], currency=cur, url=href, source="", source_kind="retailer")
        if amounts[-1] > amounts[0]:
            o.original_price = amounts[-1]
        seen[href] = o
    return list(seen.values())


def parse_product_jsonld(html: str) -> dict | None:
    """Read schema.org Product/ProductGroup data from a product page: name, min price, currency, availability."""
    blocks = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S | re.I)
    for raw in blocks:
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        for node in data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []:
            if not isinstance(node, dict) or node.get("@type") not in ("Product", "ProductGroup"):
                continue
            offers = []
            products = [node] + [v for v in node.get("hasVariant") or [] if isinstance(v, dict)]
            for p in products:
                off = p.get("offers")
                for o in off if isinstance(off, list) else [off] if off else []:
                    if not isinstance(o, dict):
                        continue
                    price = o.get("price", o.get("lowPrice"))
                    try:
                        price = float(str(price).replace(",", "."))
                    except (TypeError, ValueError):
                        continue
                    offers.append((price, o.get("priceCurrency", ""), str(o.get("availability", ""))))
            if not offers:
                continue
            cur_offers = [x for x in offers if x[1] in ("EUR", "GBP")] or offers
            price, cur, _ = min(cur_offers)
            avail = " ".join(x[2] for x in offers).lower()
            return {
                "name": node.get("name", ""),
                "price": price,
                "currency": cur,
                "in_stock": "instock" in avail.replace(" ", "") or "in_stock" in avail,
                "discontinued": "discontinued" in avail,
            }
    return None


# ------------------------------------------------------------------ finder

class PriceFinder:
    def __init__(self, browser, cache, serpapi_key: str | None = None, retailers=None,
                 verify_product_page: bool = True, http_client=None):
        self.browser = browser
        self.cache = cache
        self.serpapi_key = serpapi_key
        self.retailers = retailers if retailers is not None else config.RETAILERS
        self.verify = verify_product_page
        self.http = http_client
        self._memo: dict[str, PriceResult] = {}
        self.blocked_sources: set[str] = set()

    # --- sources

    def _serpapi(self, query: str) -> list[Offer]:
        key = f"google_shopping|ie|{query}"
        hit = self.cache.get("serpapi", key)
        if hit is None:
            import httpx
            client = self.http or httpx.Client(timeout=30)
            r = client.get("https://serpapi.com/search.json", params={
                "engine": "google_shopping", "q": query, "gl": "ie", "hl": "en",
                "location": "Ireland", "api_key": self.serpapi_key})
            if r.status_code in (401, 403):
                raise Blocked("SerpAPI", "https://serpapi.com/search.json", f"HTTP {r.status_code} (check SERPAPI_KEY)")
            r.raise_for_status()
            hit = {"checked": today(), "data": r.json()}
            self.cache.set("serpapi", key, hit)
        return parse_serpapi(hit["data"], hit["checked"])

    def _retailer(self, rt: config.Retailer, query: str) -> list[Offer]:
        url = rt.search_url.format(q=quote_plus(query))
        html = self.browser.fetch(url, site=rt.name, namespace="retail_search", settle_ms=3000,
                                  wait_for_prices=True)
        offers = extract_tiles(html, url, rt.product_url_hint)
        checked = today()
        for o in offers:
            o.source, o.source_kind, o.checked = rt.name, rt.kind, checked
        return offers

    def _verify(self, offer: Offer, ident: Identification, brand_site: bool) -> Offer:
        """Open the chosen product page and confirm price/currency from its structured data."""
        if not self.verify or offer.source_kind == "serpapi":
            return offer
        try:
            html = self.browser.fetch(offer.url, site=offer.source, namespace="retail_product", settle_ms=3000)
        except Blocked:
            offer.notes.append("product page blocked; price taken from search results tile")
            return offer
        except Exception as e:  # network hiccup: keep the tile price, say so
            offer.notes.append(f"product page not checked ({type(e).__name__})")
            return offer
        ld = parse_product_jsonld(html)
        if not ld:
            offer.notes.append("price from search results tile (no structured data on product page)")
            return offer
        if ld["name"] and not match_level(ident, ld["name"], brand_site):
            offer.notes.append("product page name didn't match; kept tile price")
            return offer
        if ld["name"]:
            offer.title = ld["name"]
        if ld["currency"] in ("EUR", "GBP"):
            if abs(ld["price"] - offer.price) > 0.01:
                offer.notes.append(f"product page price {ld['price']:.2f} {ld['currency']} (tile said {offer.price:.2f})")
            offer.price, offer.currency = ld["price"], ld["currency"]
        offer.in_stock = ld["in_stock"]
        offer.discontinued = ld["discontinued"]
        return offer

    def sources_for(self, ident: Identification) -> list[tuple[str, object]]:
        out: list[tuple[str, object]] = []
        if self.serpapi_key:
            out.append(("serpapi", None))
        brand = norm(ident.brand)
        for rt in self.retailers:
            if rt.kind == "brand":
                if any(norm(b) == brand or norm(b) == ident.brand_key for b in rt.brands):
                    out.append(("brand", rt))
        for rt in self.retailers:
            if rt.kind == "retailer":
                out.append(("retailer", rt))
        return out

    def find(self, ident: Identification) -> PriceResult:
        query = ident.price_query
        if query is None:
            return PriceResult(None, ident.confidence, "no reliable price (low-confidence identification)",
                               discontinued=ident.discontinued)
        memo_key = f"{query}|{ident.confidence}"
        if memo_key in self._memo:
            return self._memo[memo_key]

        tried: list[str] = []
        fallback: Offer | None = None
        found: Offer | None = None
        for kind, rt in self.sources_for(ident):
            name = "SerpAPI Google Shopping" if kind == "serpapi" else rt.name
            if name in self.blocked_sources:
                continue
            tried.append(name)
            try:
                offers = self._serpapi(query) if kind == "serpapi" else self._retailer(rt, query)
            except Blocked as e:
                self.blocked_sources.add(name)
                print(f"  ! {name} blocked us ({e.reason}); skipping it for this run")
                continue
            except Exception as e:
                print(f"  ! {name} failed ({type(e).__name__}: {str(e)[:80]}); skipping")
                if kind == "serpapi":
                    record("SerpAPI", "https://serpapi.com", f"request failed: {type(e).__name__}")
                continue
            brand_site = kind == "brand"
            best = choose(offers, ident, brand_site)
            if not best:
                continue
            best = self._verify(best, ident, brand_site)
            if LEVELS[best.match] >= LEVELS[ident.confidence]:
                found = best
                break
            if fallback is None or LEVELS[best.match] > LEVELS[fallback.match]:
                fallback = best
        offer = found or fallback
        discontinued = ident.discontinued or bool(offer and offer.discontinued)
        if not offer:
            status = "no retail match found"
            if discontinued:
                status = "discontinued; no retail price found"
            res = PriceResult(None, ident.confidence, status, tried, discontinued)
        else:
            conf = min_level(ident.confidence, offer.match)
            if conf == "low":
                res = PriceResult(None, conf, "no reliable price (weak retail match)", tried, discontinued)
            else:
                status = "price found"
                if offer.match == "medium" and ident.confidence == "high":
                    status = "closest retail match is a different variant"
                if discontinued:
                    status = "discontinued; last retail price found"
                res = PriceResult(offer, conf, status, tried, discontinued)
        self._memo[memo_key] = res
        return res
