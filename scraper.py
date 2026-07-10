import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import database
import re
import os
import config
from locality import parse_locality


def extract_labeled_int(soup, label_text):
    """Read a NoBroker overview metric (e.g. 'Deposit', 'Builtup') as an int from
    ITS OWN value node — the `heading-6` div immediately preceding the `heading-7`
    label — never the shared `flex-col` container, which holds several metrics and
    would concatenate their digits (the old bug that produced a ₹25,002,500
    'deposit' from rent+deposit+area run together). Returns None when the metric
    is absent or its value node has no digits."""
    label_div = None
    for node in soup.find_all(string=re.compile(label_text, re.I)):
        parent = node.find_parent('div')
        if parent and 'heading-7' in (parent.get('class') or []):
            label_div = parent
            break
    if label_div is None:  # fall back to the first match's parent div
        node = soup.find(string=re.compile(label_text, re.I))
        label_div = node.find_parent('div') if node else None
    if label_div is None:
        return None
    value_div = label_div.find_previous_sibling('div')
    if value_div is None:
        return None
    digits = ''.join(ch for ch in value_div.get_text() if ch.isdigit())
    return int(digits) if digits else None

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
                
                # Deposit and built-up area: read each from its own value node
                # (see extract_labeled_int) so sibling metrics are never
                # concatenated. None when absent -> stored NULL.
                deposit = extract_labeled_int(soup, "Deposit")
                area_sqft = extract_labeled_int(soup, "Builtup")
                
                # Enforce rent constraint dynamically from config
                if rent > config.MAX_RENT or rent == 0:
                    continue # Skip listings above budget or if rent extraction failed
                
                # Robust locality extraction from the title (see locality.py).
                # Returns None when no locality is confidently extractable; the
                # row is stored with a NULL locality and skipped by commute.py
                # rather than emitting a junk locality that mis-geocodes.
                locality = parse_locality(title)
                
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
