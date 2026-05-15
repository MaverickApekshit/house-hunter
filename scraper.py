import asyncio
from playwright.async_api import async_playwright
import database
import re
import os

async def scrape_nobroker(url):
    print(f"Scraping NoBroker URL: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate and wait for content to load
        await page.goto(url, wait_until='networkidle')
        
        # Scroll down multiple times to load dynamic content
        for i in range(10):
            print(f"Scrolling {i+1}/10...")
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(2)
            
        articles = await page.query_selector_all('article')
        print(f"Found {len(articles)} listings on page.")
        
        for article in articles:
            try:
                # Title
                title_el = await article.query_selector('.heading-6')
                title = await title_el.inner_text() if title_el else "Unknown"
                
                # URL and External ID
                link_el = await article.query_selector('a.overflow-hidden')
                href = await link_el.get_attribute('href') if link_el else ""
                full_url = "https://www.nobroker.in" + href if href else ""
                
                match = re.search(r'/([a-f0-9]{32})/', full_url)
                if not match:
                    match = re.search(r'/([a-f0-9]{10,40})/', full_url) # fallback for varying lengths
                
                external_id = match.group(1) if match else "unknown"
                
                # Rent
                rent_el = await article.query_selector('#roomRent')
                rent_text = await rent_el.inner_text() if rent_el else ""
                digits = ''.join(filter(str.isdigit, rent_text))
                rent = int(digits) if digits else 0
                
                # Deposit
                deposit_el = await article.query_selector('#roomDeposit')
                deposit_text = await deposit_el.inner_text() if deposit_el else ""
                dep_digits = ''.join(filter(str.isdigit, deposit_text))
                deposit = int(dep_digits) if dep_digits else 0
                
                # Area Sqft
                sqft_el = await article.query_selector('#roomArea')
                sqft_text = await sqft_el.inner_text() if sqft_el else ""
                sqft_digits = ''.join(filter(str.isdigit, sqft_text))
                area_sqft = int(sqft_digits) if sqft_digits else 0
                
                if rent > 45000:
                    continue # Skip listings above budget
                
                # Locality extraction from title (e.g., "3 BHK In <Locality> For Rent")
                locality = "Unknown"
                if " In " in title:
                    parts = title.split(" In ", 1)
                    if " For " in parts[1]:
                        locality = parts[1].split(" For ")[0].strip()
                    else:
                        locality = parts[1].strip()
                
                data = {
                    'source': 'NoBroker',
                    'external_id': external_id,
                    'title': title,
                    'rent': rent,
                    'deposit': deposit,
                    'area_sqft': area_sqft,
                    'bhk': '3 BHK', 
                    'furnishing': 'Unknown',
                    'locality': locality,
                    'url': full_url,
                    'latitude': None, 
                    'longitude': None
                }
                
                if database.add_listing(data):
                    print(f"Added new listing: {title} - Rs. {rent}")
                else:
                    print(f"Skipped duplicate: {external_id}")
                
            except Exception as e:
                print(f"Error parsing article: {e}")
                
        await browser.close()
        print("Scraping completed.")

if __name__ == "__main__":
    database.init_db()
    
    START_URL = "https://www.nobroker.in/property/rent/bangalore/Bangalore/?searchParam=W3sibGF0IjoxMi45NzE1OTg3LCJsb24iOjc3LjU5NDU2MjcsInBsYWNlSWQiOiJDaElKYlU2MHlYQVZyanNSNEdYQkVRZGdUM1EiLCJwbGFjZU5hbWUiOiJCYW5nYWxvcmUifV0=&radius=2.0&type=BHK3,BHK4,BHK4PLUS&propertyAge=0&rent=0,45000"
    
    asyncio.run(scrape_nobroker(START_URL))
