import json

import pytest

from vintedtool import config
from vintedtool.blockers import Blocked
from vintedtool.cache import Cache
from vintedtool.identify import identify_text
from vintedtool.pricing import (Offer, PriceFinder, choose, extract_tiles, find_prices, match_level,
                                parse_amount, parse_product_jsonld, parse_serpapi)

FL_URL = "https://www.footlocker.ie/en/search?query=salomon+xt-6"


def xt6(variant_text=""):
    return identify_text(f"Salomon XT-6 {variant_text}".strip(), brand_field="Salomon")


def test_parse_amounts():
    assert parse_amount("199,99") == 199.99
    assert parse_amount("1.299,00") == 1299.0
    assert parse_amount("1,299.00") == 1299.0
    assert parse_amount("180") == 180.0
    assert find_prices("Salomon XT-6 € 199,99") == [(199.99, "EUR")]
    assert find_prices("£150 was £180") == [(150.0, "GBP"), (180.0, "GBP")]
    assert find_prices("SAVE €39 Price dropped from € 179,99 to € 140,00") == [(179.99, "EUR"), (140.0, "EUR")]


def test_extract_tiles_footlocker(fixture_text):
    offers = extract_tiles(fixture_text("footlocker_search_salomon_xt6.html.gz"), FL_URL, "/product/")
    assert len(offers) >= 20
    assert all("/product/" in o.url for o in offers)
    gtx = [o for o in offers if "GTX" in o.title]
    assert gtx and all(o.price == 199.99 and o.currency == "EUR" for o in gtx)
    sale = [o for o in offers if o.original_price]
    assert sale and all(o.original_price == 179.99 and o.price < 179.99 for o in sale)
    assert not any("on sale" in o.title.lower() for o in offers)


def test_jsonld_product_page(fixture_text):
    ld = parse_product_jsonld(fixture_text("footlocker_pdp_xt6_gtx.html.gz"))
    assert ld == {"name": "Salomon XT-6 GTX - Women Shoes", "price": 199.99, "currency": "EUR",
                  "in_stock": True, "discontinued": False}


def test_match_levels():
    plain, gtx = xt6(), xt6("GTX")
    assert match_level(plain, "Salomon XT-6 Men Shoes") == "high"
    assert match_level(plain, "Salomon XT-6 GTX Men Shoes") == "medium"     # different variant
    assert match_level(gtx, "Salomon XT-6 GTX - Women Shoes") == "high"
    assert match_level(gtx, "Salomon XT-6 Men Shoes") == "medium"
    assert match_level(plain, "Salomon XT-4 OG") is None                   # different model
    assert match_level(plain, "Nike XT-6") is None                          # wrong brand
    assert match_level(plain, "XT-6", brand_site=True) == "high"            # brand implied on brand site
    assert match_level(plain, "Salomon XT-6 Kids") is None
    assert match_level(plain, "Salomon XT-6 replacement laces") is None
    line = identify_text("Salomon Speedcross trainers", brand_field="Salomon")
    assert match_level(line, "Salomon Speedcross 6 GTX") == "medium"


def test_choose_prefers_best_match_then_eur_then_cheapest(fixture_text):
    offers = extract_tiles(fixture_text("footlocker_search_salomon_xt6.html.gz"), FL_URL, "/product/")
    best = choose(offers, xt6("GTX"))
    assert best.match == "high" and "GTX" in best.title and best.price == 199.99
    plain = choose(offers, xt6())
    assert plain.match == "high" and "GTX" not in plain.title and "EXPANSE" not in plain.title
    # regular price (179.99) is used, not a colourway-specific sale price; the sale is noted
    assert plain.price == 179.99 and plain.original_price is None
    assert any("on sale new from €120.00" in n for n in plain.notes)
    only_sale = [o for o in offers if o.original_price]
    assert choose(only_sale, xt6()).price == 120.0
    eur = Offer("Salomon XT-6", 160, "EUR", "u1", "s", "retailer")
    gbp = Offer("Salomon XT-6", 120, "GBP", "u2", "s", "retailer")
    assert choose([gbp, eur], xt6()) is eur
    s_lab = identify_text("Salomon S/LAB XT-6", brand_field="Salomon")
    assert s_lab.variant == "S/LAB" and match_level(s_lab, "Salomon XT-6 Men Shoes") == "medium"


