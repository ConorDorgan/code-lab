import gzip

from vintedtool.identify import (Identification, identify_text, looks_like_collab, merge_claude, norm)
from vintedtool.vinted import parse_catalog


def test_norm_model_codes():
    assert norm("XT-6") == norm("xt6") == norm("XT 6") == "xt 6"
    assert norm("990v6") == "990 v 6"
    assert norm("Gore-Tex") == "gore tex"


def test_xt6_variants():
    i = identify_text("Salomon XT-6 GTX 42", brand_field="Salomon")
    assert (i.brand, i.model, i.variant, i.confidence) == ("Salomon", "XT-6", "GTX", "high")
    assert i.product_name == "Salomon XT-6 GTX" and i.price_query == "Salomon XT-6 GTX"
    assert identify_text("salomon xt-6 gor-tex noir", brand_field="Salomon").variant == "GTX"
    assert identify_text("Salomon XT 6 Unisexe Black 42 2/3", brand_field="Salomon").variant == ""


def test_colour_and_type():
    i = identify_text("Salomon XT-6 noir", brand_field="Salomon", category="Women Trainers")
    assert i.colour == "black" and i.item_type == "trainers"
    assert identify_text("Salomon XT-6", brand_field="Salomon", vinted_colour="Grey").colour == "grey"


def test_model_in_description_only():
    i = identify_text("Chaussures Salomon", "Modèle XT-6, taille 42", brand_field="Salomon")
    assert i.model == "XT-6" and i.confidence == "high"
    assert any("description" in n for n in i.notes)


def test_medium_and_low():
    i = identify_text("Salomon Speedcross trail shoes", brand_field="Salomon")
    assert i.confidence == "medium" and i.product_line == "Speedcross" and i.model == ""
    assert i.price_query == "Salomon Speedcross"
    low = identify_text("Chaussures Salmon", brand_field="Salomon", category="Women Trainers")
    assert low.confidence == "low" and low.price_query is None
    assert low.product_name == "Salomon trainers"


def test_unknown_brand_is_low():
    i = identify_text("Salomon XT-6 Jjjjound", brand_field="JJJJound")
    assert i.brand == "JJJJound" and i.confidence == "low"


def test_collab_capped_at_medium():
    assert looks_like_collab("Salomon XT-6 x Maison Margiela")
    assert not looks_like_collab("Salomon XT-6 Wren 40")
    i = identify_text("Salomon XT-6 x Maison Margiela", brand_field="Salomon")
    assert i.confidence == "medium"


def test_brand_not_duplicated_in_name():
    i = identify_text("Air Jordan 1 low", brand_field="Jordan")
    assert i.product_name == "Air Jordan 1 Low"


def test_other_brands():
    assert identify_text("Nike Air Max 90 white", brand_field="Nike").model == "Air Max 90"
    assert identify_text("NB 990v6 grey", brand_field="New Balance").model == "990v6"
    assert identify_text("Asics gel-kayano 14 silver", brand_field="ASICS").model == "Gel-Kayano 14"
    assert identify_text("Speedcross 5", brand_field="Salomon").discontinued is True


def test_real_sample_mostly_high(fixture_text):
    items = parse_catalog(fixture_text("vinted_catalog_salomon_xt6.html.gz"))
    idents = [identify_text(i.title, "", i.brand) for i in items]
    high = sum(i.confidence == "high" for i in idents)
    assert high >= 85, high
    assert all(i.model == "XT-6" for i in idents if i.confidence == "high")


def test_merge_claude_upgrades_but_never_downgrades():
    low = identify_text("Chaussures Salmon", brand_field="Salomon")
    out = merge_claude(low, {"brand": "Salomon", "product_line": "XT", "model": "XT-6", "variant": "",
                             "item_type": "trainers", "colour": "black", "confidence": "high", "reason": "logo"})
    assert out.confidence == "high" and out.model == "XT-6" and out.source.startswith("text+photo")
    high = identify_text("Salomon XT-6", brand_field="Salomon")
    out2 = merge_claude(high, {"brand": "Salomon", "product_line": "", "model": "", "variant": "GTX",
                               "item_type": "", "colour": "", "confidence": "low", "reason": ""})
    assert out2.confidence == "high" and out2.variant == ""      # variant hint noted, not applied
    assert any("GTX" in n for n in out2.notes)


def test_merge_claude_brand_conflict_caps_medium():
    i = identify_text("Chaussures", brand_field="Salomon")
    out = merge_claude(i, {"brand": "Nike", "product_line": "Air Max", "model": "Air Max 90", "variant": "",
                           "item_type": "trainers", "colour": "", "confidence": "high", "reason": ""})
    assert out.confidence == "medium" and out.model == ""


def test_claude_identifier_request_and_parse(monkeypatch, tmp_path):
    """No network: replace the SDK call and check what we send and how we read the answer."""
    import json as _json
    from types import SimpleNamespace
    from vintedtool.cache import Cache
    from vintedtool.identify import ClaudeIdentifier, identify_listing
    from vintedtool.vinted import Listing

    sent = {}

    def fake_create(**kw):
        sent.update(kw)
        body = {"brand": "Salomon", "product_line": "XT", "model": "XT-6", "variant": "GTX",
                "item_type": "trainers", "colour": "black", "confidence": "high", "reason": "logo + mudguard"}
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=_json.dumps(body))])

    cid = ClaudeIdentifier("test-key", cache=Cache(tmp_path))
    monkeypatch.setattr(cid.client.messages, "create", fake_create)
    it = Listing(id=1, title="Chaussures Salmon", url="u", brand="Salomon",
                 photos=["https://images1.vinted.net/x.webp"])
    ident = identify_listing(it, cid)
    assert ident.model == "XT-6" and ident.confidence == "high" and ident.source == "text+photo (Claude)"
    assert sent["model"] == "claude-opus-5-5"
    assert sent["output_config"]["format"]["type"] == "json_schema"
    content = sent["messages"][0]["content"]
    assert content[0] == {"type": "image", "source": {"type": "url", "url": "https://images1.vinted.net/x.webp"}}
    # cached: a second call doesn't hit the API
    sent.clear()
    identify_listing(it, cid)
    assert sent == {}
