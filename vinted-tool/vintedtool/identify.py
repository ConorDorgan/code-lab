"""Work out what a listing actually is: brand, product line, model, item type, colour.

Rule-based first (Vinted brand field + title + description + category, matched against
data/products.json). If ANTHROPIC_API_KEY is set, the main photo plus the text is also sent to
Claude, which can fill in a model the text doesn't name.

Confidence levels (used later to decide whether a retail price is shown):
  high   - exact product/model identified
  medium - brand and product line known, exact model unclear
  low    - brand and item type only
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

from . import config

LEVELS = {"low": 0, "medium": 1, "high": 2}


def min_level(a: str, b: str) -> str:
    return a if LEVELS[a] <= LEVELS[b] else b


@dataclass
class Identification:
    brand: str = ""
    product_line: str = ""
    model: str = ""
    variant: str = ""
    item_type: str = ""
    colour: str = ""
    confidence: str = "low"
    source: str = "text"            # "text" or "text+photo (Claude)"
    discontinued: bool = False
    brand_key: str = ""
    notes: list[str] = field(default_factory=list)

    def _with_brand(self, name: str) -> str:
        if self.brand and name and norm(self.brand) in norm(name):
            return name  # e.g. brand "Jordan", model "Air Jordan 1 Low"
        return " ".join(p for p in (self.brand, name) if p)

    @property
    def product_name(self) -> str:
        parts = [self._with_brand(self.model or self.product_line), self.variant]
        name = " ".join(p for p in parts if p)
        if not (self.model or self.product_line) and self.item_type:
            name = f"{name} {self.item_type}".strip()
        return name

    @property
    def price_query(self) -> str | None:
        """What to search retailers for. None for low confidence (no reliable price)."""
        if self.confidence == "high":
            return " ".join(p for p in (self._with_brand(self.model), self.variant) if p)
        if self.confidence == "medium":
            return self._with_brand(self.product_line or self.model)
        return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["product_name"] = self.product_name
        return d


# ------------------------------------------------------------------ text normalisation

_FOLD = str.maketrans({"ø": "o", "æ": "ae", "ß": "ss", "œ": "oe", "ł": "l", "đ": "d"})

def norm(text: str) -> str:
    """Lowercase, strip punctuation and split letter/number runs, so 'XT-6', 'xt6' and 'XT 6'
    all become 'xt 6' and '990v6' becomes '990 v 6'. Patterns get the same treatment."""
    t = (text or "").lower().replace("'", "").replace("’", "").replace("+", " plus ")
    t = t.translate(_FOLD)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def has_phrase(haystack_norm: str, phrase: str) -> bool:
    p = norm(phrase)
    return bool(p) and f" {p} " in f" {haystack_norm} "


@lru_cache(maxsize=1)
def knowledge() -> dict:
    data = json.loads((Path(__file__).parent / "data" / "products.json").read_text())
    data.pop("_comment", None)
    return data


ITEM_TYPES = {
    "trainers": ["trainers", "trainer", "sneakers", "sneaker", "baskets", "running shoes", "runners",
                 "turnschuhe", "zapatillas", "scarpe", "chaussures", "shoes"],
    "boots": ["boots", "boot", "bottes", "stiefel", "botas", "chelsea"],
    "sandals": ["sandals", "sliders", "slides", "sandales"],
    "jacket": ["jacket", "jackets", "coat", "coats", "parka", "puffer", "veste", "doudoune", "jacke", "giacca",
               "anorak", "shell", "hardshell", "hoody", "chaqueta", "jas", "kurtka", "outerwear", "raincoat",
               "waterproof jacket", "regenjacke", "blouson", "manteau"],
    "fleece": ["fleece", "polaire"],
    "hoodie": ["hoodie", "sweatshirt", "sweat", "jumper", "sweater", "pullover", "pull", "crewneck"],
    "t-shirt": ["t shirt", "tshirt", "tee"],
    "shirt": ["shirt", "chemise"],
    "trousers": ["trousers", "pants", "joggers", "pantalon", "hose", "cargo", "bib", "salopettes", "leg"],
    "jeans": ["jeans", "denim"],
    "shorts": ["shorts", "short"],
    "dress": ["dress", "robe"],
    "skirt": ["skirt", "jupe"],
    "bag": ["bag", "backpack", "rucksack", "sac", "tote"],
    "hat": ["hat", "cap", "beanie", "bonnet", "casquette"],
    "gloves": ["gloves", "glove", "mittens", "mitts", "gants", "guantes", "handschuhe", "guanti"],
    "book": ["book", "livre", "buch", "libro"],
}

FOOTWEAR_TYPES = {"trainers", "boots", "sandals"}

COLOURS = {
    "black": ["black", "noir", "noire", "schwarz", "nero", "negro", "zwart", "czarny", "triple black"],
    "white": ["white", "blanc", "blanche", "blanches", "weiss", "bianco", "blanco", "wit", "bialy"],
    "grey": ["grey", "gray", "gris", "grau", "grigio", "grijs", "szary"],
    "blue": ["blue", "bleu", "blau", "blu", "azul", "blauw", "navy", "niebieski"],
    "red": ["red", "rouge", "rot", "rosso", "rojo", "rood", "czerwony"],
    "green": ["green", "vert", "grun", "verde", "groen", "olive", "khaki", "zielony"],
    "beige": ["beige", "cream", "ecru", "sand", "creme"],
    "brown": ["brown", "marron", "braun", "marrone", "bruin", "tan"],
    "pink": ["pink", "rose", "rosa", "roze"],
    "purple": ["purple", "violet", "lila", "lilac", "viola"],
    "yellow": ["yellow", "jaune", "gelb", "giallo", "amarillo"],
    "orange": ["orange", "arancione", "naranja"],
    "silver": ["silver", "argent", "metallic"],
}


def detect_item_type(category: str, text_norm: str) -> str:
    cat = norm(category)
    for t, words in ITEM_TYPES.items():
        if any(has_phrase(cat, w) for w in words):
            return t
    for t, words in ITEM_TYPES.items():
        if any(has_phrase(text_norm, w) for w in words):
            return t
    return ""


def detect_colour(vinted_colour: str, text_norm: str) -> str:
    if vinted_colour:
        return vinted_colour.strip().lower()
    found = [c for c, words in COLOURS.items() if any(has_phrase(text_norm, w) for w in words)]
    return "/".join(found[:2])


def find_brand(brand_field: str, text_norm: str) -> tuple[str, str]:
    """Return (brand_key, display name). Vinted's brand field wins; title is the fallback."""
    kb = knowledge()
    bf = norm(brand_field)
    for key, b in kb.items():
        if bf and any(norm(a) == bf or has_phrase(bf, a) for a in b["aliases"]):
            return key, b["name"]
    if bf:
        return "", brand_field.strip()
    for key, b in kb.items():
        if any(has_phrase(text_norm, a) for a in b["aliases"]):
            return key, b["name"]
    return "", ""


