import re
from urllib.parse import urlparse

EMAIL_REGEX = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"


def clean_email(email: str) -> str:
    if not email:
        return ""

    email = email.strip().lower()
    email = email.replace("u003e", "")
    email = email.replace(">", "")
    email = email.replace("<", "")
    email = email.rstrip(".,;:")

    return email


def is_valid_email(email: str) -> bool:
    if not email:
        return False

    email = clean_email(email)

    if not re.match(EMAIL_REGEX, email):
        return False

    blocked_keywords = [
        "example",
        "test",
        "noreply",
        "no-reply",
        "justdial",
        "google",
        "sentry",
        "wixpress",
        "@2x",
        "@3x",
        ".png",
        ".jpg",
        ".jpeg",
        ".svg",
        ".webp",
    ]

    for word in blocked_keywords:
        if word in email:
            return False

    invalid_tlds = ["png", "jpg", "jpeg", "svg", "webp"]
    tld = email.split(".")[-1]

    if tld in invalid_tlds:
        return False

    return True


# 🔥 FIXED DOMAIN MATCHING
def normalize_domain(domain: str) -> str:
    if not domain:
        return ""

    parsed = urlparse(domain)

    netloc = parsed.netloc if parsed.netloc else parsed.path

    netloc = netloc.lower()
    netloc = netloc.replace("www.", "")
    netloc = netloc.split("/")[0]

    return netloc


def domain_matches_website(email: str, website: str) -> bool:
    if not email or not website:
        return False

    try:
        email_domain = email.split("@")[1].lower()
        website_domain = normalize_domain(website)

        # Allow subdomains
        if email_domain == website_domain:
            return True

        if website_domain.endswith(email_domain):
            return True

        if email_domain.endswith(website_domain):
            return True

        return False

    except:
        return False
