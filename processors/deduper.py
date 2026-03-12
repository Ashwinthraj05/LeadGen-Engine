"""
processors/deduper.py
FIXED:
  1. BIG BUG: old code dropped ALL leads with no website — now kept
  2. Dedup key uses name when no website (not discarded)
  3. BLOCKED_NAME_KEYWORDS was killing valid leads like "IT services companies"
  4. merge_records handles string emails (not just lists)
  5. Returns ALL unique businesses, not just ones with websites
"""

from urllib.parse import urlparse

# ── Strict directory domains to filter ───────────────────────────────────────
BLOCKED_DOMAINS = {
    "justdial.com", "sulekha.com", "indiamart.com",
    "yellowpages.com", "yelp.com", "clutch.co",
    "goodfirms.co", "trustpilot.com", "facebook.com",
    "linkedin.com", "instagram.com", "twitter.com", "youtube.com",
    "glassdoor.com", "ambitionbox.com", "reddit.com",
    "quora.com", "wikipedia.org",
}

# FIX: removed overly broad keywords that killed valid business names
# Old list had "companies", "services", "agencies" which appear in REAL names
BLOCKED_NAME_KEYWORDS = {
    "top 10", "top 20", "top 50", "best list",
    "directory of", "list of companies",
    "near me results", "reviews and ratings",
}


def normalize_website(url: str) -> str:
    if not url:
        return ""
    url = url.strip().lower()
    if not url.startswith("http"):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "").strip()
        return domain
    except Exception:
        return ""


def is_real_business(business: dict) -> bool:
    name = (business.get("Name") or "").strip().lower()
    website = normalize_website(business.get("Website", ""))

    # must have a name
    if not name or len(name) < 2:
        return False

    # FIX: no longer reject leads with no website — they still have name/phone
    # skip only actual directory domains
    if website and website in BLOCKED_DOMAINS:
        return False

    # skip only clearly spammy list-page titles
    for phrase in BLOCKED_NAME_KEYWORDS:
        if phrase in name:
            return False

    return True


def _to_list(val) -> list:
    """Normalize email field — could be str, list, or empty."""
    if not val:
        return []
    if isinstance(val, list):
        return [e for e in val if e]
    if isinstance(val, str) and val:
        return [val]
    return []


def score_email(email: str, domain: str) -> int:
    email = email.lower()
    domain = (domain or "").replace("www.", "")

    if domain and domain in email:
        return 100
    if email.startswith(("info@", "contact@", "sales@", "hello@")):
        return 90
    if email.startswith(("support@", "admin@", "office@", "enquiry@")):
        return 75
    return 50


def choose_best_email(emails: list, domain: str) -> str:
    if not emails:
        return ""
    return sorted(emails, key=lambda e: score_email(e, domain), reverse=True)[0]


def merge_records(existing: dict, new: dict) -> dict:
    """Merge two records for the same business, keeping best data."""

    domain = existing.get("Website", "")

    # merge emails
    all_emails = list(set(
        _to_list(existing.get("Email")) + _to_list(new.get("Email"))
    ))
    existing["Email"] = choose_best_email(all_emails, domain)
    existing["AllEmails"] = all_emails

    # merge phones
    existing_phones = set(_to_list(existing.get("Phone")))
    new_phones = set(_to_list(new.get("Phone")))
    all_phones = list(existing_phones | new_phones)
    existing["Phone"] = ", ".join(all_phones[:3]) if all_phones else ""

    # fill missing fields from new record
    for field in ("LinkedIn", "About", "Address", "Website", "Category"):
        if not existing.get(field) and new.get(field):
            existing[field] = new[field]

    return existing


def dedupe_businesses(businesses: list) -> list:
    """
    Remove duplicates and filter junk, but KEEP leads even without websites.
    Dedup key = website domain (if available) else business name.
    """

    unique: dict = {}

    for b in businesses:

        if not is_real_business(b):
            continue

        name = (b.get("Name") or "").strip().lower()
        website = normalize_website(b.get("Website", ""))

        # FIX: use website as key if available, else name
        key = website if website else name
        if not key:
            continue

        # normalize website field
        b["Website"] = website

        if key in unique:
            unique[key] = merge_records(unique[key], b)
        else:
            unique[key] = b

    return list(unique.values())