_COLLAB_RE = re.compile(r"(?:^|\s)(?:x|×)\s+[a-z0-9]", re.I)


def looks_like_collab(title: str) -> bool:
    """'Salomon XT-6 x Maison Margiela' -> True. Collabs retail very differently from the base model."""
    return bool(_COLLAB_RE.search(title or ""))


def identify_text(title: str, description: str = "", brand_field: str = "", category: str = "",
                  vinted_colour: str = "") -> Identification:
    title_n = norm(title)
    full_n = norm(f"{title} {description}")
    ident = Identification()
    ident.brand_key, ident.brand = find_brand(brand_field, title_n or full_n)
    ident.item_type = detect_item_type(category, title_n) or detect_item_type("", full_n)
    ident.colour = detect_colour(vinted_colour, title_n) or detect_colour("", full_n)

    b = knowledge().get(ident.brand_key)
    if not b:
        if ident.brand:
            ident.notes.append("brand not in local product list")
        return ident

    # Title first (most reliable), then description. Longest pattern wins (e.g. 'xt wings 2' over 'xt').
    for text_n, where in ((title_n, "title"), (full_n, "description")):
        best = None
        for line_name, line in b["lines"].items():
            for model_name, model in line.get("models", {}).items():
                for pat in model["patterns"]:
                    if has_phrase(text_n, pat) and (best is None or len(norm(pat)) > best[0]):
                        best = (len(norm(pat)), line_name, model_name, model)
        if best:
            _, ident.product_line, ident.model, model = best
            ident.confidence = "high"
            ident.discontinued = bool(model.get("discontinued"))
            for vname, vpats in (model.get("variants") or {}).items():
                if any(has_phrase(text_n, vp) for vp in vpats):
                    ident.variant = vname
                    break
            if where == "description":
                ident.notes.append("model found in description, not title")
            if looks_like_collab(title):
                ident.confidence = "medium"
                ident.notes.append("looks like a collaboration; base-model retail price may not apply")
            return ident
        for line_name, line in b["lines"].items():
            if any(has_phrase(text_n, p) for p in line.get("patterns", [])):
                ident.product_line = line_name
                ident.confidence = "medium"
                return ident
    return ident


