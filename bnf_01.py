from playwright.sync_api import sync_playwright
import time
        
def search_gallica():
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=False)  # Set True to run in the background
        page = browser.new_page()

        # Step 1: Open Gallica
        print("Opening Gallica...")
        page.goto("https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&version=1.2&query=%28dc.type%20all%20%22manuscrit%22%20or%20dc.type%20all%20%22monographie%22%20or%20dc.type%20all%20%22fascicule%22%29%20and%20%28gallicapublication_date%3E%3D%221945%22%20and%20gallicapublication_date%3C%3D%221955%22%29%20and%20%28subgallica%20all%20%22panafricain%22%29&filter=")

        page_count = 2
        while page_count > 0:
            print("🔄 Simulating user scrolling...")
            # #Scroll down by the height of the document
            # page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            # page.wait_for_timeout(3000) 
            # page.wait_for_load_state("networkidle")  # Ensure new content loads
            
            for _ in range(10):
                page.keyboard.press("PageDown")
                page.wait_for_timeout(1000)  # Wait for new elements
            page.wait_for_timeout(50)
            
            # Step 3: Click "See extracts in search reports"
            # buttons = page.locator("text=See extracts in search report")
            page.wait_for_selector("a.btn.btn-default.btn-voir-extraits", state="visible", timeout=5000)
            buttons = page.locator("a.btn.btn-default.btn-voir-extraits").all()
            print(f"New total buttons found: {len(buttons)}")
        
            # Step 3: Click each button and handle the new tab
            for index, button in enumerate(buttons):
                print(f"Clicking button {index + 1} of {len(buttons)}...")

                button.scroll_into_view_if_needed()
                button.wait_for(state="visible", timeout=5000)

                with page.expect_popup() as popup_info:
                    button.hover()
                    page.wait_for_timeout(500)
                    button.click(force=True)  # Force click to avoid hidden elements

                    # Handle the new popup/tab
                    new_page = popup_info.value  
                    new_page.wait_for_load_state("networkidle")

                    # Extract data from the new tab 
                    print(f"✅ Opened Page {index + 1}: {new_page.title()}")

                    # Close the new tab
                    new_page.close()
                    time.sleep(2)

            # Locate the "Next Search Page" button
            next_button = page.locator("#nextResultPageButtom")
            
            # Check if the button is visible
            if next_button.is_visible():
                print("Clicking the 'Next Search Page' button...")
                next_button.hover()
                page.wait_for_timeout(500)
                next_button.click()
                page.wait_for_load_state("networkidle")  # Ensure new content loads
                page_count -= 1  # Decrement counter
            else:
                print("No 'Next Search Page' button found.")
                break  # Stop loop if the button is missing

        # Close the browser
        browser.close()

# Run the function
search_gallica()
