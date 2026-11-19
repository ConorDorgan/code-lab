"""Record anything that blocked us (403s, captcha/challenge pages) in BLOCKERS.md."""
from __future__ import annotations

import datetime as dt

from . import config

_HEADER = (
    "# Blockers\n\n"
    "Things that stopped part of the tool working. The tool never tries to bypass captchas or bot\n"
    "protection: when it meets one it stops that part, logs it here and carries on.\n\n"
)

_seen: set[str] = set()


class Blocked(Exception):
    """Raised when a site answers with a 403/429 or a challenge/captcha page."""

    def __init__(self, site: str, url: str, reason: str):
        super().__init__(f"{site}: {reason} ({url})")
        self.site, self.url, self.reason = site, url, reason


def record(site: str, url: str, reason: str) -> None:
    """Append one line per (site, reason) per run."""
    key = f"{site}|{reason}"
    if key in _seen:
        return
    _seen.add(key)
    path = config.BLOCKERS_FILE
    existing = path.read_text() if path.exists() else _HEADER
    if not existing.startswith("# Blockers"):
        existing = _HEADER + existing
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    existing = existing.rstrip("\n") + f"\n- {stamp} — **{site}**: {reason}. URL: {url}\n"
    path.write_text(existing)