# ------------------------------------------------------------------ optional: Claude vision

_CLAUDE_SCHEMA = {
    "type": "object",
    "properties": {
        "brand": {"type": "string"},
        "product_line": {"type": "string"},
        "model": {"type": "string", "description": "Exact model name, or empty if not identifiable"},
        "variant": {"type": "string", "description": "e.g. GTX, Mid, colourway name; empty if none"},
        "item_type": {"type": "string"},
        "colour": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "reason": {"type": "string"},
    },
    "required": ["brand", "product_line", "model", "variant", "item_type", "colour", "confidence", "reason"],
    "additionalProperties": False,
}

_PROMPT = """You identify second-hand items listed on Vinted so their new retail price can be looked up.
Use the photo and the listing text. Be strict:
- confidence "high" only if the exact model is clearly shown (readable branding/tags or an unmistakable design) or stated.
- "medium" if brand and product line are clear but not the exact model.
- "low" if you only know brand and item type.
Never guess a model you can't support from the photo or text; leave it empty instead.

Listing title: {title}
Brand field: {brand}
Category: {category}
Description: {description}"""


class ClaudeIdentifier:
    def __init__(self, api_key: str, model: str = config.CLAUDE_MODEL, cache=None):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.cache = cache
        self.errors = 0

    def identify(self, title: str, description: str, brand: str, category: str, photo_url: str) -> dict | None:
        key = f"{self.model}|{photo_url}|{title}"
        if self.cache and (hit := self.cache.get("claude_ident", key)) is not None:
            return hit
        import anthropic
        content = []
        if photo_url:
            content.append({"type": "image", "source": {"type": "url", "url": photo_url}})
        content.append({"type": "text", "text": _PROMPT.format(
            title=title, brand=brand or "(none)", category=category or "(unknown)",
            description=(description or "")[:1500])})
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": _CLAUDE_SCHEMA}},
                messages=[{"role": "user", "content": content}],
            )
        except anthropic.APIStatusError as e:
            self.errors += 1
            print(f"  ! Claude identification failed (HTTP {e.status_code}); using text-only result")
            return None
        except anthropic.APIConnectionError:
            self.errors += 1
            print("  ! Claude identification failed (connection); using text-only result")
            return None
        if resp.stop_reason != "end_turn":
            return None
        text = next((b.text for b in resp.content if b.type == "text"), "")
        try:
            out = json.loads(text)
        except json.JSONDecodeError:
            return None
        if self.cache:
            self.cache.set("claude_ident", key, out)
        return out


def merge_claude(ident: Identification, c: dict | None) -> Identification:
    """Fold a Claude result into the text-based identification, never lowering confidence."""
    if not c:
        return ident
    ident.source = "text+photo (Claude)"
    c_conf = c.get("confidence", "low")
    if ident.brand and c.get("brand") and norm(c["brand"]) not in norm(ident.brand) and norm(ident.brand) not in norm(c["brand"]):
        ident.notes.append(f"photo suggests brand '{c['brand']}' but listing says '{ident.brand}'")
        c_conf = min_level(c_conf, "medium")
    if LEVELS.get(c_conf, 0) > LEVELS[ident.confidence]:
        if not ident.brand:
            ident.brand = c.get("brand", "")
        ident.product_line = c.get("product_line") or ident.product_line
        if c_conf == "high" and c.get("model"):
            ident.model = c["model"]
        ident.variant = c.get("variant") or ident.variant
        ident.confidence = c_conf
        ident.notes.append(f"model from photo: {c.get('reason', '')[:120]}")
    elif ident.confidence == "high" and not ident.variant and c.get("variant"):
        # Claude may spot a variant (e.g. GTX) the text didn't mention; note it, don't apply.
        ident.notes.append(f"photo hints variant '{c['variant']}'")
    if not ident.item_type and c.get("item_type"):
        ident.item_type = c["item_type"].lower()
    if not ident.colour and c.get("colour"):
        ident.colour = c["colour"].lower()
    return ident


def identify_listing(listing, claude: ClaudeIdentifier | None = None) -> Identification:
    ident = identify_text(listing.title, listing.description, listing.brand, listing.category, listing.colour)
    if claude is not None:
        photo = (listing.photos or [listing.thumbnail] or [""])[0]
        c = claude.identify(listing.title, listing.description, listing.brand, listing.category, photo)
        ident = merge_claude(ident, c)
    return ident
