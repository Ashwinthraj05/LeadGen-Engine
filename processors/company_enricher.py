import requests
from bs4 import BeautifulSoup


def extract_company_details(url):
    data = {
        "linkedin": "",
        "about": ""
    }

    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all("a", href=True):
            if "linkedin.com/company" in a["href"]:
                data["linkedin"] = a["href"]

        about_section = soup.find("p")
        if about_section:
            data["about"] = about_section.get_text(strip=True)[:200]

    except:
        pass

    return data
