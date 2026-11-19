"""Playwright-backed page fetcher: polite delays, 24h cache, block detection.

We use a normal (headless by default) Chromium session. If a site serves a captcha or a
bot-check that doesn't clear on its own, we stop and raise Blocked — we never try to solve
or evade it.
"""
from __future__ import annotations

import os
import random
import time
from pathlib import Path
from urllib.parse import urlparse

from . import config
from .blockers import Blocked, record
from .cache import Cache

if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH") and Path("/opt/pw-browsers").exists():
    # Pre-installed browsers in some sandboxes; harmless elsewhere.
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/pw-browsers"

CHALLENGE_MARKERS = (
    "just a moment",
    "enable javascript and cookies to continue",
    "access to this page has been denied",
    "access denied",
    "captcha",
    "are you a robot",
    "verify you are human",
    "px-captcha",
)


def looks_blocked(status: int | None, title: str, html: str) -> str | None:
    """Return a reason string if the response looks like a block/challenge, else None."""
    if status in (401, 403, 429):
        return f"HTTP {status}"
    t = (title or "").lower()
    for m in CHALLENGE_MARKERS:
        if m in t:
            return f"challenge page ('{title.strip()[:60]}')"
    head = (html or "")[:20000].lower()
    small = len(html or "") < 60000  # real content pages are far bigger than challenge pages
    if small and ("_cf_chl_opt" in head or "/cdn-cgi/challenge-platform/" in head):
        return "Cloudflare challenge page"
    if small and ("px-captcha" in head or "g-recaptcha" in head):
        return "captcha page"
    return None


def polite_sleep() -> None:
    time.sleep(random.uniform(config.MIN_DELAY_S, config.MAX_DELAY_S))


class Browser:
    """Context manager wrapping one Chromium context. Pages are fetched one at a time."""

    def __init__(self, cache: Cache | None = None, headless: bool = True,
                 storage_state: Path | None = None, verbose: bool = True):
        self.cache = cache or Cache()
        self.headless = headless
        self.storage_state = storage_state
        self.verbose = verbose
        self._pw = self._browser = self._ctx = None
        self._blocked_hosts: dict[str, str] = {}
        self.live_requests = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _ensure(self):
        if self._ctx:
            return
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        kw = dict(locale="en-IE", user_agent=config.USER_AGENT, viewport={"width": 1366, "height": 900})
        if self.storage_state and Path(self.storage_state).exists():
            kw["storage_state"] = str(self.storage_state)
        self._ctx = self._browser.new_context(**kw)

    @property
    def context(self):
        self._ensure()
        return self._ctx

    def close(self):
        for obj in (self._ctx, self._browser):
            try:
                obj and obj.close()
            except Exception:
                pass
        if self._pw:
            self._pw.stop()
        self._pw = self._browser = self._ctx = None

    def is_blocked(self, url: str) -> bool:
        return urlparse(url).netloc in self._blocked_hosts

    def fetch(self, url: str, site: str, namespace: str = "pages", settle_ms: int = 2500,
              use_cache: bool = True, evaluate: str | None = None):
        """Return page HTML (or the result of `evaluate` JS if given). Cached for 24h.

        Raises Blocked if the site answers with a block/challenge. Once a host has blocked us
        in this run we don't hit it again.
        """
        cache_key = url + ("|eval:" + evaluate if evaluate else "")
        if use_cache:
            hit = self.cache.get(namespace, cache_key)
            if hit is not None:
                return hit
        host = urlparse(url).netloc
        if host in self._blocked_hosts:
            raise Blocked(site, url, self._blocked_hosts[host])

        self._ensure()
        if self.live_requests:
            polite_sleep()
        self.live_requests += 1
        if self.verbose:
            print(f"  · fetching {url}")
        page = self._ctx.new_page()
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            status = resp.status if resp else None
            page.wait_for_timeout(settle_ms)
            title, html = page.title(), page.content()
            reason = looks_blocked(status, title, html)
            if reason and status not in (401, 403, 429):
                # Some bot checks are non-interactive and finish on their own in a real
                # browser. Give it a few seconds like a person would; never interact with it.
                page.wait_for_timeout(8000)
                title, html = page.title(), page.content()
                reason = looks_blocked(None, title, html)
            if reason:
                self._blocked_hosts[host] = reason
                record(site, url, reason)
                raise Blocked(site, url, reason)
            result = page.evaluate(evaluate) if evaluate else html
        finally:
            page.close()
        if use_cache:
            self.cache.set(namespace, cache_key, result)
        return result
