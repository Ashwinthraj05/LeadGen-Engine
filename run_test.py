# test_run.py
from core.orchestrator import run_global_scraper

leads, raw = run_global_scraper(
    cities=["Chennai"],
    categories=["digital marketing agency"]
)

print(f"\n{'='*40}")
print(f"Total leads    : {len(leads)}")
print(f"With email     : {sum(1 for l in leads if l.get('Email'))}")
print(f"With phone     : {sum(1 for l in leads if l.get('Phone'))}")
print(f"With website   : {sum(1 for l in leads if l.get('Website'))}")
print(f"{'='*40}")

# show first 5 leads
for l in leads[:5]:
    print(f"\n  Name    : {l.get('Name')}")
    print(f"  Website : {l.get('Website')}")
    print(f"  Email   : {l.get('Email')}")
    print(f"  Phone   : {l.get('Phone')}")
