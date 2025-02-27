from playwright.sync_api import sync_playwright
import time

class GallicaScraper:
    """Handles searching, scrolling, and opening OCR pages in Gallica."""
    
    def __init__(self, search_term):
        self.search_term = search_term
        self.results = []  # Stores extracted data

    def search_gallica(self):
        """Automates Gallica search, scrolling, and OCR extraction."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            print("Opening Gallica...")
            page.goto(f"https://rapportgallica.bnf.fr/recherche?query=(gallica+all+%22{self.search_term}%22)&lang=en")
            page.wait_for_load_state("networkidle")

            print("✅ Page loaded. Searching for scrollable container...")
            scroll_container = page.locator("div.overflow-auto.h-full.z-2")

            if not scroll_container.count():
                print("⚠️ Scrollable container not found. Exiting...")
                return
            
            print("✅ Hovering over container...")
            scroll_container.hover()
            time.sleep(1)

            print("✅ Scrolling...")
            scroll_handle = scroll_container.element_handle()

            if not scroll_handle:
                print("⚠️ Could not retrieve scroll handle. Exiting...")
                return

            previous_height = 0
            while True:
                page.evaluate("(element) => element.scrollBy(0, 500)", scroll_handle)
                time.sleep(2)
                new_height = page.evaluate("(element) => element.scrollHeight", scroll_handle)

                if new_height == previous_height:
                    break

                previous_height = new_height

            print("✅ Scrolling complete.")

            # Locate and click all "See extracts in search reports" buttons
            page.wait_for_selector("a.focus\\:outline-none", timeout=5000)
            buttons = page.locator("a.focus\\:outline-none").all()
            print(f"✅ Found {len(buttons)} buttons to click.")

            from text_extractor import extract_text_data  # Import text processing module

            for index, button in enumerate(buttons):
                print(f"🔍 Clicking button {index + 1}/{len(buttons)}...")
                button.scroll_into_view_if_needed()
                button.wait_for(state="visible", timeout=5000)

                with page.expect_popup() as popup_info:
                    button.click(force=True)

                new_page = popup_info.value  
                new_page.wait_for_load_state("networkidle")

                print(f"✅ Opened Page {index + 1}: {new_page.title()}")

                extracted_data = extract_text_data(new_page, self.search_term)

                if extracted_data:
                    self.results.append(extracted_data)
                
                new_page.close()
                time.sleep(2)

            # Close browser
            browser.close()
            print("✅ Finished scraping.")
            return self.results
