import json
import time
from playwright.sync_api import sync_playwright

def extract_text_with_context(full_text, keyword, char_range=500):
    """Extracts the keyword-containing paragraph with 500 characters before and after."""
    index = full_text.lower().find(keyword.lower())
    if index == -1:
        return None  # Return None if keyword not found
    
    # Get text slice with 500 characters before & after the keyword
    start = max(0, index - char_range)
    end = min(len(full_text), index + char_range)
    return full_text[start:end]

def search_gallica():
    extracted_data = []  # Store extracted documents

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Step 1: Open Gallica search
        print("Opening Gallica...")
        page.goto("https://rapportgallica.bnf.fr/recherche?query=(gallica+all+%22panafricain%22)&lang=en&suggest=0&aig=2&mb=5&collapsing=true")
        page.wait_for_load_state("networkidle")

        # Step 2: Scroll down to load more results
        print("Scrolling through results...")
        scroll_container = page.locator("div.overflow-auto.h-full.z-2")
        if not scroll_container.count():
            print("⚠️ Scrollable container not found. Exiting...")
            return
        
        scroll_container.hover()
        time.sleep(1)

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

        # Step 3: Click "See extracts in search reports"
        print("Locating result links...")
        page.wait_for_selector("a.focus\\:outline-none", state="visible", timeout=5000)
        buttons = page.locator("a.focus\\:outline-none").all()

        print(f"Total result pages found: {len(buttons)}")

        for index, button in enumerate(buttons):
            print(f"Clicking button {index + 1}...")
            button.scroll_into_view_if_needed()
            button.wait_for(state="visible", timeout=5000)

            with page.expect_popup() as popup_info:
                button.click(force=True)
                new_page = popup_info.value
                new_page.wait_for_load_state("networkidle")

                # Extract metadata
                title = new_page.locator("h1").inner_text().strip()
                author = new_page.locator(".author").inner_text().strip() if new_page.locator(".author").count() else "Unknown"
                date = new_page.locator(".date").inner_text().strip() if new_page.locator(".date").count() else "Unknown"
                publication = new_page.locator(".publication").inner_text().strip() if new_page.locator(".publication").count() else "Unknown"

                # Get OCR text mode URL
                ocr_text_url = new_page.url.replace("f1.image", "texteBrut")  # Modify URL to direct to OCR text

                # Click OCR text mode tab
                print(f"Extracting text from: {title}")
                ocr_button = new_page.locator("#ocrTextPanel button")
                if ocr_button.count():
                    ocr_button.click()
                    time.sleep(2)

                # Scroll inside OCR text panel
                ocr_scroll = new_page.locator("#mCSB_13_container")
                if ocr_scroll.count():
                    ocr_scroll.hover()
                    for _ in range(5):
                        new_page.evaluate("(element) => element.scrollBy(0, 500)", ocr_scroll)
                        time.sleep(1)

                # Extract OCR text
                full_text = new_page.locator("#mCSB_13_container").inner_text()
                extracted_snippet = extract_text_with_context(full_text, "panafricain")

                if extracted_snippet:
                    extracted_data.append({
                        "doc_id": index + 1,
                        "title": title,
                        "author": author,
                        "date": date,
                        "publication": publication,
                        "ocr_text_url": ocr_text_url,  # Add OCR text mode link
                        "text": extracted_snippet,
                        "keywords": ["Pan-Africanism", "Bandung Conference"]
                    })

                # Close the tab
                new_page.close()
                time.sleep(2)

        # Step 4: Save extracted data to JSON
        with open("pan_africanism_data.json", "w", encoding="utf-8") as json_file:
            json.dump(extracted_data, json_file, indent=4, ensure_ascii=False)

        print("✅ Data saved to pan_africanism_data.json")
        browser.close()

# Run the function
search_gallica()
