from urllib.parse import parse_qs, urlparse

from vintedtool.vinted import (Listing, apply_details, build_search_url, extract_flight,
                               listing_from_item_page, matches_filters, parse_catalog, parse_item)

CATALOG = "vinted_catalog_salomon_xt6.html.gz"
ITEM = "vinted_item_10107798298.html.gz"


def test_flight_is_decoded(fixture_text):
    flight = extract_flight(fixture_text(CATALOG))
    assert '"productItem":{' in flight
    assert "\\u" not in flight[:1000]


def test_parse_catalog_basic(fixture_text):
    items = parse_catalog(fixture_text(CATALOG))
    assert len(items) == 96
    assert len({i.id for i in items}) == 96
    first = items[0]
    assert first.id == 10875275245
    assert first.title == "Salomon xt-6 wren 40"
    assert first.url == "https://www.vinted.ie/items/10875275245-salomon-xt-6-wren-40"
    assert (first.price, first.service_fee, first.total_item_price) == (107.0, 6.05, 113.05)
    assert first.brand == "Salomon"
    assert first.size == "40"
    assert first.condition == "Very good"
    assert first.thumbnail.startswith("https://images1.vinted.net/")


def test_catalog_prices_are_consistent(fixture_text):
    for it in parse_catalog(fixture_text(CATALOG)):
        assert it.currency == "EUR"
        assert it.price and it.service_fee is not None
        assert abs(it.price + it.service_fee - it.total_item_price) < 0.011


def test_promoted_flag_parsed(fixture_text):
    items = parse_catalog(fixture_text(CATALOG))
    assert any(i.is_promoted for i in items) and not all(i.is_promoted for i in items)


def test_parse_item_page(fixture_text):
    d = parse_item(fixture_text(ITEM))
    assert d["title"] == "Salomon XT-6 noir"
    assert d["brand"] == "Salomon"
    assert d["size"] == "37.5"
    assert d["condition"] == "Very good"
    assert d["colour"] == "Black"
    assert d["category"] == "Women Trainers"
    assert d["material"] == "Foam"
    assert d["description"].startswith("Salomon XT-6 – Black Taille 37")
    assert d["shipping"] == 7.29
    assert d["service_fee"] == 7.7
    assert d["price"] == 140.0
    assert len(d["photos"]) == 7


def test_listing_from_item_page_and_total(fixture_text):
    url = "https://www.vinted.ie/items/10107798298-salomon-xt-6-noir"
    it = listing_from_item_page(url, fixture_text(ITEM))
    assert it.id == 10107798298 and it.price == 140.0
    # 140 + 7.70 buyer protection + 7.29 postage
    assert it.total_cost == 154.99


def test_apply_details_keeps_search_fee():
    it = Listing(id=1, title="t", url="u", price=100, service_fee=5.7, total_item_price=105.7)
    apply_details(it, {"shipping": 4.5, "service_fee": 9.9, "colour": "Black", "description": "d"})
    assert it.service_fee == 5.7 and it.shipping == 4.5 and it.colour == "Black"
    assert it.total_cost == 110.2


def test_total_cost_without_postage():
    it = Listing(id=1, title="t", url="u", price=50, service_fee=3.2)
    assert it.total_cost == 53.2


def test_build_search_url_filters():
    url = build_search_url("salomon xt-6", max_price=120, conditions=["very_good", "new_with_tags"], page=2)
    q = parse_qs(urlparse(url).query)
    assert urlparse(url).netloc == "www.vinted.ie"
    assert q["search_text"] == ["salomon xt-6"]
    assert q["price_to"] == ["120"] and q["currency"] == ["EUR"]
    assert q["status_ids[]"] == ["2", "6"]
    assert q["page"] == ["2"]


def test_matches_filters():
    it = Listing(id=1, title="Salomon XT-6", url="u", price=100, brand="Salomon", size="42.5", condition="Very good")
    assert matches_filters(it)
    assert not matches_filters(it, max_price=90)
    assert matches_filters(it, size="42.5")
    assert not matches_filters(it, size="42")          # 42 must not match 42.5
    assert matches_filters(it, brand="salomon")
    assert not matches_filters(it, brand="nike")
    assert matches_filters(it, conditions=["very_good"])
    assert not matches_filters(it, conditions=["new_with_tags"])
    letter = Listing(id=2, title="t", url="u", size="M / 38 / 10")
    assert matches_filters(letter, size="M") and not matches_filters(letter, size="L")
