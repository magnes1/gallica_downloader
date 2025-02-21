from playwright.sync_api import sync_playwright, TimeoutError
import time

def scroll_and_load(page, scroll_step=500, timeout=10000):
    """Scrolls the page incrementally until no more content is loaded or timeout is reached."""
    last_height = page.evaluate("document.body.scrollHeight")
    start_time = time.time()

    while True:
        page.evaluate(f"window.scrollBy(0, {scroll_step})")
        time.sleep(0.5)  # Allow time for content to load

        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            if time.time() - start_time > timeout / 1000:
                print("Timeout reached, stopping scroll.")
                break
            print("No new content loaded, checking again...")
            time.sleep(1)  # Wait longer before checking again
            if page.evaluate("document.body.scrollHeight") == last_height:
                 print("No new content after longer wait, stopping scroll.")
                 break
        else:
            start_time = time.time()  # Reset timer on new content
        last_height = new_height