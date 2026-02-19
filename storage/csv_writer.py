import pandas as pd


def save_to_csv(data, filepath):
    df = pd.DataFrame(data)

    # Ensure column order
    columns = [
        "Name",
        "Phone",
        "Address",
        "Website",
        "Email",
        "City",
        "Category",
        "Source"
    ]

    df = df.reindex(columns=columns)

    df.to_csv(filepath, index=False)
    return filepath
