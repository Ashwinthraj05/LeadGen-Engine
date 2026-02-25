import pandas as pd


def save_to_csv(data, filepath):
    """
    Save leads safely to CSV

    ✔ preserves all fields
    ✔ converts lists → readable text
    ✔ keeps engine scoring fields
    """

    if not data:
        return filepath

    cleaned_rows = []

    for row in data:
        cleaned = dict(row)

        # convert list fields to readable strings
        if isinstance(cleaned.get("UndeliverableEmails"), list):
            cleaned["UndeliverableEmails"] = ", ".join(
                cleaned["UndeliverableEmails"])

        if isinstance(cleaned.get("Phone"), list):
            cleaned["Phone"] = ", ".join(cleaned["Phone"])

        if isinstance(cleaned.get("LinkedIn"), list):
            cleaned["LinkedIn"] = ", ".join(cleaned["LinkedIn"])

        cleaned_rows.append(cleaned)

    df = pd.DataFrame(cleaned_rows)

    # ⭐ preferred column order
    preferred_order = [
        "Name",
        "Company",
        "Website",
        "Email",
        "UndeliverableEmails",
        "Phone",
        "LinkedIn",
        "CompanySize",
        "EmailScore",
        "LeadScore",
        "About",
        "City",
        "Category",
        "Source",
    ]

    # keep available columns only
    columns = [col for col in preferred_order if col in df.columns]

    df = df.reindex(columns=columns)

    df.to_csv(filepath, index=False, encoding="utf-8-sig")

    return filepath
