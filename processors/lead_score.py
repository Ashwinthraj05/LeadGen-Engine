# processors/lead_score.py

def score_lead(lead):
    """
    Calculates overall lead quality score (0–100)
    """

    score = 0

    # email presence
    if lead.get("Email"):
        score += 30

    # linkedin presence
    if lead.get("LinkedIn"):
        score += 20

    # company size scoring
    if lead.get("CompanySize") == "Large":
        score += 25
    elif lead.get("CompanySize") == "Medium":
        score += 15
    elif lead.get("CompanySize"):
        score += 5

    # email quality score bonus
    score += lead.get("EmailScore", 0)

    return min(score, 100)
