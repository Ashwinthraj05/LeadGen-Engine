from urllib.parse import urlparse

# ----------------------------
# BLOCKED DOMAINS (directories & aggregators)
# ----------------------------

BLOCKED_DOMAINS = {
    "justdial.com",
    "sulekha.com",
    "indiamart.com",
    "yellowpages.com",
    "yelp.com",
    "clutch.co",
    "goodfirms.co",
    "trustpilot.com",
    "facebook.com",
    "linkedin.com",
    "instagram.com",
    "twitter.com",
    "youtube.com"
}

# keywords that indicate list pages / blog results
BLOCKED_NAME_KEYWORDS = {
    "top", "best", "list", "directory", "agencies",
    "companies", "services", "firms", "near me",
    "in chennai", "in bangalore", "in mumbai",
    "reviews", "ratings"
}

# ----------------------------
# NORMALIZE WEBSITE
# ----------------------------


def normalize_website(url: str) -> str:
    if not url:
        return ""

    url = url.strip().lower()

    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "").strip()

    return domain

# ----------------------------
# FILTER JUNK BUSINESSES
# ----------------------------


def is_real_business(business: dict) -> bool:
    name = (business.get("Name") or "").lower()
    website = normalize_website(business.get("Website", ""))

    # ❌ skip if no website
    if not website:
        return False

    # ❌ skip directory & aggregator domains
    if website in BLOCKED_DOMAINS:
        return False

    # ❌ skip list-style titles
    for word in BLOCKED_NAME_KEYWORDS:
        if word in name:
            return False

    return True

# ----------------------------
# EMAIL PRIORITY
# ----------------------------


def score_email(email, domain):
    email = email.lower()

    if domain and domain in email:
        return 100

    if email.startswith(("info@", "contact@", "sales@", "hello@")):
        return 90

    if email.startswith(("support@", "admin@", "office@")):
        return 75

    return 50


def choose_best_email(emails, domain):
    if not emails:
        return ""

    return sorted(
        emails,
        key=lambda e: score_email(e, domain),
        reverse=True
    )[0]

# ----------------------------
# MERGE RECORDS
# ----------------------------


def merge_records(existing, new):
    # merge emails
    existing_emails = set(existing.get("Email", []))
    new_emails = set(new.get("Email", []))
    all_emails = list(existing_emails | new_emails)

    domain = existing.get("Website", "")

    existing["Email"] = all_emails
    existing["BestEmail"] = choose_best_email(all_emails, domain)

    # merge phones
    existing_phones = set(existing.get("Phone", []))
    new_phones = set(new.get("Phone", []))
    existing["Phone"] = list(existing_phones | new_phones)

    # merge linkedin
    if not existing.get("LinkedIn"):
        existing["LinkedIn"] = new.get("LinkedIn", "")

    # merge company description
    if not existing.get("About"):
        existing["About"] = new.get("About", "")

    return existing

# ----------------------------
# DEDUPE BUSINESSES
# ----------------------------


def dedupe_businesses(businesses):
    """
    ✔ Removes duplicates
    ✔ Removes directories & list pages
    ✔ Keeps real companies only
    """

    unique = {}

    for b in businesses:

        if not is_real_business(b):
            continue

        name = (b.get("Name") or "").strip().lower()
        website = normalize_website(b.get("Website", ""))

        key = website if website else name
        if not key:
            continue

        b["Website"] = website

        if key in unique:
            unique[key] = merge_records(unique[key], b)
        else:
            unique[key] = b

    return list(unique.values())
