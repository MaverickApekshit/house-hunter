import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import database
import re
import os
import config

async def scrape_nobroker(url):
    print(f"Scraping NoBroker URL: {url}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate and wait for content to load
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        
        # Scroll down multiple times to load dynamic content
        for i in range(10):
            print(f"Scrolling {i+1}/10...")
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(2)
            
        articles = await page.query_selector_all('article')
        print(f"Found {len(articles)} listings on page.")
        
        for article in articles:
            try:
                html = await article.inner_html()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Title
                title_el = soup.select_one('.heading-6')
                title = title_el.text.strip() if title_el else "Unknown"
                
                # URL and External ID
                link_el = soup.select_one('a.overflow-hidden')
                href = link_el['href'] if link_el and link_el.has_attr('href') else ""
                full_url = "https://www.nobroker.in" + href if href else ""
                
                match = re.search(r'/([a-f0-9]{32})/', full_url)
                if not match:
                    match = re.search(r'/([a-f0-9]{10,40})/', full_url)
                
                external_id = match.group(1) if match else "unknown"
                
                # Rent
                rent = 0
                price_meta = soup.select_one('meta[itemprop="price"]')
                if price_meta and price_meta.has_attr('content'):
                    rent_digits = ''.join(filter(str.isdigit, price_meta['content']))
                    rent = int(rent_digits) if rent_digits else 0
                
                # Deposit
                deposit = 0
                deposit_label = soup.find(string=re.compile("Deposit", re.I))
                if deposit_label:
                    deposit_parent = deposit_label.find_parent('div', class_='flex-col')
                    if deposit_parent:
                        dep_digits = ''.join(filter(str.isdigit, deposit_parent.text))
                        deposit = int(dep_digits) if dep_digits else 0
                
                # Area Sqft
                area_sqft = 0
                builtup_label = soup.find(string=re.compile("Builtup", re.I))
                if builtup_label:
                    builtup_parent = builtup_label.find_parent('div', class_='flex-col')
                    if builtup_parent:
                        sqft_digits = ''.join(filter(str.isdigit, builtup_parent.text))
                        area_sqft = int(sqft_digits) if sqft_digits else 0
                
                # Enforce rent constraint dynamically from config
                if rent > config.MAX_RENT or rent == 0:
                    continue # Skip listings above budget or if rent extraction failed
                
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
                    'bhk': config.TARGET_BHK, 
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
    
    # Construct Start URL dynamically using dynamic configuration value for MAX_RENT
    START_URL = f"https://www.nobroker.in/property/rent/bangalore/Bangalore/?searchParam=W3sibGF0IjoxMi45NzE1OTg3LCJsb24iOjc3LjU5NDU2MjcsInBsYWNlSWQiOiJDaElKYlU2MHlYQVZyanNSNEdYQkVRZGdUM1EiLCJwbGFjZU5hbWUiOiJCYW5nYWxvcmUifV0=&radius=2.0&type=BHK3,BHK4,BHK4PLUS&propertyAge=0&rent=0,{config.MAX_RENT}"
    
    asyncio.run(scrape_nobroker(START_URL))
