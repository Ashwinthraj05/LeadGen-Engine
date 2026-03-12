"""
processors/email_score.py
FIXED:
  1. Handles None / empty inputs without crashing
  2. choose_best_email accepts both list and single string
  3. Scoring logic unchanged but made crash-proof
"""

from urllib.parse import urlparse

FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "live.com", "icloud.com", "aol.com", "protonmail.com",
    "yahoo.co.in", "rediffmail.com",
}

DISPOSABLE_PROVIDERS = {
    "mailinator.com", "tempmail.com", "10minutemail.com",
    "guerrillamail.com", "trashmail.com", "yopmail.com",
}

DECISION_PREFIXES = (
    "ceo@", "founder@", "director@", "owner@", "cofounder@",
    "president@", "partner@", "chairman@", "md@", "cto@", "coo@",
)

BUSINESS_PREFIXES = (
    "sales@", "info@", "contact@", "hello@", "support@",
    "admin@", "office@", "enquiry@", "marketing@", "hr@",
)

RISKY_PREFIXES = (
    "noreply@", "no-reply@", "donotreply@",
    "mailer@", "notification@", "bounce@",
)


def normalize_domain(website: str) -> str:
    if not website:
        return ""
    try:
        parsed = urlparse(website)
        netloc = parsed.netloc if parsed.netloc else parsed.path
        return netloc.lower().replace("www.", "").strip().split("/")[0]
    except Exception:
        return ""


def score_email(email: str, website: str = "") -> int:
    """Score email quality 0-100."""

    if not email or not isinstance(email, str) or "@" not in email:
        return 0

    email = email.lower().strip()
    domain = email.split("@")[-1]
    website_domain = normalize_domain(website)

    score = 40   # base

    # domain match
    if website_domain and (
        domain == website_domain
        or domain.endswith("." + website_domain)
        or website_domain.endswith("." + domain)
    ):
        score += 35
    else:
        score -= 10

    # provider penalties
    if domain in FREE_PROVIDERS:
        score -= 25
    if domain in DISPOSABLE_PROVIDERS:
        score -= 40

    # prefix bonuses / penalties
    if email.startswith(DECISION_PREFIXES):
        score += 25
    elif email.startswith(BUSINESS_PREFIXES):
        score += 10

    if email.startswith(RISKY_PREFIXES):
        score -= 15

    # structure checks
    if len(email) > 60:
        score -= 5
    if ".." in email:
        score -= 10

    return max(0, min(score, 100))


def choose_best_email(emails, site: str = "") -> str:
    """
    Select highest quality email for outreach.
    FIX: accepts list OR single string safely.
    """

    if not emails:
        return ""

    # normalize input
    if isinstance(emails, str):
        emails = [emails]

    site_domain = normalize_domain(site)

    # deduplicate and clean
    clean = list({
        e.lower().strip()
        for e in emails
        if e and isinstance(e, str) and "@" in e
    })

    if not clean:
        return ""

    if len(clean) == 1:
        return clean[0]

    def priority(email: str) -> int:
        try:
            domain = email.split("@")[-1]
            s = 0
            if site_domain and site_domain in domain:
                s += 50
            if email.startswith(DECISION_PREFIXES):
                s += 40
            elif email.startswith(BUSINESS_PREFIXES):
                s += 25
            if email.startswith(RISKY_PREFIXES):
                s -= 20
            if domain in FREE_PROVIDERS:
                s -= 15
            return s
        except Exception:
            return 0

    clean.sort(key=priority, reverse=True)
    return clean[0]
