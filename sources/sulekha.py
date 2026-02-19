from bs4 import BeautifulSoup
import requests
import time
from utils.helpers import create_business


def scrape_sulekha(city, category, pages=2):
    results = []
    category_slug = category.replace(" ", "-")

    for page in range(1, pages + 1):
        url = f"https://www.sulekha.com/{category_slug}-services/{city}?page={page}"
        print(f"📒 {url}")

        try:
            res = requests.get(url, timeout=15)
        except:
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select(".business-listing")

        for card in cards:
            name_tag = card.select_one("h3")

            name = name_tag.text.strip() if name_tag else ""

            if name:
                results.append(
                    create_business(
                        name=name,
                        phone="",
                        address="",
                        website="",
                        email="",
                        city=city,
                        category=category,
                        source="Sulekha"
                    )
                )

        time.sleep(1)

    return results
