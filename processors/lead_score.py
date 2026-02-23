# processors/lead_score.py

def score_lead(lead):
    """
    Calculates overall lead quality score (0–100)

    Focus:
    ✔ deliverable email quality
    ✔ decision-maker reach
    ✔ company value
    ✔ outreach readiness
    """

    score = 0

    # -------------------------
    # EMAIL QUALITY (MOST IMPORTANT)
    # -------------------------

    best_email = lead.get("BestEmail") or ""

    if best_email:
        score += 40

        if best_email.startswith(("ceo@", "founder@", "director@", "owner@")):
            score += 15  # decision maker bonus

        elif best_email.startswith(("sales@", "info@", "contact@")):
            score += 10  # business inbox bonus

    # fallback if only raw emails exist
    elif lead.get("Email"):
        score += 20

    # email deliverability score
    score += lead.get("EmailScore", 0)

    # -------------------------
    # LINKEDIN PRESENCE
    # -------------------------

    linkedin = lead.get("LinkedIn")

    if linkedin:
        score += 15

        if "company" in linkedin.lower():
            score += 5

    # -------------------------
    # COMPANY SIZE VALUE
    # -------------------------

    size = lead.get("CompanySize")

    if size == "Large":
        score += 20
    elif size == "Medium":
        score += 12
    elif size == "Small":
        score += 5

    # -------------------------
    # WEBSITE PRESENCE
    # -------------------------

    if lead.get("Website"):
        score += 5

    # -------------------------
    # ABOUT / DESCRIPTION
    # -------------------------

    if lead.get("About"):
        score += 5

    # -------------------------
    # PHONE (optional trust signal)
    # -------------------------

    if lead.get("Phone"):
        score += 3

    return min(score, 100)