def test_serpapi_parsing_filters_used_and_resale(fixture_text):
    data = json.loads(fixture_text("serpapi_google_shopping_sample.json"))
    offers = parse_serpapi(data, checked="2026-11-19")
    sources = {o.source for o in offers}
    assert not any(x in s for s in sources for x in ("eBay", "StockX"))
    assert "https://used.example.com/1" not in {o.url for o in offers}
    uk = next(o for o in offers if o.currency == "GBP")
    assert uk.converted and uk.price_eur == round(150 * config.GBP_TO_EUR, 2)
    assert all(o.url and o.checked == "2026-11-19" for o in offers)
    best = choose(offers, xt6())
    assert best.price == 180.0 and best.url.startswith("https://www.salomon.com/")


class FakeBrowser:
    def __init__(self, pages=None, blocked=()):
        self.pages, self.blocked, self.calls = pages or {}, set(blocked), []

    def fetch(self, url, site, **kw):
        self.calls.append(url)
        for key in self.blocked:
            if key in url:
                raise Blocked(site, url, "HTTP 403")
        for key, html in self.pages.items():
            if key in url:
                return html
        return "<html><body>nothing</body></html>"


class FakeHttp:
    def __init__(self, data):
        self.data, self.calls = data, 0

    def get(self, url, params=None):
        self.calls += 1
        data = self.data

        class R:
            status_code = 200

            def json(self):
                return data

            def raise_for_status(self):
                pass
        return R()


def test_finder_serpapi_first(fixture_text, tmp_path):
    data = json.loads(fixture_text("serpapi_google_shopping_sample.json"))
    http = FakeHttp(data)
    b = FakeBrowser()
    f = PriceFinder(b, Cache(tmp_path), serpapi_key="k", http_client=http)
    res = f.find(xt6())
    assert res.offer.price == 180.0 and res.confidence == "high" and res.status == "price found"
    assert res.offer.source == "Google Shopping: Salomon IE" and res.offer.checked
    assert b.calls == []                      # no retailer pages needed
    f.find(xt6())                             # memoised
    assert http.calls == 1


def test_finder_falls_back_to_retailers_and_skips_blocked(fixture_text, tmp_path):
    b = FakeBrowser(pages={"footlocker.ie/en/search": fixture_text("footlocker_search_salomon_xt6.html.gz"),
                           "footlocker.ie/en/product": fixture_text("footlocker_pdp_xt6_gtx.html.gz")},
                    blocked=["salomon.com", "zalando"])
    f = PriceFinder(b, Cache(tmp_path), serpapi_key=None)
    res = f.find(xt6("GTX"))
    assert res.offer is not None and res.offer.source == "Foot Locker IE"
    assert res.offer.price == 199.99 and res.offer.in_stock is True
    assert res.offer.url.startswith("https://www.footlocker.ie/en/product/")
    assert {"Salomon IE", "Zalando IE"} <= f.blocked_sources
    assert res.sources_tried[:3] == ["Salomon IE", "Salomon UK", "Zalando IE"]


def test_finder_low_confidence_gives_no_price(tmp_path):
    f = PriceFinder(FakeBrowser(), Cache(tmp_path))
    res = f.find(identify_text("Chaussures Salmon", brand_field="Salomon"))
    assert res.offer is None and res.status.startswith("no reliable price")


def test_finder_no_match(tmp_path):
    f = PriceFinder(FakeBrowser(), Cache(tmp_path), retailers=config.RETAILERS[5:6])
    res = f.find(xt6())
    assert res.offer is None and res.status == "no retail match found"


def test_discontinued_flag(tmp_path):
    ident = identify_text("Salomon Speedcross 5", brand_field="Salomon")
    f = PriceFinder(FakeBrowser(), Cache(tmp_path), retailers=[])
    res = f.find(ident)
    assert res.discontinued and "discontinued" in res.status
