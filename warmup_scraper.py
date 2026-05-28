# warmup_scraper.py
# ---------------------------------------------------------------
# DAY 1-2 WARMUP: Scrape books from books.toscrape.com
# This teaches you the core scraping pattern you'll use on Day 3-4
# for Internshala. Master this first!
# ---------------------------------------------------------------

import requests                      # sends HTTP GET request to the URL
from bs4 import BeautifulSoup        # parses the HTML we receive
import pandas as pd                  # stores data in a table (DataFrame)
import os                            # used to handle file paths

# ---------------------------------------------------------------
# STEP 1: Send a request to the website
# ---------------------------------------------------------------

URL = "https://books.toscrape.com/"

# requests.get() is like typing a URL in your browser and hitting Enter
# The website sends back HTML — we store it in 'response'
response = requests.get(URL)

# Always check if the request succeeded
# Status code 200 = OK, 404 = Not Found, 403 = Forbidden
print(f"Status Code: {response.status_code}")  # Should print 200

if response.status_code != 200:
    print("Failed to fetch the page. Check the URL or your internet.")
    exit()

# ---------------------------------------------------------------
# STEP 2: Parse the HTML with BeautifulSoup
# ---------------------------------------------------------------

# response.text contains the raw HTML as a string
# BeautifulSoup turns it into a navigable tree structure
# 'lxml' is the parser — it reads and structures the HTML
soup = BeautifulSoup(response.text, 'lxml')

# At this point, `soup` is like the entire webpage as a Python object
# You can search it like: soup.find(), soup.find_all()

# ---------------------------------------------------------------
# STEP 3: Find all book containers
# ---------------------------------------------------------------

# Inspect the site: every book sits inside <article class="product_pod">
# find_all() returns a LIST of every element matching that description
books = soup.find_all('article', class_='product_pod')

print(f"Books found on this page: {len(books)}")  # Should print 20

# ---------------------------------------------------------------
# STEP 4: Extract data from each book
# ---------------------------------------------------------------

# We'll store each book as a dictionary, then collect all in a list
all_books = []

# Rating words on the site are stored as text ("One", "Two", etc.)
# We map them to numbers for cleaner data
rating_map = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

for book in books:
    # --- TITLE ---
    # The title is in an <a> tag inside <h3>, stored as a 'title' attribute
    # Example HTML: <h3><a title="A Light in the Attic" href="...">A Light...</a></h3>
    title = book.find('h3').find('a')['title']
    # book.find('h3')       → finds the <h3> tag inside this book's HTML
    # .find('a')            → finds the <a> tag inside that <h3>
    # ['title']             → gets the value of the 'title' attribute

    # --- PRICE ---
    # Example HTML: <p class="price_color">£51.77</p>
    price_text = book.find('p', class_='price_color').text
    # .text extracts the visible text content of the tag → "£51.77"
    # We remove the £ symbol and convert to a float for clean data
    price = float(price_text.replace('£', '').replace('Â', '').strip())

    # --- STAR RATING ---
    # Example HTML: <p class="star-rating Three">
    # The rating is embedded in the CSS class name itself — tricky!
    # We find the <p> tag with class 'star-rating', then read its second class
    star_tag = book.find('p', class_='star-rating')
    # star_tag['class'] returns a list like ['star-rating', 'Three']
    rating_word = star_tag['class'][1]   # gets 'Three'
    rating = rating_map.get(rating_word, 0)  # converts 'Three' → 3

    # --- AVAILABILITY ---
    # Example HTML: <p class="availability">In stock</p>
    availability = book.find('p', class_='availability').text.strip()
    # .strip() removes any extra whitespace or newlines around the text

    # Package this book's data as a dictionary
    all_books.append({
        'Title': title,
        'Price (£)': price,
        'Star Rating': rating,
        'Availability': availability
    })

# ---------------------------------------------------------------
# STEP 5: Store in a Pandas DataFrame
# ---------------------------------------------------------------

# pd.DataFrame() turns a list of dictionaries into a table
# Each dict key becomes a column, each dict becomes a row
df = pd.DataFrame(all_books)

print("\n--- Scraped Data Preview ---")
print(df.head(5))          # prints first 5 rows
print(f"\nTotal books scraped: {len(df)}")
print(f"Columns: {list(df.columns)}")

# ---------------------------------------------------------------
# STEP 6: Save to CSV inside the /data folder
# ---------------------------------------------------------------

# os.path.join builds a file path correctly on any OS
output_path = os.path.join('data', 'books_warmup.csv')

# index=False means don't write the row numbers (0,1,2...) into the CSV
df.to_csv(output_path, index=False)

print(f"\n✅ Data saved to: {output_path}")
print("Open the CSV in Excel or VS Code to verify!")

# ---------------------------------------------------------------
# STEP 7: Basic analysis to verify data quality
# ---------------------------------------------------------------

print("\n--- Quick Stats ---")
print(f"Average price: £{df['Price (£)'].mean():.2f}")
print(f"Most common rating: {df['Star Rating'].mode()[0]} stars")
print(f"In stock books: {(df['Availability'] == 'In stock').sum()}")