"""
processors/lead_score.py
FIXED:
  1. Handles missing/None fields without crashing
  2. EmailScore field is optional (was causing KeyError)
  3. Checks both "Email" and "BestEmail" correctly
  4. CompanySize comparison is case-insensitive
"""


def score_lead(lead: dict) -> int:
    """
    Score overall lead quality 0-100.
    Higher = better outreach candidate.
    """

    if not lead or not isinstance(lead, dict):
        return 0

    score = 0

    # ── Email quality (most important) ────────────────────────────────────
    best_email = (lead.get("BestEmail") or lead.get("Email") or "").lower()

    if best_email and "@" in best_email:
        score += 35

        if any(best_email.startswith(p) for p in
               ("ceo@", "founder@", "director@", "owner@",
                "cofounder@", "president@", "partner@")):
            score += 15   # decision maker

        elif any(best_email.startswith(p) for p in
                 ("sales@", "info@", "contact@", "hello@", "enquiry@")):
            score += 10   # business inbox

    # add email score if available
    email_score = lead.get("EmailScore", 0)
    try:
        score += int(email_score) // 5   # normalize: max +20
    except (ValueError, TypeError):
        pass

    # ── LinkedIn ──────────────────────────────────────────────────────────
    linkedin = lead.get("LinkedIn") or ""
    if linkedin:
        score += 10
        if "company" in linkedin.lower():
            score += 5

    # ── Company size ──────────────────────────────────────────────────────
    size = (lead.get("CompanySize") or "").strip().lower()
    if size == "large":
        score += 15
    elif size == "medium":
        score += 10
    elif size == "small":
        score += 5

    # ── Website ───────────────────────────────────────────────────────────
    if lead.get("Website"):
        score += 5

    # ── About / description ───────────────────────────────────────────────
    if lead.get("About"):
        score += 5

    # ── Phone ─────────────────────────────────────────────────────────────
    if lead.get("Phone"):
        score += 5

    # ── Address ───────────────────────────────────────────────────────────
    if lead.get("Address"):
        score += 3

    return min(score, 100)
