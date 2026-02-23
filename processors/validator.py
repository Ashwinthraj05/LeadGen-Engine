import re
from urllib.parse import urlparse

# allow uppercase + longer TLDs
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

# ----------------------------------------
# FREE / LOW VALUE EMAIL PROVIDERS
# ----------------------------------------
FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "live.com", "icloud.com", "protonmail.com", "aol.com"
}

# ----------------------------------------
# ROLE BASED EMAILS (GOOD)
# ----------------------------------------
ROLE_BASED_PREFIXES = {
    "info", "contact", "sales", "hello", "support",
    "admin", "office", "enquiry", "marketing"
}

# ----------------------------------------
# DECISION MAKER PREFIXES (BEST)
# ----------------------------------------
DECISION_PREFIXES = {
    "ceo", "founder", "director", "owner",
    "cofounder", "partner", "president"
}

# ----------------------------------------
# DEFINITELY JUNK
# ----------------------------------------
BLOCKED_KEYWORDS = {
    "example", "test", "noreply", "no-reply",
    "do-not-reply", "donotreply",
    "sentry", "wixpress",
    ".png", ".jpg", ".jpeg", ".svg", ".webp",
    "@2x", "@3x"
}

# =========================
# CLEAN EMAIL
# =========================


def clean_email(email: str) -> str:
    if not email:
        return ""

    email = email.strip().lower()

    # remove HTML junk
    email = email.replace("u003e", "")
    email = email.replace("<", "").replace(">", "")
    email = email.replace('"', "").replace("'", "")

    # remove trailing punctuation
    email = email.rstrip(".,;:()[]")

    return email


# =========================
# BASIC VALIDATION
# =========================

def is_valid_email(email: str) -> bool:
    if not email:
        return False

    email = clean_email(email)

    if not re.match(EMAIL_REGEX, email):
        return False

    # block obvious junk
    for word in BLOCKED_KEYWORDS:
        if word in email:
            return False

    return True


# =========================
# DOMAIN NORMALIZATION
# =========================

def normalize_domain(domain: str) -> str:
    if not domain:
        return ""

    parsed = urlparse(domain)
    netloc = parsed.netloc if parsed.netloc else parsed.path

    netloc = netloc.lower()
    netloc = netloc.replace("www.", "")
    netloc = netloc.split("/")[0]

    return netloc


# =========================
# DOMAIN MATCH CHECK
# =========================

def domain_matches_website(email: str, website: str) -> bool:
    if not email or not website:
        return False

    try:
        email_domain = email.split("@")[1].lower()
        website_domain = normalize_domain(website)

        if email_domain == website_domain:
            return True

        # allow subdomains
        if email_domain.endswith("." + website_domain):
            return True

        if website_domain.endswith("." + email_domain):
            return True

        return False

    except Exception:
        return False


# =========================
# EMAIL QUALITY SCORE
# =========================

def score_email(email: str, website: str = "") -> int:
    """
    Higher score = better email
    """

    if not is_valid_email(email):
        return 0

    email = clean_email(email)
    prefix, domain = email.split("@")

    score = 50

    # ⭐ company domain match (MOST IMPORTANT)
    if website and domain_matches_website(email, website):
        score += 40

    # ⭐ decision maker emails
    if prefix in DECISION_PREFIXES:
        score += 25

    # ⭐ role inbox emails
    elif prefix in ROLE_BASED_PREFIXES:
        score += 10

    # personal inbox → lower value
    if domain in FREE_PROVIDERS:
        score -= 25

    # real-name pattern (john.doe)
    if "." in prefix:
        score += 5

    return max(0, min(score, 100))


# =========================
# CHOOSE BEST EMAIL
# =========================

def choose_best_email(emails, website=None):
    if not emails:
        return ""

    ranked = sorted(
        set(emails),
        key=lambda e: score_email(e, website),
        reverse=True
    )

    return ranked[0]


# =========================
# FILTER & PRIORITIZE EMAILS
# =========================

def filter_emails(emails, website=None, limit=3):
    """
    Returns BEST deliverable emails

    Priority:
    1. Company domain emails
    2. Decision-maker emails
    3. Role inbox emails
    4. Personal emails (last)
    """

    if not emails:
        return []

    cleaned = set()

    for email in emails:
        email = clean_email(email)
        if is_valid_email(email):
            cleaned.add(email)

    if not cleaned:
        return []

    ranked = sorted(
        cleaned,
        key=lambda e: score_email(e, website),
        reverse=True
    )

    return ranked[:limit]
