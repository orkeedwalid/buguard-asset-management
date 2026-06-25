import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

class SimpleCache:
    def __init__(self, ttl_seconds: int = 300):
        self._store = {}
        self._ttl = ttl_seconds

    def _make_key(self, data: dict) -> str:
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()

    def get(self, data: dict) -> Optional[dict]:
        key = self._make_key(data)
        if key not in self._store:
            return None
        entry = self._store[key]
        age = (datetime.now(timezone.utc) - entry["cached_at"]).total_seconds()
        if age > self._ttl:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, data: dict, value: dict):
        key = self._make_key(data)
        self._store[key] = {
            "value": value,
            "cached_at": datetime.now(timezone.utc)
        }

    def clear(self):
        self._store.clear()

    def stats(self):
        return {
            "cached_entries": len(self._store),
            "ttl_seconds": self._ttl
        }

# Global cache instance — lives for the lifetime of the app
llm_cache = SimpleCache(ttl_seconds=300)