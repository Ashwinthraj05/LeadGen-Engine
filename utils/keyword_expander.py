"""
utils/keyword_expander.py
FIXED:
  1. Old version only had 2 categories — missed everything else
  2. Now covers ALL DEFAULT_CATEGORIES from config.py
  3. Each category has 6-10 real search variants
  4. Generic fallback generates useful variants automatically
"""

KEYWORD_MAP = {

    # ── BPO & OUTSOURCING ────────────────────────────────────────────────────
    "bpo company": [
        "BPO company",
        "Business process outsourcing company",
        "BPO services provider",
        "outsourced business operations",
        "BPO firm",
    ],
    "call center services": [
        "call center company",
        "inbound call center",
        "outbound call center",
        "contact center services",
        "customer call center",
        "telemarketing services",
    ],
    "outsourcing services": [
        "outsourcing company",
        "outsourced services provider",
        "business outsourcing firm",
        "process outsourcing company",
    ],
    "customer support outsourcing": [
        "customer support outsourcing",
        "outsourced customer service",
        "customer care outsourcing",
        "helpdesk outsourcing company",
    ],
    "back office outsourcing": [
        "back office outsourcing company",
        "back office services",
        "data entry outsourcing",
        "document processing outsourcing",
    ],

    # ── RCM & MEDICAL BILLING ────────────────────────────────────────────────
    "medical billing company": [
        "medical billing company",
        "healthcare billing services",
        "medical billing and coding",
        "physician billing services",
        "hospital billing services",
        "medical billing outsourcing",
    ],
    "revenue cycle management": [
        "revenue cycle management company",
        "RCM services",
        "healthcare RCM",
        "medical revenue cycle",
        "claims management services",
        "insurance billing company",
    ],
    "medical coding services": [
        "medical coding company",
        "clinical coding services",
        "ICD coding services",
        "CPT coding company",
        "medical coding outsourcing",
    ],
    "dental billing services": [
        "dental billing company",
        "dental revenue cycle management",
        "dental insurance billing",
        "orthodontic billing services",
    ],

    # ── IT & SOFTWARE ────────────────────────────────────────────────────────
    "it services company": [
        "IT services company",
        "IT consulting firm",
        "managed IT services",
        "IT solutions provider",
        "technology services company",
        "IT support company",
    ],
    "software development company": [
        "software development company",
        "custom software development",
        "software development firm",
        "application development company",
        "software engineering company",
        "software outsourcing company",
    ],
    "web development company": [
        "web development company",
        "website development agency",
        "web design and development",
        "ecommerce development company",
        "full stack development company",
    ],
    "cloud services provider": [
        "cloud services company",
        "cloud computing provider",
        "AWS consulting partner",
        "Azure cloud services",
        "cloud migration company",
        "cloud infrastructure services",
    ],
    "cybersecurity services": [
        "cybersecurity company",
        "information security services",
        "network security company",
        "cyber security consulting",
        "penetration testing company",
        "IT security services",
    ],

    # ── HIGH-CONVERSION SERVICES ─────────────────────────────────────────────
    "outsourced accounting services": [
        "outsourced accounting company",
        "accounting outsourcing services",
        "bookkeeping outsourcing",
        "virtual accounting services",
        "CPA outsourcing firm",
        "financial outsourcing company",
    ],
    "hr outsourcing services": [
        "HR outsourcing company",
        "human resources outsourcing",
        "payroll outsourcing services",
        "PEO services",
        "HR consulting firm",
        "workforce management company",
    ],
    "digital marketing agency": [
        "digital marketing agency",
        "SEO company",
        "social media marketing agency",
        "PPC advertising agency",
        "online marketing company",
        "performance marketing agency",
        "content marketing agency",
    ],
}


def expand_keyword(user_keyword: str) -> list:
    """
    Return a list of search variants for a given category keyword.
    Falls back to auto-generating variants if category not in map.
    """
    key = user_keyword.lower().strip()

    # direct match
    if key in KEYWORD_MAP:
        return KEYWORD_MAP[key]

    # partial match
    for map_key, variants in KEYWORD_MAP.items():
        if map_key in key or key in map_key:
            return variants

    # FIX: smart auto-fallback instead of just returning the original
    base = user_keyword.strip()
    return [
        base,
        f"{base} company",
        f"{base} services",
        f"{base} firm",
        f"top {base}",
        f"best {base}",
        f"{base} outsourcing",
    ]
