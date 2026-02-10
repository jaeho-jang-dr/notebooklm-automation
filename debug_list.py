import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from noterang.browser import NotebookLMBrowser
from noterang.config import get_config

async def main():
    print("Debug: Listing Notebooks and Screenshotting")
    async with NotebookLMBrowser() as browser:
        await browser.ensure_logged_in()
        print(f"Logged in. URL: {browser.page.url}")
        
        # Take screenshot
        screenshot_path = Path("dashboard_debug.png").resolve()
        await browser.page.screenshot(path=str(screenshot_path))
        print(f"Screenshot saved to {screenshot_path}")
        
        # List
        notebooks = await browser.list_notebooks()
        print(f"Found {len(notebooks)} notebooks.")
        for nb in notebooks:
            print(f" - {nb['title']} ({nb['id']})")
            
        # Check specific selectors
        content = await browser.page.content()
        print(f"Page content length: {len(content)}")
        if "족저" in content:
            print("Found '족저' in page content!")
        else:
            print("'족저' NOT found in page content.")

if __name__ == "__main__":
    asyncio.run(main())
