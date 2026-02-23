from core.orchestrator import run_global_scraper

if __name__ == "__main__":
    leads = run_global_scraper(
        cities=["Chennai"],
        categories=["digital marketing agency"]
    )

    print("\n\n=== RESULTS ===\n")
    for lead in leads[:5]:
        print(lead)
