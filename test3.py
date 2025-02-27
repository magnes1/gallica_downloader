from playwright.sync_api import sync_playwright
import time

def search_gallica():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Change to True for headless mode
        page = browser.new_page()

        # Open Gallica Search
        print("Opening Gallica...")
        page.goto("https://rapportgallica.bnf.fr/recherche?query=(gallica+all+%22panafricain%22)&lang=en&suggest=0&aig=2&mb=5&collapsing=true")
        page.wait_for_load_state("networkidle")

        print("✅ Page loaded. Searching for scrollable container...")

        # Locate the scrollable container
        scroll_container = page.locator("div.overflow-auto.h-full.z-2")

        if not scroll_container.count():
            print("⚠️ Scrollable container not found. Exiting...")
            return

        print("✅ Scrollable container found. Hovering over it...")
        scroll_container.hover()
        time.sleep(1)  # Ensure hover takes effect

        print("✅ Hovered over container. Now scrolling...")

        # Get the JavaScript handle for the scroll container
        scroll_handle = scroll_container.element_handle()
        
        if not scroll_handle:
            print("⚠️ Could not retrieve scroll handle. Exiting...")
            return

        previous_height = 0
        while True:
            # Scroll inside the correct container
            page.evaluate("(element) => element.scrollBy(0, 500)", scroll_handle)
            time.sleep(2)  # Wait for content to load

            # Check new height inside the container
            new_height = page.evaluate("(element) => element.scrollHeight", scroll_handle)
            print(f"Scrolled to: {new_height}px")

            if new_height == previous_height:
                break  # Stop scrolling if no new content loads

            previous_height = new_height

        print("✅ Scrolling complete.")

        # Click on search result buttons to open OCR text pages
        print("✅ Clicking search results...")
        buttons = page.locator("a.focus\\:outline-none").all()
        print(f"🛠 Found {len(buttons)} buttons.")

        for index, button in enumerate(buttons):
            print(f"🔍 Clicking result {index + 1}...")
            button.scroll_into_view_if_needed()
            button.wait_for(state="visible", timeout=5000)

            with page.expect_popup() as popup_info:
                button.hover()
                page.wait_for_timeout(500)
                button.click(force=True)

                new_page = popup_info.value
                new_page.wait_for_load_state("networkidle")

                # Extract OCR Text from the page
                extract_ocr_text(new_page)

                new_page.close()
                time.sleep(2)

        # Close browser
        browser.close()

def extract_ocr_text(page):
    """Extracts OCR text: Paragraph with keyword, the one before, and the one after."""
    page.wait_for_selector("div#mCSB_13_container", timeout=5000)
    ocr_container = page.locator("div#mCSB_13_container")

    if not ocr_container.count():
        print("⚠️ OCR container not found.")
        return

    ocr_text = ocr_container.inner_text()
    paragraphs = ocr_text.split("\n")

    keyword = "panafricain"
    for i, para in enumerate(paragraphs):
        if keyword in para.lower():
            before = paragraphs[i - 1] if i > 0 else "N/A"
            after = paragraphs[i + 1] if i < len(paragraphs) - 1 else "N/A"

            print("\n📜 **Extracted OCR Snippet:**")
            print(f"🔹 **Title:** {page.title()}")
            print(f"🔹 **Previous Paragraph:** {before}")
            print(f"🔹 **Matching Paragraph:** {para}")
            print(f"🔹 **Next Paragraph:** {after}")
            break

# Run the function
search_gallica()
