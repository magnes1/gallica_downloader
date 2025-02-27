import json
from gallica_scraper import GallicaScraper

# Define search term
SEARCH_TERM = "panafricain"

# Run scraper
scraper = GallicaScraper(SEARCH_TERM)
results = scraper.search_gallica()

# Save results to JSON file
if results:
    output_file = "gallica_extracted_text.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"✅ Saved extracted text to {output_file}")
else:
    print("⚠️ No results found.")
