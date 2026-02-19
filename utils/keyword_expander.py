KEYWORD_MAP = {
    "rcm companies": [
        "RCM companies",
        "Revenue Cycle Management",
        "Medical billing companies",
        "Healthcare billing services",
        "Medical coding companies",
        "Insurance claim processing companies"
    ],

    "digital marketing": [
        "Digital marketing agency",
        "SEO company",
        "Social media marketing agency",
        "PPC agency",
        "Online marketing services"
    ]
}


def expand_keyword(user_keyword):
    key = user_keyword.lower().strip()

    if key in KEYWORD_MAP:
        return KEYWORD_MAP[key]

    # Default fallback
    return [user_keyword]
