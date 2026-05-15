import asyncio
from playwright.async_api import async_playwright
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def debug_nobroker(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        
        articles = await page.query_selector_all('article')
        if articles:
            html = await articles[0].inner_html()
            print(html)
        await browser.close()

if __name__ == "__main__":
    START_URL = "https://www.nobroker.in/property/rent/bangalore/Bangalore/?searchParam=W3sibGF0IjoxMi45NzE1OTg3LCJsb24iOjc3LjU5NDU2MjcsInBsYWNlSWQiOiJDaElKYlU2MHlYQVZyanNSNEdYQkVRZGdUM1EiLCJwbGFjZU5hbWUiOiJCYW5nYWxvcmUifV0=&radius=2.0&type=BHK3,BHK4,BHK4PLUS&propertyAge=0&rent=0,45000"
    asyncio.run(debug_nobroker(START_URL))
