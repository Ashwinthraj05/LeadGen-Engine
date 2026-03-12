"""
SerpAPI Key Rotation Manager
Automatically rotates between multiple API keys when limits are reached.
Tracks usage per key, persists state across runs using a local JSON file.
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

USAGE_FILE = "serpapi_usage.json"

# ---------------------------------------------------------------------------
# Configuration – fill in your real keys here or set them as env vars:
#   SERPAPI_KEY_1, SERPAPI_KEY_2, SERPAPI_KEY_3
# ---------------------------------------------------------------------------
DEFAULT_KEYS = [
    os.getenv("SERPAPI_KEY_1", "YOUR_KEY_1_HERE"),
    os.getenv("SERPAPI_KEY_2", "YOUR_KEY_2_HERE"),
    os.getenv("SERPAPI_KEY_3", "YOUR_KEY_3_HERE"),
]

MONTHLY_LIMIT = 250          # searches allowed per key per month
RESET_DAY = 1             # day of month when SerpAPI resets usage


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _load_usage() -> dict:
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_usage(data: dict) -> None:
    try:
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.warning(f"Could not save usage file: {e}")


def _month_key() -> str:
    """Returns a string like '2026-03' representing the current billing month."""
    return datetime.now().strftime("%Y-%m")


# ---------------------------------------------------------------------------
# Core manager
# ---------------------------------------------------------------------------

class SerpAPIKeyManager:
    """
    Manages a pool of SerpAPI keys with automatic rotation.

    Usage
    -----
        mgr = SerpAPIKeyManager()
        key = mgr.get_key()          # raises RuntimeError if all keys exhausted
        mgr.record_use(key)          # call AFTER a successful search
        mgr.record_error(key, err)   # call when SerpAPI returns a limit error
    """

    def __init__(self, keys: list = None, monthly_limit: int = MONTHLY_LIMIT):
        from config import SERPAPI_KEYS
        self.keys = keys or [k for k in SERPAPI_KEYS if k]
        if not self.keys:
            raise ValueError(
                "No SerpAPI keys found. Set SERPAPI_KEYS=key1,key2,key3 in .env"
            )
        self.monthly_limit = monthly_limit
        self.usage = _load_usage()
        self._month = _month_key()
        self._ensure_month()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_key(self) -> str:
        """Return the next available key. Raises RuntimeError if all exhausted."""
        self._refresh_month()
        for key in self.keys:
            remaining = self._remaining(key)
            if remaining > 0:
                logger.debug(
                    f"Using key …{key[-6:]}, {remaining} searches left this month.")
                return key

        exhausted_info = ", ".join(
            f"…{k[-6:]} ({self._used(k)}/{self.monthly_limit})" for k in self.keys
        )
        raise RuntimeError(
            f"All SerpAPI keys exhausted for {self._month}. "
            f"Details: {exhausted_info}. "
            f"Keys reset on the {RESET_DAY}th of next month."
        )

    def record_use(self, key: str, count: int = 1) -> None:
        """Increment usage counter for *key* by *count*."""
        self._refresh_month()
        entry = self._entry(key)
        entry["used"] = entry.get("used", 0) + count
        _save_usage(self.usage)
        logger.info(
            f"Key …{key[-6:]}: {entry['used']}/{self.monthly_limit} used this month."
        )

    def record_error(self, key: str, error: Exception) -> Optional[str]:
        """
        Call when SerpAPI responds with a rate-limit / quota error.
        Marks the key as exhausted and returns the next available key,
        or None if all keys are done.
        """
        msg = str(error).lower()
        if any(word in msg for word in ("limit", "quota", "exceeded", "credits")):
            logger.warning(
                f"Key …{key[-6:]} hit its limit. Marking exhausted.")
            self._mark_exhausted(key)
            try:
                return self.get_key()
            except RuntimeError:
                return None
        return key   # error unrelated to quota – keep using same key

    def status(self) -> list[dict]:
        """Return usage status for all keys (useful for logging / dashboard)."""
        self._refresh_month()
        return [
            {
                "key_suffix": f"…{k[-6:]}",
                "used": self._used(k),
                "remaining": self._remaining(k),
                "limit": self.monthly_limit,
                "exhausted": self._remaining(k) == 0,
            }
            for k in self.keys
        ]

    def print_status(self) -> None:
        print(f"\n{'='*50}")
        print(f"  SerpAPI Key Status  –  {self._month}")
        print(f"{'='*50}")
        for s in self.status():
            bar = self._progress_bar(s["used"], s["limit"])
            flag = "🔴 EXHAUSTED" if s["exhausted"] else "🟢 OK"
            print(
                f"  {s['key_suffix']}  {bar}  {s['used']}/{s['limit']}  {flag}")
        print(f"{'='*50}\n")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_month(self):
        if self._month not in self.usage:
            self.usage[self._month] = {}
        for key in self.keys:
            if key not in self.usage[self._month]:
                self.usage[self._month][key] = {"used": 0}
        _save_usage(self.usage)

    def _refresh_month(self):
        current = _month_key()
        if current != self._month:
            logger.info(
                f"New billing month detected ({self._month} → {current}). Resetting usage.")
            self._month = current
            self._ensure_month()

    def _entry(self, key: str) -> dict:
        return self.usage[self._month].setdefault(key, {"used": 0})

    def _used(self, key: str) -> int:
        return self._entry(key).get("used", 0)

    def _remaining(self, key: str) -> int:
        return max(0, self.monthly_limit - self._used(key))

    def _mark_exhausted(self, key: str) -> None:
        self._entry(key)["used"] = self.monthly_limit
        _save_usage(self.usage)

    @staticmethod
    def _progress_bar(used: int, total: int, width: int = 20) -> str:
        filled = int(width * used / total) if total else 0
        return f"[{'█' * filled}{'░' * (width - filled)}]"


# ---------------------------------------------------------------------------
# Singleton – import and use `key_manager` anywhere in the project
# ---------------------------------------------------------------------------
key_manager = SerpAPIKeyManager()
