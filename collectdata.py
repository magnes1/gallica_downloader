from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import json
import time
from bs4 import BeautifulSoup

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
    page.wait_for_load_state("networkidle")

    if ocr_button.count() == 0:
        print("⚠️ OCR Text Mode button not found! Saving URL instead.")
        return f"Failed to extract OCR text. URL: {page.url}"
    
    print("✅ Clicking OCR Text Mode button...")
    try:
        if not ocr_button.get_attribute("aria-expanded") or ocr_button.get_attribute("aria-expanded") == "false":
                ocr_button.click()
                time.sleep(3)  # Allow time for text to load

        # ✅ Wait for OCR container to appear
        print("🔍 Waiting for OCR text container to appear...")
        page.wait_for_selector("//div[@id='textImageModeDiv']", state="attached", timeout=8000)

        parent_container = page.locator("//div[@id='textImageModeDiv']")
        ocr_container = parent_container.locator(".mCustomScrollBox")

        if ocr_container.count() == 0:
            print("⚠️ OCR container not found. Saving URL instead.")
            return f"Failed to extract OCR text. URL: {page.url}"

        print("✅ OCR container found. Hovering and scrolling inside it...")
        ocr_container.hover()
        time.sleep(3)

        # ✅ Ensure scrolling works
        ocr_handle = ocr_container.element_handle()
        if not ocr_handle:
            print("⚠️ Could not retrieve OCR container handle. Saving URL instead.")
            return f"Failed to extract OCR text. URL: {page.url}"

        previous_height = 0
        while True:
            page.evaluate("(element) => element.scrollBy(0, 500)", ocr_handle)
            time.sleep(3)
            new_height = page.evaluate("(element) => element.scrollHeight", ocr_handle)
            if new_height == previous_height:
                break
            previous_height = new_height

        page.wait_for_load_state("networkidle")
        print("✅ Finished scrolling OCR container.")
        ocr_text = ocr_container.inner_text().replace("\n", " ").strip()

        # ✅ Extract relevant snippet
        snippet = extract_text_with_context(ocr_text, SEARCH_TERM)
        return snippet if snippet else "Not found"
    
    except Exception as e:
        print(f"❌ Error extracting OCR text: {e}. Saving URL instead.")
        return f"Failed to extract OCR text. URL: {page.url}"    

def extract_metadata_from_about(page):
    """Extracts metadata from the ABOUT section, with a maximum of 3 retries if necessary."""

    print("🔘 Clicking ABOUT tab...")
    about_button = page.locator("button#acc_1-0_panel_3_trigger")
    page.wait_for_load_state("networkidle")

    if about_button.count() > 0:
        about_button.click()
        time.sleep(3)  # Allow time for content to expand
    else:
        print("❌ ABOUT button not found!")
        return None

    # Locate the scrollable container with retries
    for attempt in range(3):
        print(f"🔍 Finding ABOUT scrollable container (Attempt {attempt+1}/3)...")
        page.wait_for_load_state("networkidle")
       
        parent_container = page.locator("div.accordion__panel").filter(has=page.locator("#enSavoirPlusContent"))
        scroll_container = parent_container.locator(".mCustomScrollBox")
        scroll_container.scroll_into_view_if_needed()
    
        if scroll_container.count() > 0:
            break
        time.sleep(3)

    if scroll_container.count() == 0:
        print("❌ ABOUT scroll container not found!")
        return None

    # Scroll through the ABOUT container
    print("🖱️ Scrolling through ABOUT section...")
    scroll_handle = scroll_container.element_handle()

    if not scroll_handle:
        print("❌ Could not retrieve scroll handle.")
        return None

    previous_height = 0
    for _ in range(10):  # Limit number of scroll attempts
        page.evaluate("(element) => element.scrollBy(0, 300)", scroll_handle)
        time.sleep(3)
        new_height = page.evaluate("(element) => element.scrollHeight", scroll_handle)
        if new_height == previous_height:
            break
        previous_height = new_height

    print("✅ Scrolling complete.")
    page.wait_for_load_state("domcontentloaded")
    
    # Extract page content and parse with BeautifulSoup
    for attempt in range(3):  # Try extracting metadata up to 3 times
        print(f"📄 Extracting metadata from ABOUT section (Attempt {attempt+1}/3)...")
        page.wait_for_load_state("networkidle")
        scroll_html = scroll_container.inner_html()
        soup = BeautifulSoup(scroll_html, "html.parser")
        about_container = soup.find("div", {"id": "mCSB_15_container"})
        extracted_text = soup.get_text(separator="\n", strip=True)
        
        def extract_field(labels):
            """Finds the value next to a given list of possible labels in <b> tags."""
            for label in labels:
                field = soup.find("b", string=lambda text: text and label in text)
                if field:
                    next_sibling = field.find_parent("span").find_next_sibling("span")  # Find the <span> with the actual value
                    return next_sibling.get_text(strip=True) if next_sibling else "Not Found"
            return "Not Found"

        # Step 6: Create structured metadata dictionary
        metadata = {
            "Title": extract_field(["Title", "Titre"]),
            "Author": extract_field(["Author", "Auteur"]),
            "Publisher": extract_field(["Publisher", "Éditeur"]),
            "Publication Date": extract_field(["Publication date", "Date de publication"]),
            "Type": extract_field(["Type"]),
            "Language": extract_field(["Language", "Langue"]),
            "Description": extract_field(["Description", "Résumé"]),
            "Identifier": soup.find("a", href=True)["href"] if soup.find("a", href=True) else "Not Found"
        }
    
        if metadata["Title"] == "Not Found" or metadata["Publisher"] == "Not Found":
            print(f"⚠️ Missing metadata for {page.url}, saving URL instead.")
            metadata["Title"] = metadata["Publisher"] = "Data Not Available"

        else:
            print(f"✅ Successfully extracted metadata: {metadata}")
            return metadata

        print("⚠️ Metadata extraction incomplete, retrying...")
        time.sleep(3)

    print("❌ Failed to extract complete metadata after 3 attempts.")
    return None

