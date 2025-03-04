from playwright.sync_api import sync_playwright
import json
import time
from bs4 import BeautifulSoup

SEARCH_TERM = "panafricain"
OUTPUT_FILE = "gallica_results.json"

def extract_text_with_context(full_text, keyword, char_range=500):
    """Extracts a snippet of text with 500 characters before and after the keyword."""
    index = full_text.lower().find(keyword.lower())
    if index == -1:
        return None  # Keyword not found
    start = max(0, index - char_range)
    end = min(len(full_text), index + char_range)
    return full_text[start:end]

def extract_ocr_text(page):
    """Extracts OCR text snippet from the 'TEXT MODE (OCR)' tab."""
    print("🟢 Checking for OCR Text Mode button...")
    ocr_button = page.locator("button#acc_1-0_panel_4_trigger")
    if not ocr_button.count():
        print("⚠️ OCR Text Mode button not found!")
        return None
    print("✅ Clicking OCR Text Mode button...")
    ocr_button.click()
    time.sleep(2)

    page.wait_for_selector("div#mCSB_13_container", timeout=6000)
    ocr_container = page.locator("div#mCSB_13_container")
    if not ocr_container.count():
        print("⚠️ OCR container not found.")
        return None

    print("✅ OCR container found. Scrolling inside it...")
    ocr_container.hover()
    time.sleep(1)
    ocr_handle = ocr_container.element_handle()
    if not ocr_handle:
        print("⚠️ Could not retrieve OCR container handle.")
        return None

    previous_height = 0
    while True:
        page.evaluate("(element) => element.scrollBy(0, 500)", ocr_handle)
        time.sleep(1)
        new_height = page.evaluate("(element) => element.scrollHeight", ocr_handle)
        if new_height == previous_height:
            break
        previous_height = new_height

    print("✅ Finished scrolling OCR container.")
    ocr_text = ocr_container.inner_text().replace("\n", " ").strip()
    snippet = extract_text_with_context(ocr_text, SEARCH_TERM)
    return snippet if snippet else "Not found"

def extract_metadata_from_about(page):
    """Extracts metadata from the ABOUT section."""
    print("🔘 Clicking ABOUT tab...")
    about_button = page.locator("button#acc_1-0_panel_3_trigger")
    if about_button.count() > 0:
        about_button.click()
        time.sleep(2)
    else:
        print("❌ ABOUT button not found!")
        return None

    print("🔍 Finding ABOUT scrollable container...")
    scroll_container = page.locator("#mCSB_15_container")

    if scroll_container.count() == 0:
        print("❌ ABOUT scroll container not found!")
        return None

    scroll_handle = scroll_container.element_handle()
    if not scroll_handle:
        print("❌ Could not retrieve scroll handle. Exiting...")
        return None

    print("🖱️ Scrolling through ABOUT section...")
    previous_height = 0
    while True:
        page.evaluate("(element) => element.scrollBy(0, 300)", scroll_handle)
        time.sleep(2)
        new_height = page.evaluate("(element) => element.scrollHeight", scroll_handle)
        if new_height == previous_height:
            break
        previous_height = new_height

    print("✅ Scrolling complete.")
    print("📄 Extracting metadata from ABOUT section...")
    about_html = page.content()
    soup = BeautifulSoup(about_html, "html.parser")
    about_container = soup.find("div", {"id": "mCSB_15_container"})

    if not about_container:
        print("❌ ABOUT metadata section not found!")
        return None

    metadata = {}
    key_mappings = {
        "Title": "Title",
        "Author": "Author",
        "Publisher": "Publisher",
        "Publication Date": "Publication date",
        "Type": "Type",
        "Language": "Language",
        "Description": "Description",
        "Identifier": "Identifier"
    }

    for key, search_text in key_mappings.items():
        label_element = about_container.find("b", string=lambda text: text and search_text in text)
        if label_element:
            value_element = label_element.find_parent().find_next("span")
            if not value_element:
                value_element = label_element.find_parent().find_next("div")
            metadata[key] = value_element.text.strip() if value_element else "Not Found"
        else:
            metadata[key] = "Not Found"

    identifier_link = about_container.find("a", href=True, string=lambda text: "ark:/" in text)
    metadata["Identifier"] = identifier_link["href"] if identifier_link else "Not Found"

    return metadata

def process_page(page, results):
    """Extracts data from all articles on a single page."""
    print("Scrolling to load all results...")
    scroll_container = page.locator("div.overflow-auto.h-full.z-2")
    if not scroll_container.count():
        print("⚠️ Scrollable container not found. Skipping...")
        return

    scroll_container.hover()
    time.sleep(1)
    
    scroll_handle = scroll_container.element_handle()
    if not scroll_handle:
        print("⚠️ Could not retrieve scroll handle. Skipping...")
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
    page.wait_for_selector("a.focus\\:outline-none", state="visible", timeout=6000)
    buttons = page.locator("a.focus\\:outline-none").all()
    print(f"Found {len(buttons)} result buttons.")

    for idx, button in enumerate(buttons):
        print(f"Processing result {idx + 1}...")
        button.scroll_into_view_if_needed()
        button.wait_for(state="visible", timeout=5000)

        with page.expect_popup() as popup_info:
            button.click(force=True)
        new_page = popup_info.value
        new_page.wait_for_load_state("networkidle")

        ocr_snippet = extract_ocr_text(new_page)
        metadata = extract_metadata_from_about(new_page)

        if metadata:
            results.append({**metadata, "ocr_text_snippet": ocr_snippet})

        new_page.close()
        time.sleep(2)

def search_gallica():
    """Main function to scrape multiple pages of Gallica search results."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False for debugging
        page = browser.new_page()

        print("Opening Gallica search page...")
        page.goto("https://rapportgallica.bnf.fr/recherche?query=(gallicapublication_date%3E=%221945%22+and+gallicapublication_date%3C=%221955%22)+and+(subgallica+all+%22panafricain%22)&filter=&aig=2&mb=5&collapsing=true&lang=en")
        page.wait_for_load_state("networkidle")

        while True:
            process_page(page, results)

            # Locate "Next" button and click if available
            next_button = page.locator("button#nextResultPageButtom")
            if next_button.count() > 0 and next_button.is_enabled():
                print("📄 Clicking next page...")
                next_button.click()
                page.wait_for_load_state("networkidle")
                time.sleep(3)
            else:
                print("✅ No more pages left.")
                break

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        print(f"✅ Data saved to {OUTPUT_FILE}")
        browser.close()

search_gallica()
