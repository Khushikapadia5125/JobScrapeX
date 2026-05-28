# warmup_pagination.py
# Scrape ALL 50 pages of books.toscrape.com (1000 books total)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time   # we use this to pause between requests (be polite to servers!)

BASE_URL = "https://books.toscrape.com/catalogue/"
all_books = []

rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

# The site has 50 pages. URLs look like:
# page-1.html, page-2.html, ... page-50.html
for page_num in range(1, 6):   # Start with 5 pages to test; change to 51 for all
    url = f"{BASE_URL}page-{page_num}.html"
    print(f"Scraping page {page_num}... {url}")

    response = requests.get(url)

    if response.status_code != 200:
        print(f"  Stopped at page {page_num} — got status {response.status_code}")
        break

    soup = BeautifulSoup(response.text, 'lxml')
    books = soup.find_all('article', class_='product_pod')

    for book in books:
        title = book.find('h3').find('a')['title']
        price = float(book.find('p', class_='price_color').text.replace('£','').replace('Â','').strip())
        rating = rating_map.get(book.find('p', class_='star-rating')['class'][1], 0)
        availability = book.find('p', class_='availability').text.strip()

        all_books.append({
            'Title': title,
            'Price (£)': price,
            'Star Rating': rating,
            'Availability': availability,
            'Page': page_num    # track which page each book came from
        })

    # ⚠️ IMPORTANT: Always sleep between requests
    # Without this, you hammer the server — rude and gets you blocked
    time.sleep(1)   # wait 1 second between each page

df = pd.DataFrame(all_books)
df.to_csv(os.path.join('data', 'books_all_pages.csv'), index=False)
print(f"\n✅ Done! Scraped {len(df)} books across {page_num} pages.")