# processors/email_score.py

FREE_PROVIDERS = [
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com"
]


def score_email(email, website):
    """
    Scores email quality from 0–100
    """

    if not email:
        return 0

    score = 50  # base score

    domain = email.split("@")[-1]

    # business domain bonus
    if website and domain in website:
        score += 30

    # free email penalty
    if domain in FREE_PROVIDERS:
        score -= 20

    # role-based bonus
    if any(prefix in email for prefix in [
        "info@", "sales@", "contact@", "support@", "admin@"
    ]):
        score += 10

    return max(0, min(score, 100))
