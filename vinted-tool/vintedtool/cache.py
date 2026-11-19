"""Tiny on-disk cache so repeat runs within 24h don't re-hit any site."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from . import config


class Cache:
    def __init__(self, root: Path | None = None, ttl_s: int = config.CACHE_TTL_S, enabled: bool = True):
        self.root = root or config.CACHE_DIR
        self.ttl_s = ttl_s
        self.enabled = enabled

    def _path(self, namespace: str, key: str) -> Path:
        h = hashlib.sha256(key.encode()).hexdigest()[:32]
        return self.root / namespace / f"{h}.json"

    def get(self, namespace: str, key: str):
        if not self.enabled:
            return None
        p = self._path(namespace, key)
        if not p.exists():
            return None
        try:
            entry = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        if time.time() - entry.get("stored_at", 0) > self.ttl_s:
            return None
        return entry["value"]

    def set(self, namespace: str, key: str, value) -> None:
        if not self.enabled:
            return
        p = self._path(namespace, key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"stored_at": time.time(), "key": key, "value": value}))
        tmp.replace(p)