def process_page(page, results):
    """Extracts data from all articles on a single page."""
    print("Scrolling to load all results...")
    scroll_container = page.locator("div.overflow-auto.h-full.z-2")
    if not scroll_container.count():
        print("⚠️ Scrollable container not found. Skipping...")
        return

    scroll_container.hover()
    time.sleep(3)
    
    scroll_handle = scroll_container.element_handle()
    if not scroll_handle:
        print("⚠️ Could not retrieve scroll handle. Skipping...")
        return

    previous_height = 0
    while True:
        page.evaluate("(element) => element.scrollBy(0, 500)", scroll_handle)
        time.sleep(4)
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
        try:
            # Ensure the button is stable before scrolling (if needed)
            for _ in range(3):  # Retry checking for stability
                # if button.is_visible() and button.is_enabled():
                if button.is_visible():
                    break
            print("⏳ Button is not stable yet, retrying...")
            time.sleep(1)
            button.scroll_into_view_if_needed()
            button.wait_for(state="visible", timeout=5000)
            
        except PlaywrightTimeoutError:
            print("⚠️ Cannot find button. Continuing...")
        except Exception as e:
            print(f"⚠️ Button error: {e}")
            
        try:
            with page.expect_popup() as popup_info:
                button.click(force=True)
                new_page = popup_info.value
                new_page.wait_for_load_state("networkidle")


            metadata = extract_metadata_from_about(new_page)
            ocr_snippet = extract_ocr_text(new_page)
            
            if metadata:
                results.append({**metadata, "ocr_text_snippet": ocr_snippet})

                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=4, ensure_ascii=False)
                
                print(f"✅ Data saved to {OUTPUT_FILE}")
                
            new_page.close()
            time.sleep(2)
            
        except PlaywrightTimeoutError:
            print("⚠️ No popup appeared within 10 seconds. Continuing...")
        except Exception as e:
            print(f"⚠️ Unexpected popup error: {e}")
        
def search_gallica(gotourl):
    """Main function to scrape multiple pages of Gallica search results."""
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Opening Gallica search page...")
        page.goto(gotourl)
        page.wait_for_load_state("networkidle", timeout=60000)

        while True:
            process_page(page, results)

            next_buttons = page.locator("a[title='Next page']").all()

            if len(next_buttons) > 0:
                next_button = next_buttons[-1]  # Select the last "Next Page" button found

                if next_button.is_visible():
                    print("🔹 Clicking 'Next Page' button...")
                    next_button.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(4)  # Allow time for the new results to load
                else:
                    print("⚠️ 'Next Page' button is not visible. Exiting loop.")
                    break
            else:
                print("✅ No more pages left. Exiting loop.")
                break  # Exit loop when no "Next Page" button is found

        print("🎉 Finished extracting all pages.")
        browser.close()


# SEARCH_TERM = "panafricain"
# OUTPUT_FILE = "gallica_results_panafricanisme_prebandung.json"
# print(f"Searching {SEARCH_TERM} ...")
# search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=(dc.type+all+%22manuscrit%22+or+dc.type+all+%22monographie%22+or+dc.type+all+%22fascicule%22)+and+(gallicapublication_date%3E=%221945%22+and+gallicapublication_date%3C=%221955%22)+and+(ocr.quality+all+%22Texte+disponible%22)+and+(subgallica+all+%22panfricain%22)&filter=&aig=2&mb=5&collapsing=true&lang=en")

# SEARCH_TERM = "panafricain"
# OUTPUT_FILE = "gallica_results_panafricanisme_prebandung.json"
# print(f"Searching {SEARCH_TERM} ...")
# search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=(dc.type+all+%22manuscrit%22+or+dc.type+all+%22monographie%22+or+dc.type+all+%22fascicule%22)+and+(gallicapublication_date%3E=%221945%22+and+gallicapublication_date%3C=%221955%22)+and+(ocr.quality+all+%22Texte+disponible%22)+and+(subgallica+all+%22panfrican%22)&filter=&aig=2&mb=5&collapsing=true&lang=en")

