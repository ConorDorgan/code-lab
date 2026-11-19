import csv
import time

from vintedtool.browser import looks_blocked
from vintedtool.cache import Cache
from vintedtool.identify import identify_text
from vintedtool.pricing import Offer, PriceResult
from vintedtool.report import build_row, sort_rows, write_csv, write_html
from vintedtool.vinted import Listing


def listing(**kw):
    base = dict(id=1, title="Salomon XT-6", url="https://www.vinted.ie/items/1-x", price=100.0,
                service_fee=5.7, total_item_price=105.7, shipping=4.3, brand="Salomon", size="42",
                condition="Very good", thumbnail="https://img/1.webp")
    base.update(kw)
    return Listing(**base)


def test_build_row_saving():
    ident = identify_text("Salomon XT-6", brand_field="Salomon")
    offer = Offer("Salomon XT-6 Men Shoes", 180.0, "EUR", "https://shop/p", "Foot Locker IE", "retailer",
                  checked="2026-11-19", match="high")
    row = build_row(listing(), ident, PriceResult(offer, "high", "price found"))
    assert row["vinted_total_eur"] == 110.0
    assert row["retail_price_eur"] == 180.0 and row["retail_url"] == "https://shop/p"
    assert row["retail_checked"] == "2026-11-19"
    assert row["saving_eur"] == 70.0 and row["saving_pct"] == 38.9


def test_build_row_gbp_flagged():
    ident = identify_text("Salomon XT-6", brand_field="Salomon")
    offer = Offer("Salomon XT-6", 150.0, "GBP", "https://uk/p", "Salomon UK", "brand", match="high")
    row = build_row(listing(), ident, PriceResult(offer, "high", "price found"))
    assert row["converted_from_gbp"] == "yes" and row["retail_price_original"] == "£150.00"
    assert "converted from GBP" in row["notes"]


def test_build_row_no_price_and_missing_postage():
    ident = identify_text("Chaussures", brand_field="Salomon")
    row = build_row(listing(shipping=None), ident, PriceResult(None, "low", "no reliable price (low-confidence identification)"))
    assert row["retail_price_eur"] is None and row["saving_pct"] is None
    assert row["status"].startswith("no reliable price")
    assert "postage not shown" in row["notes"]


def test_sort_rows():
    rows = [{"saving_pct": None}, {"saving_pct": 10.0}, {"saving_pct": -5.0}, {"saving_pct": 40.0}]
    assert [r["saving_pct"] for r in sort_rows(rows)] == [40.0, 10.0, -5.0, None]


def test_write_outputs(tmp_path):
    ident = identify_text("Salomon XT-6", brand_field="Salomon")
    row = build_row(listing(title='<script>alert(1)</script>'), ident, None)
    write_csv([row], tmp_path / "r.csv")
    write_html([row], tmp_path / "r.html", "Test", ["meta"])
    rows = list(csv.DictReader((tmp_path / "r.csv").open()))
    assert rows[0]["title"] == "<script>alert(1)</script>" and "saving_pct" in rows[0]
    html = (tmp_path / "r.html").read_text()
    assert "<script>alert" not in html and "&lt;script&gt;" in html


def test_looks_blocked(fixture_text):
    assert looks_blocked(403, "", "")
    assert looks_blocked(200, "Just a moment...", "")
    assert looks_blocked(200, "Vinted", fixture_text("cloudflare_challenge.html"))
    assert looks_blocked(200, "Items | Vinted", fixture_text("vinted_catalog_salomon_xt6.html.gz")) is None


def test_cache_ttl(tmp_path):
    c = Cache(tmp_path, ttl_s=100)
    c.set("ns", "k", {"a": 1})
    assert c.get("ns", "k") == {"a": 1}
    c2 = Cache(tmp_path, ttl_s=0)
    time.sleep(0.01)
    assert c2.get("ns", "k") is None
    assert Cache(tmp_path, enabled=False).get("ns", "k") is None
