"""
Debug script - saves screenshot + HTML to see what tracker.gg actually returns
"""

from playwright.sync_api import sync_playwright

URL = "https://tracker.gg/valorant/profile/riot/welly%23wells/overview?platform=pc&playlist=competitive"

with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)  # visible window
    page = browser.new_page()

    # Spoof a real user agent
    page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept-Language": "en-US,en;q=0.9",
    })

    print("Loading page...")
    page.goto(URL, wait_until="networkidle", timeout=60000)

    # Save screenshot
    page.screenshot(path="debug_screenshot.png", full_page=True)
    print("Screenshot saved: debug_screenshot.png")

    # Save HTML
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("HTML saved: debug_page.html")

    # Print page title so we know what loaded
    print(f"Page title: {page.title()}")
    print(f"Page URL:   {page.url}")

    browser.close()