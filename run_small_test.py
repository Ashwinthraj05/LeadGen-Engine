from core.orchestrator import run_global_scraper

if __name__ == "__main__":

    print("\n🚀 RUNNING SMALL TEST\n")

    # 🔹 Test city
    cities = ["Bangalore"]

    # 🔹 Test categories
    categories = [
        "digital marketing agency",
        "web design company",
        "seo services",
        "software training institute"
    ]

    output_file = run_global_scraper(cities, categories)

    print("\n✅ TEST COMPLETE")
    print("📁 Output file:", output_file)
