from bs4 import BeautifulSoup
from utils.helpers import safe_request


def scrape_indiamart(city, keyword, pages=1):
    results = []

    for page in range(1, pages+1):
        url = f"https://dir.indiamart.com/search.mp?ss={keyword}+{city}&page={page}"

        res = safe_request(url)
        if not res:
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        for card in soup.select(".r-cl"):
            name = card.get_text(strip=True)
            results.append({
                "Name": name,
                "Website": "",
                "Phone": ""
            })

    return results
