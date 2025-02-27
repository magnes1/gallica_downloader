from playwright.sync_api import sync_playwright
import time
import os
import re
from config import OCR_TAB_SELECTOR, TEXT_CONTAINER_SELECTOR, SAVE_TEXT_PATH

def extract_ocr_text(page, search_term):
    """Extracts OCR text from the container and saves relevant paragraphs."""
    
    print("🔍 Locating the OCR tab...")
    ocr_tab = page.locator(OCR_TAB_SELECTOR)
    
    if ocr_tab.is_visible():
        print("✅ Clicking on OCR tab...")
        ocr_tab.click()
        page.wait_for_timeout(2000)  # Wait for text to load
    else:
        print("⚠️ OCR Tab not found!")
        return None

    # Locate the scrollable text container
    scroll_container = page.locator("#mCSB_13_container")

    if not scroll_container.count():
        print("⚠️ Scrollable text container not found!")
        return None

    print("✅ Found OCR text container. Scrolling inside...")

    # Scroll down to load all text
    scroll_handle = scroll_container.element_handle()
    previous_height = 0

    while True:
        page.evaluate("(element) => element.scrollBy(0, 500)", scroll_handle)
        time.sleep(1)  # Wait for content to load
        new_height = page.evaluate("(element) => element.scrollHeight", scroll_handle)

        if new_height == previous_height:
            break
        previous_height = new_height

    print("✅ Scrolling complete. Extracting text...")

    # Extract text content
    full_text = scroll_container.inner_text()

    # Split text into paragraphs
    paragraphs = re.split(r"\n\s*\n", full_text)

    # Find paragraph with search term & get surrounding paragraphs
    extracted_text = []
    for i, paragraph in enumerate(paragraphs):
        if search_term.lower() in paragraph.lower():
            before = paragraphs[i - 1] if i > 0 else ""
            after = paragraphs[i + 1] if i < len(paragraphs) - 1 else ""
            extracted_text.append(f"Title: {page.title()}\n\nBefore:\n{before}\n\nMatch:\n{paragraph}\n\nAfter:\n{after}\n")

    if extracted_text:
        os.makedirs(SAVE_TEXT_PATH, exist_ok=True)
        filename = os.path.join(SAVE_TEXT_PATH, f"{page.title().replace(' ', '_')}.txt")
        with open(filename, "w", encoding="utf-8") as file:
            file.write("\n\n".join(extracted_text))

        print(f"✅ Extracted text saved to {filename}")
    else:
        print("⚠️ No matching paragraphs found.")

    return extracted_text
