# scraper.py
# ---------------------------------------------------------------
# JobScrapeX — Day 3-4
# Scrapes internship listings from Internshala's AJAX endpoint
# Strategy: hit the internal HTML-returning API, parse with BS4
# ---------------------------------------------------------------

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from datetime import datetime

# ---------------------------------------------------------------
# CONFIGURATION — tweak these to control what gets scraped
# ---------------------------------------------------------------

BASE_URL = "https://internshala.com/internships/ajax/search/page-{}"

# These headers are CRITICAL — without them the server may block us
# We're pretending to be a real browser making an AJAX request
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",   # tells server this is an AJAX call
    "Referer": "https://internshala.com/internships/",  # pretend we came from the listings page
    "Accept": "text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_PAGES = 5          # scrape 5 pages (~60-75 internships). Change to 10, 20 etc. later
SLEEP_BETWEEN_PAGES = 2  # seconds to wait between page requests (be polite!)


# ---------------------------------------------------------------
# CORE FUNCTION: scrape a single page, return list of dicts
# ---------------------------------------------------------------

def scrape_page(page_num):
    """
    Fetches one page of internship listings and extracts all fields.
    Returns a list of dictionaries, one per internship.
    """
    url = BASE_URL.format(page_num)
    print(f"  Fetching page {page_num}: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        # timeout=15 means: if server doesn't respond in 15s, give up (don't hang forever)
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Network error on page {page_num}: {e}")
        return []   # return empty list so we can keep going with other pages

    if response.status_code != 200:
        print(f"  ❌ Got status {response.status_code} on page {page_num}. Stopping.")
        return []

    # Parse the HTML response with BeautifulSoup
    soup = BeautifulSoup(response.text, 'lxml')

    # ---------------------------------------------------------------
    # FIND ALL INTERNSHIP CARDS
    # Each internship lives inside a <div class="individual_internship">
    # This is the main container — everything else is inside here
    # ---------------------------------------------------------------
    internship_cards = soup.find_all('div', class_='individual_internship')

    if not internship_cards:
        # Try alternate class name (Internshala sometimes changes these)
        internship_cards = soup.find_all('div', class_='internship_meta')

    print(f"  Found {len(internship_cards)} internships on page {page_num}")

    page_results = []

    for card in internship_cards:
        try:
            internship = extract_internship_data(card)
            if internship:   # only add if extraction succeeded
                page_results.append(internship)
        except Exception as e:
            # If one card fails, skip it and continue — don't crash the whole scraper
            print(f"  ⚠️  Skipped one card due to error: {e}")
            continue

    return page_results


# ---------------------------------------------------------------
# EXTRACTION FUNCTION: pull all fields from one card's HTML
# ---------------------------------------------------------------

def extract_internship_data(card):
    """
    Given a BeautifulSoup tag for one internship card,
    extracts all fields and returns a dictionary.
    Returns None if this card is an ad (not a real listing).
    """

    # --- SKIP ADS ---
    if card.get('data-is-ad') == '1':
        return None
    if 'image_ad' in card.get('class', []):
        return None

    # ---------------------------------------------------------------
    # JOB TITLE
    # HTML: <a id="job_title" class="job-title-href">Python Developer</a>
    # The actual clickable title link has id="job_title" — most reliable selector
    # ---------------------------------------------------------------
    title = None
    title_tag = card.find('a', id='job_title')
    if title_tag:
        title = title_tag.get_text(strip=True)

    # ---------------------------------------------------------------
    # COMPANY NAME
    # HTML: <p class="company-name">Loopday Labs</p>  ✅ already working
    # ---------------------------------------------------------------
    company = None
    company_tag = card.find('p', class_='company-name')
    if company_tag:
        company = company_tag.get_text(strip=True)

    # ---------------------------------------------------------------
    # LOCATION
    # HTML: <div class="row-1-item locations"><i>...</i><span><a>Surat</a>(Hybrid)</span></div>
    # We find the div with class "locations", then get the <a> tag text inside it
    # ---------------------------------------------------------------
    location = None
    location_div = card.find('div', class_='locations')
    if location_div:
        location_a = location_div.find('a')
        if location_a:
            location = location_a.get_text(strip=True)
        # Also check if it says Work from Home
        full_text = location_div.get_text(strip=True)
        if 'Work from Home' in full_text or 'work_from_home' in str(location_div):
            location = 'Work from Home'

    # ---------------------------------------------------------------
    # STIPEND
    # HTML: <span class="stipend">₹ 12,000 - 18,000 /month</span>  ✅ already working
    # ---------------------------------------------------------------
    stipend = None
    stipend_tag = card.find('span', class_='stipend')
    if stipend_tag:
        stipend = stipend_tag.get_text(strip=True)

    # ---------------------------------------------------------------
    # DURATION
    # HTML: <div class="row-1-item"><i class="ic-16-calendar"></i><span>6 Months</span></div>
    # Strategy: find the row-1-item that contains the calendar icon, grab its span
    # ---------------------------------------------------------------
    duration = None
    row_items = card.find_all('div', class_='row-1-item')
    for item in row_items:
        # The duration row has a calendar icon inside it
        if item.find('i', class_='ic-16-calendar'):
            span = item.find('span')
            if span:
                duration = span.get_text(strip=True)
            break

    # ---------------------------------------------------------------
    # SKILLS / TECHNOLOGIES
    # HTML: <div class="tags_container"><a class="round_tabs">Python</a>...</div>
    # These appear lower in the card — find all round_tabs anchor tags
    # ---------------------------------------------------------------
    skills = None
    job_skills_div = card.find('div', class_='job_skills')
    if job_skills_div:
        skill_tags = job_skills_div.find_all('div', class_='job_skill')
        skill_list = [s.get_text(strip=True) for s in skill_tags if s.get_text(strip=True)]
        if skill_list:
            skills = ', '.join(skill_list)

    # ---------------------------------------------------------------
    # DATE POSTED / ACTIVELY HIRING BADGE
    # HTML: <div class="actively-hiring-badge">Actively hiring</div>
    #    or <div class="status-inactive">1 day ago</div>
    # ---------------------------------------------------------------
    date_posted = None
    date_tag = (
        card.find('div', class_='status-inactive') or
        card.find('span', class_='posted_by_time_ago')
    )
    if date_tag:
        date_posted = date_tag.get_text(strip=True)
    else:
        # If actively hiring badge exists, note that instead
        hiring_badge = card.find('div', class_='actively-hiring-badge')
        if hiring_badge:
            date_posted = hiring_badge.get_text(strip=True)

    # ---------------------------------------------------------------
    # INTERNSHIP LINK
    # The card itself has data-href attribute — most reliable
    # HTML: <div data-href="/internship/detail/...">
    # ---------------------------------------------------------------
    link = None
    data_href = card.get('data-href')
    if data_href:
        link = 'https://internshala.com' + data_href
    else:
        link_tag = card.find('a', class_='job-title-href')
        if link_tag:
            link = 'https://internshala.com' + link_tag.get('href', '')

    # Skip completely empty cards
    if not title and not company:
        return None

    return {
        'Title':        title       or 'N/A',
        'Company':      company     or 'N/A',
        'Location':     location    or 'N/A',
        'Stipend':      stipend     or 'N/A',
        'Duration':     duration    or 'N/A',
        'Skills':       skills      or 'N/A',
        'Date Posted':  date_posted or 'N/A',
        'Link':         link        or 'N/A',
        'Scraped At':   datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }


# ---------------------------------------------------------------
# MAIN SCRAPER: loop through all pages, collect everything
# ---------------------------------------------------------------

def scrape_internshala(max_pages=MAX_PAGES):
    """
    Main function. Scrapes multiple pages and returns a DataFrame.
    """
    print("=" * 55)
    print("  JobScrapeX — Internshala Scraper Starting")
    print("=" * 55)

    all_internships = []

    for page_num in range(1, max_pages + 1):
        print(f"\n📄 Page {page_num} of {max_pages}")

        page_data = scrape_page(page_num)
        all_internships.extend(page_data)  # add this page's results to master list

        print(f"  ✅ Total collected so far: {len(all_internships)}")

        # Don't hammer the server — wait between pages
        # Skip the sleep on the last page (no point waiting after we're done)
        if page_num < max_pages:
            print(f"  ⏳ Waiting {SLEEP_BETWEEN_PAGES}s before next page...")
            time.sleep(SLEEP_BETWEEN_PAGES)

    # ---------------------------------------------------------------
    # BUILD DATAFRAME AND SAVE
    # ---------------------------------------------------------------
    if not all_internships:
        print("\n❌ No data scraped. The HTML structure may have changed.")
        print("   Run debug_scraper.py to inspect the raw HTML.")
        return pd.DataFrame()

    df = pd.DataFrame(all_internships)

    print(f"\n{'=' * 55}")
    print(f"  Scraping complete!")
    print(f"  Total internships scraped: {len(df)}")
    print(f"  Pages scraped: {max_pages}")
    print(f"{'=' * 55}")

    # Preview
    print("\n--- Sample Data (first 3 rows) ---")
    print(df[['Title', 'Company', 'Location', 'Stipend']].head(3).to_string())

    # Save to CSV
    os.makedirs('data', exist_ok=True)  # create /data folder if it doesn't exist
    output_path = os.path.join('data', 'internships_raw.csv')
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    # utf-8-sig adds a BOM so Excel opens it correctly with Indian characters (₹ etc.)

    print(f"\n✅ Saved to: {output_path}")
    return df


# ---------------------------------------------------------------
# DEBUG HELPER — run this first to inspect raw HTML
# ---------------------------------------------------------------

def debug_html_structure():
    """
    Saves raw HTML to a file so you can open it in VS Code
    and find the correct class names if scraper returns empty data.
    """
    print("🔍 Fetching raw HTML for debugging...")
    response = requests.get(
        BASE_URL.format(1),
        headers=HEADERS,
        timeout=15
    )
    debug_path = os.path.join('data', 'debug_page1.html')
    os.makedirs('data', exist_ok=True)
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"✅ Raw HTML saved to: {debug_path}")
    print("   Open it in VS Code → Ctrl+F → search 'individual_internship'")
    print("   This shows you the exact class names to use")


