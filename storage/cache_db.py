import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = "data/cache.db"
CACHE_EXPIRY_DAYS = 7  # auto expire after 7 days


def init_cache():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            query TEXT PRIMARY KEY,
            results TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_cache(query):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT results, created_at FROM search_cache WHERE query=?", (query,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    results, created_at = row
    created_at = datetime.fromisoformat(created_at)

    # expire old cache
    if datetime.now() - created_at > timedelta(days=CACHE_EXPIRY_DAYS):
        return None

    return json.loads(results)


def save_cache(query, results):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO search_cache VALUES (?, ?, ?)",
        (query, json.dumps(results), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
