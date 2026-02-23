from urllib.parse import urlparse

# --------------------------------------------------
# EMAIL PROVIDER RULES
# --------------------------------------------------

FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "live.com", "icloud.com", "aol.com", "protonmail.com"
}

DISPOSABLE_PROVIDERS = {
    "mailinator.com", "tempmail.com", "10minutemail.com",
    "guerrillamail.com", "trashmail.com"
}

DECISION_PREFIXES = (
    "ceo@", "founder@", "director@", "owner@", "cofounder@",
    "president@", "partner@", "chairman@"
)

BUSINESS_PREFIXES = (
    "sales@", "info@", "contact@", "hello@", "support@", "admin@"
)

RISKY_PREFIXES = (
    "noreply@", "no-reply@", "donotreply@", "mailer@", "notification@"
)

# --------------------------------------------------
# DOMAIN NORMALIZATION
# --------------------------------------------------


def normalize_domain(website: str) -> str:
    if not website:
        return ""

    parsed = urlparse(website)
    netloc = parsed.netloc if parsed.netloc else parsed.path
    netloc = netloc.lower().replace("www.", "").strip()

    return netloc


# --------------------------------------------------
# EMAIL QUALITY SCORING
# --------------------------------------------------

def score_email(email: str, website: str = "") -> int:
    """
    Score email quality (0–100)

    Focus:
    ✔ deliverability
    ✔ decision-maker reach
    ✔ business legitimacy
    ✔ outreach success probability
    """

    if not email or "@" not in email:
        return 0

    email = email.lower().strip()
    domain = email.split("@")[-1]
    website_domain = normalize_domain(website)

    score = 40  # base score

    # -------------------------
    # DOMAIN MATCH (MOST IMPORTANT)
    # -------------------------

    if website_domain and (
        domain == website_domain
        or domain.endswith(website_domain)
        or website_domain.endswith(domain)
    ):
        score += 35
    else:
        score -= 10

    # -------------------------
    # FREE PROVIDER PENALTY
    # -------------------------

    if domain in FREE_PROVIDERS:
        score -= 25

    # -------------------------
    # DISPOSABLE EMAIL BLOCK
    # -------------------------

    if domain in DISPOSABLE_PROVIDERS:
        score -= 40

    # -------------------------
    # DECISION MAKER BONUS
    # -------------------------

    if email.startswith(DECISION_PREFIXES):
        score += 25

    # -------------------------
    # BUSINESS INBOX BONUS
    # -------------------------

    elif email.startswith(BUSINESS_PREFIXES):
        score += 10

    # -------------------------
    # RISKY EMAIL PENALTY
    # -------------------------

    if email.startswith(RISKY_PREFIXES):
        score -= 15

    # -------------------------
    # STRUCTURE QUALITY
    # -------------------------

    if len(email) > 40:
        score -= 5

    if ".." in email:
        score -= 10

    return max(0, min(score, 100))


# --------------------------------------------------
# ⭐ BEST EMAIL SELECTOR (IMPORTANT)
# --------------------------------------------------

def choose_best_email(emails, site):
    """
    Select highest quality email for outreach.
    Prioritizes:
    1️⃣ domain match emails
    2️⃣ decision maker emails
    3️⃣ business inboxes
    4️⃣ everything else
    """

    if not emails:
        return ""

    site_domain = normalize_domain(site)

    # remove duplicates
    emails = list(set(e.lower().strip() for e in emails if "@" in e))

    def priority(email):
        domain = email.split("@")[-1]

        score = 0

        # domain match (MOST IMPORTANT)
        if site_domain and site_domain in domain:
            score += 50

        # decision maker
        if email.startswith(DECISION_PREFIXES):
            score += 40

        # business inbox
        elif email.startswith(BUSINESS_PREFIXES):
            score += 25

        # avoid risky emails
        if email.startswith(RISKY_PREFIXES):
            score -= 20

        # avoid free providers
        if domain in FREE_PROVIDERS:
            score -= 15

        return score

    emails.sort(key=priority, reverse=True)
    return emails[0]
