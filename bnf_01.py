from playwright.sync_api import sync_playwright
import time

def search_gallica():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set True for headless mode
        page = browser.new_page()

        # Open Gallica Search
        print("🔍 Opening Gallica...")
        page.goto("https://rapportgallica.bnf.fr/recherche?query=(gallica+all+%22panafricain%22)&lang=en&suggest=0&aig=2&mb=5&collapsing=true")
        page.wait_for_load_state("networkidle")

        print("✅ Page loaded. Searching for scrollable container...")

        # Find the correct scrollable container
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
            print(f"📏 Scrolled to: {new_height}px")

            if new_height == previous_height:
                print("✅ Reached bottom of results.")
                break  # Stop scrolling if no new content loads

            previous_height = new_height

        print("✅ Scrolling complete.")

        # Step 4: Locate "See extracts in search report" buttons
        print("🔍 Looking for 'See extracts in search report' buttons...")
        page.wait_for_selector("a.focus\\:outline-none", state="visible", timeout=5000)
        buttons = page.locator("a.focus\\:outline-none").all()

        if len(buttons) == 0:
            print("❌ No buttons found! Something might have changed.")
        else:
            print(f"✅ Found {len(buttons)} buttons.")

        # Step 5: Click each button
        for index, button in enumerate(buttons):
            print(f"Clicking button {index + 1} of {len(buttons)}...")
            button.scroll_into_view_if_needed()
            button.wait_for(state="visible", timeout=5000)

            with page.expect_popup() as popup_info:
                button.hover()
                page.wait_for_timeout(500)
                button.click(force=True)

                new_page = popup_info.value  
                new_page.wait_for_load_state("networkidle")
                print(f"✅ Opened Page {index + 1}: {new_page.title()}")

                new_page.close()
                time.sleep(2)

        print("✅ All buttons clicked and pages processed.")

        # Step 6: Handle pagination
        print("🔄 Checking for 'Next Search Page' button...")
        page_count = 2
        while page_count > 0:
            next_button = page.locator("#nextResultPageButtom")

            if next_button.is_visible():
                print("➡️ Clicking 'Next Search Page'...")
                next_button.hover()
                page.wait_for_timeout(500)
                next_button.click()
                page.wait_for_load_state("networkidle")
                page_count -= 1
            else:
                print("❌ No more pages found. Stopping...")
                break

        browser.close()
        print("✅ Search process completed.")

# Run the function
search_gallica()