# SEARCH_TERM = "panafricanisme"
# OUTPUT_FILE = "gallica_results_panafricanisme_prebandung.json"
# print(f"Searching {SEARCH_TERM} ...")
# search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=(dc.type+all+%22manuscrit%22+or+dc.type+all+%22monographie%22+or+dc.type+all+%22fascicule%22)+and+(gallicapublication_date%3E=%221945%22+and+gallicapublication_date%3C=%221955%22)+and+(ocr.quality+all+%22Texte+disponible%22)+and+(subgallica+all+%22panafricanisme%22)&filter=&aig=2&mb=5&collapsing=true&lang=en")

# SEARCH_TERM = "bandung"
# OUTPUT_FILE = "gallica_results_bandung_prebandung.json"
# print(f"Searching {SEARCH_TERM} ...")
# search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=(dc.type+all+%22manuscrit%22+or+dc.type+all+%22monographie%22+or+dc.type+all+%22fascicule%22)+and+(gallicapublication_date%3E=%221953%22+and+gallicapublication_date%3C=%221955%22)+and+(ocr.quality+all+%22Texte+disponible%22)+and+(subgallica+all+%22bandung%22)&aig=2&mb=5&collapsing=true&lang=en")


# SEARCH_TERM = "bandung"
# OUTPUT_FILE = "gallica_results_bandung_postbandung.json"
# print(f"Searching {SEARCH_TERM} ...")
# search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=(dc.type+all+%22manuscrit%22+or+dc.type+all+%22monographie%22+or+dc.type+all+%22fascicule%22)+and+(gallicapublication_date%3E=%221956%22+and+gallicapublication_date%3C=%221965%22)+and+(ocr.quality+all+%22Texte+disponible%22)+and+(subgallica+all+%22bandung%22)&aig=2&mb=5&collapsing=true&lang=en")

# SEARCH_TERM = "panafricain"
# OUTPUT_FILE = "gallica_results_panafricanisme_postbandung.json"
# print(f"Searching {SEARCH_TERM} ...")
# search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=(dc.type+all+%22manuscrit%22+or+dc.type+all+%22monographie%22+or+dc.type+all+%22fascicule%22)+and+(gallicapublication_date%3E=%221956%22+and+gallicapublication_date%3C=%221965%22)+and+(ocr.quality+all+%22Texte+disponible%22)+and+(subgallica+all+%22panfricain%22)&filter=&aig=2&mb=5&collapsing=true&lang=en")

# SEARCH_TERM = "panafricain"
# OUTPUT_FILE = "gallica_results_panafricanisme_postbandung.json"
# print(f"Searching {SEARCH_TERM} ...")
# search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=(dc.type+all+%22manuscrit%22+or+dc.type+all+%22monographie%22+or+dc.type+all+%22fascicule%22)+and+(gallicapublication_date%3E=%221956%22+and+gallicapublication_date%3C=%221965%22)+and+(ocr.quality+all+%22Texte+disponible%22)+and+(subgallica+all+%22panfrican%22)&filter=&aig=2&mb=5&collapsing=true&lang=en")

# SEARCH_TERM = "panafricanisme"
# OUTPUT_FILE = "gallica_results_panafricanisme_postbandung.json"
# print(f"Searching {SEARCH_TERM} ...")
# search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=(dc.type+all+%22manuscrit%22+or+dc.type+all+%22monographie%22+or+dc.type+all+%22fascicule%22)+and+(gallicapublication_date%3E=%221956%22+and+gallicapublication_date%3C=%221965%22)+and+(ocr.quality+all+%22Texte+disponible%22)+and+(subgallica+all+%22panafricanisme%22)&filter=&aig=2&mb=5&collapsing=true&lang=en")

SEARCH_TERM = "panafrican socialism"
OUTPUT_FILE = "gallica_results_panafrican_socialism_prebandung.json"
print(f"Searching {SEARCH_TERM} ...")
search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=text+all+%22panafrican+socialism%22+and+(gallicapublication_date%3E=%221945%22+and+gallicapublication_date%3C=%221955%22)&suggest=10&keywords=panafrican+socialism&aig=2&mb=5&collapsing=true&lang=en")

SEARCH_TERM = "panafrican socialism"
OUTPUT_FILE = "gallica_results_panafrican_socialism_prebandung.json"
print(f"Searching {SEARCH_TERM} ...")
search_gallica(gotourl ="https://rapportgallica.bnf.fr/recherche?query=text+all+%22panafrican+socialism%22+and+(gallicapublication_date%3E=%221955%22+and+gallicapublication_date%3C=%221965%22)&suggest=10&keywords=panafrican+socialism&aig=2&mb=5&collapsing=true&lang=en")