# ---------------------------------------------------------------
# RUN
# ---------------------------------------------------------------

if __name__ == '__main__':
    # STEP 1: Always debug first — uncomment this line on first run
    # debug_html_structure()

    # STEP 2: Run the main scraper
    df = scrape_internshala(max_pages=5)

    if not df.empty:
        print("\n--- Column Summary ---")
        for col in df.columns:
            non_na = (df[col] != 'N/A').sum()
            print(f"  {col}: {non_na}/{len(df)} filled")

# ---------------------------------------------------------------
# AUTO-SCHEDULER
# Run this to scrape automatically every N hours
# Usage: python scraper.py --schedule
# ---------------------------------------------------------------

import sys

def run_pipeline():
    """
    Full pipeline: scrape → clean → export
    Called by the scheduler every N hours
    """
    from cleaner  import load_raw_data, clean_data, save_clean_data
    from exporter import load_clean_data, export_csv, export_excel

    print(f"\n{'='*55}")
    print(f"  Auto-run started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    # Step 1: Scrape
    df_raw = scrape_internshala(max_pages=5)
    if df_raw.empty:
        print("❌ Scraping failed — aborting pipeline")
        return

    # Step 2: Clean
    df_clean = clean_data(df_raw)
    save_clean_data(df_clean)

    # Step 3: Export
    export_csv(df_clean)
    export_excel(df_clean)

    print(f"\n✅ Pipeline complete at {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Next run in {SCHEDULE_HOURS} hour(s)")


def run_scheduler(hours=6):
    """
    Runs the full pipeline immediately, then repeats every N hours.
    Keeps running until you press Ctrl+C.
    """
    global SCHEDULE_HOURS
    SCHEDULE_HOURS = hours

    print(f"⏰ Scheduler started — running every {hours} hour(s)")
    print(f"   Press Ctrl+C to stop\n")

    while True:
        run_pipeline()
        # Sleep for N hours (converted to seconds)
        sleep_seconds = hours * 3600
        print(f"\n💤 Sleeping for {hours} hour(s)... (Ctrl+C to stop)")
        time.sleep(sleep_seconds)


# Handle command line argument
if len(sys.argv) > 1 and sys.argv[1] == '--schedule':
    run_scheduler(hours=6)   # change hours=6 to any interval you want            