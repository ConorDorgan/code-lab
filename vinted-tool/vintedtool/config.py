"""Central configuration. Secrets come from .env only; everything else lives here."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# .env in vinted-tool/ wins; a .env at the repo root is also read (never overrides real env vars).
load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

VINTED_BASE = "https://www.vinted.ie"

# Fixed conversion rate used for any GBP retail price. Every converted price is flagged.
# Update by hand when it drifts; deliberately not fetched live so results are reproducible.
GBP_TO_EUR = 1.17

# Polite crawling
MIN_DELAY_S = 2.0
MAX_DELAY_S = 5.0
DEFAULT_LIMIT = 50
CACHE_TTL_S = 24 * 60 * 60
CACHE_DIR = ROOT / ".cache"
OUTPUT_DIR = ROOT / "output"
SESSION_FILE = ROOT / "session" / "vinted_session.json"
BLOCKERS_FILE = ROOT / "BLOCKERS.md"

# Model used for optional photo identification (only if ANTHROPIC_API_KEY is set).
CLAUDE_MODEL = os.environ.get("VINTED_TOOL_CLAUDE_MODEL", "claude-opus-5-5")

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)

# Vinted condition filter -> status_ids used by the catalog URL.
CONDITIONS = {
    "new_with_tags": 6,
    "new_without_tags": 1,
    "very_good": 2,
    "good": 3,
    "satisfactory": 4,
}
# Human labels as Vinted shows them (English UI).
CONDITION_LABELS = {
    "new_with_tags": "New with tags",
    "new_without_tags": "New without tags",
    "very_good": "Very good",
    "good": "Good",
    "satisfactory": "Satisfactory",
}


@dataclass
class Retailer:
    """A retail site we can search for a new-price. Order in RETAILERS = priority."""
    key: str
    name: str
    search_url: str  # {q} is replaced with the URL-encoded query
    currency: str
    kind: str  # "brand" (brand's own site) or "retailer"
    brands: list[str] = field(default_factory=list)  # for brand sites: which brands it sells
    product_url_hint: str = ""  # regex every product link matches (filters nav links)
    item_types: list[str] = field(default_factory=list)  # only used for these item types (empty = all)


# Price sources after SerpAPI, in the order the brief asks for:
# brand's own IE/UK site first, then large retailers. Irish (EUR) before UK (GBP).
RETAILERS: list[Retailer] = [
    Retailer("salomon_ie", "Salomon IE", "https://www.salomon.com/en-ie/search?q={q}", "EUR", "brand", ["salomon"], "/product/"),
    Retailer("salomon_gb", "Salomon UK", "https://www.salomon.com/en-gb/search?q={q}", "GBP", "brand", ["salomon"], "/product/"),
    Retailer("tnf_ie", "The North Face IE", "https://www.thenorthface.ie/search?q={q}", "EUR", "brand", ["the north face"], r"\.html"),
    Retailer("arcteryx_ie", "Arc'teryx IE", "https://arcteryx.com/ie/en/search?q={q}", "EUR", "brand", ["arc'teryx"], "/shop/"),
    Retailer("montbell_uk", "Montbell UK", "https://www.montbell.co.uk/search?q={q}", "GBP", "brand", ["montbell"], "/products/"),
    Retailer("nike_ie", "Nike IE", "https://www.nike.com/ie/w?q={q}", "EUR", "brand", ["nike", "jordan"], "/t/"),
    Retailer("adidas_ie", "adidas IE", "https://www.adidas.ie/search?q={q}", "EUR", "brand", ["adidas"], r"\.html"),
    Retailer("newbalance_ie", "New Balance IE", "https://www.newbalance.ie/search?q={q}", "EUR", "brand", ["new balance"], "/pd/"),
    Retailer("zalando_ie", "Zalando IE", "https://www.zalando.ie/catalogue/?q={q}", "EUR", "retailer", [], r"\.html"),
    Retailer("footlocker_ie", "Foot Locker IE", "https://www.footlocker.ie/en/search?query={q}", "EUR", "retailer", [], "/product/",
             ["trainers", "boots", "sandals", ""]),
    Retailer("53north_ie", "53 Degrees North", "https://www.53degreesnorth.ie/search?q={q}", "EUR", "retailer", [], "/products/"),
    Retailer("ellisbrigham", "Ellis Brigham", "https://www.ellis-brigham.com/search?q={q}", "GBP", "retailer", [], r"-\d{6,}$"),
    Retailer("jdsports_ie", "JD Sports IE", "https://www.jdsports.ie/search/{q}/", "EUR", "retailer", [], "/product/"),
    Retailer("lifestyle_ie", "Life Style Sports", "https://www.lifestylesports.com/ie/search?q={q}", "EUR", "retailer", [], "/ie/"),
    Retailer("asos", "ASOS", "https://www.asos.com/search/?q={q}", "EUR", "retailer", [], "/prd/"),
    Retailer("end", "END. Clothing", "https://www.endclothing.com/ie/catalogsearch/result/?q={q}", "EUR", "retailer", [], r"\.html"),
]


def env(name: str) -> str | None:
    v = os.environ.get(name, "").strip()
    return v or None
