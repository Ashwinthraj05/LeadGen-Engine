from sources.justdial import scrape_justdial

data = scrape_justdial("Bangalore", "software company", 1)

print("RESULTS:", len(data))
print(data[:3])
