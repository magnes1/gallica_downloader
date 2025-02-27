# Configuration settings for the Gallica Scraper

# Playwright settings
HEADLESS_MODE = False  # Set to True for headless mode
SCROLL_WAIT_TIME = 2  # Time (in seconds) to wait after scrolling

# Search settings
SEARCH_QUERY = "(gallica all 'panafricain')"
SEARCH_URL = f"https://rapportgallica.bnf.fr/recherche?query={SEARCH_QUERY}&lang=en&suggest=0&aig=2&mb=5&collapsing=true"

# Locator settings
SCROLLABLE_CONTAINER_SELECTOR = "div.overflow-auto.h-full.z-2"
BUTTON_SELECTOR = "a.focus\\:outline-none"  # Button to open OCR page
OCR_TAB_SELECTOR = "button:text('Mode texte (OCR)')"
TEXT_CONTAINER_SELECTOR = "div.ocr-text-container"

# Output settings
SAVE_TEXT_PATH = "extracted_texts/"


