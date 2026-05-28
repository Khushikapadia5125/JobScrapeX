# cleaner.py
# ---------------------------------------------------------------
# JobScrapeX — Day 5-6
# Cleans raw scraped data + applies filters
# Input:  data/internships_raw.csv
# Output: data/internships_clean.csv
# ---------------------------------------------------------------

import pandas as pd
import numpy as np
import os
import re

# ---------------------------------------------------------------
# STEP 1: LOAD RAW DATA
# ---------------------------------------------------------------

def load_raw_data(path='data/internships_raw.csv'):
    """Load the CSV saved by scraper.py"""
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        print("   Run scraper.py first!")
        return None

    df = pd.read_csv(path)
    print(f"✅ Loaded {len(df)} rows from {path}")
    print(f"   Columns: {list(df.columns)}")
    return df


# ---------------------------------------------------------------
# STEP 2: CLEANING FUNCTIONS — one per field
# ---------------------------------------------------------------

def clean_title(df):
    """
    - Strip extra whitespace
    - Title case (e.g. 'python developer' → 'Python Developer')
    - Replace N/A with NaN so pandas can handle it properly
    """
    df['Title'] = df['Title'].str.strip()
    df['Title'] = df['Title'].str.title()
    df['Title'] = df['Title'].replace('N/A', np.nan)
    return df


def clean_company(df):
    """
    - Strip whitespace
    - Remove common suffixes noise like extra spaces
    """
    df['Company'] = df['Company'].str.strip()
    df['Company'] = df['Company'].replace('N/A', np.nan)
    return df


def clean_location(df):
    """
    - Strip whitespace
    - Standardise 'Work from home' → 'Work from Home' (consistent casing)
    - Replace N/A with NaN
    """
    df['Location'] = df['Location'].str.strip()

    # Standardise all variations of WFH to one consistent label
    wfh_variants = ['work from home', 'wfh', 'remote', 'work from home (wfh)']
    df['Location'] = df['Location'].apply(
        lambda x: 'Work from Home' if str(x).lower() in wfh_variants else x
    )

    df['Location'] = df['Location'].replace('N/A', np.nan)
    return df


def parse_stipend(stipend_str):
    """
    Converts stipend string to min and max numeric values.

    Examples:
      '₹ 12,000 - 18,000 /month'  → (12000, 18000)
      '₹ 10,000 /month'           → (10000, 10000)  ← fixed amount
      'Unpaid'                     → (0, 0)
      'N/A'                        → (NaN, NaN)

    Why separate min/max?
    → So you can filter "show me internships paying at least ₹8000"
      You need a number to compare, not a string like "₹ 5,000 - 10,000"
    """
    if pd.isna(stipend_str) or str(stipend_str).strip() in ['N/A', '', 'Unpaid']:
        if str(stipend_str).strip() == 'Unpaid':
            return 0, 0
        return np.nan, np.nan

    s = str(stipend_str)

    # Remove ₹, commas, /month, spaces — keep only digits and hyphens
    # re.sub replaces all characters NOT in our keep-list with a space
    s_clean = re.sub(r'[₹,/month\s]', '', s)
    # Now s_clean looks like: '12000-18000' or '10000'

    # Check if it's a range (has a hyphen between two numbers)
    range_match = re.findall(r'\d+', s_clean)
    # re.findall(r'\d+', ...) extracts ALL sequences of digits as a list
    # '12000-18000' → ['12000', '18000']
    # '10000'       → ['10000']

    if len(range_match) >= 2:
        return int(range_match[0]), int(range_match[1])
    elif len(range_match) == 1:
        val = int(range_match[0])
        return val, val   # fixed stipend: min == max
    else:
        return np.nan, np.nan


def clean_stipend(df):
    """
    Splits Stipend string into three columns:
    - Stipend_Min (int): minimum monthly stipend in ₹
    - Stipend_Max (int): maximum monthly stipend in ₹
    - Stipend_Avg (int): average of min and max — useful for sorting
    """
    # Apply parse_stipend to every row, get back two values
    parsed = df['Stipend'].apply(lambda x: pd.Series(parse_stipend(x)))
    df['Stipend_Min'] = parsed[0].astype('Int64')  # Int64 (capital I) supports NaN in integers
    df['Stipend_Max'] = parsed[1].astype('Int64')
    df['Stipend_Avg'] = ((df['Stipend_Min'] + df['Stipend_Max']) / 2).astype('Int64')

    return df


def parse_duration_to_months(duration_str):
    """
    Converts duration string to number of months for easy sorting/filtering.

    Examples:
      '6 Months' → 6
      '3 Months' → 3
      '1 Week'   → 0  (less than a month, store as 0)
      '24 Months'→ 24
      'N/A'      → NaN
    """
    if pd.isna(duration_str) or str(duration_str).strip() == 'N/A':
        return np.nan

    s = str(duration_str).lower().strip()

    # Extract the number from the string
    num_match = re.search(r'\d+', s)
    if not num_match:
        return np.nan

    num = int(num_match.group())

    if 'week' in s:
        return 0           # less than 1 month
    elif 'month' in s:
        return num
    elif 'year' in s:
        return num * 12    # convert years to months
    else:
        return num         # assume months if unit unclear


def clean_duration(df):
    """
    Keeps original Duration string AND adds Duration_Months for numeric filtering
    """
    df['Duration'] = df['Duration'].str.strip()
    df['Duration'] = df['Duration'].replace('N/A', np.nan)
    df['Duration_Months'] = df['Duration'].apply(parse_duration_to_months)
    return df


def clean_date_posted(df):
    """
    Standardise date posted values.
    Your data has: 'Actively hiring', '1 day ago', '2 days ago', '3 days ago'
    We keep as-is but strip whitespace and replace N/A
    """
    df['Date Posted'] = df['Date Posted'].str.strip()
    df['Date Posted'] = df['Date Posted'].replace('N/A', np.nan)
    return df


def clean_skills(df):
    """
    Skills are currently all empty (0/210).
    Column contains NaN (float) so we can't use .str directly.
    Convert to string first, then clean.
    """
    # fillna first so we're working with strings, not floats
    df['Skills'] = df['Skills'].fillna('N/A')
    df['Skills'] = df['Skills'].astype(str).str.strip()
    df['Skills'] = df['Skills'].replace('N/A', np.nan)
    return df

def remove_duplicates(df):
    """
    Remove duplicate internships.
    We use Link as the unique identifier — same URL = same listing.
    If Link is N/A, fall back to Title+Company combination.
    """
    before = len(df)

    # First deduplicate by Link (most reliable)
    df = df.drop_duplicates(subset=['Link'], keep='first')

    # Then deduplicate by Title + Company (catches same job with slightly different links)
    df = df.drop_duplicates(subset=['Title', 'Company'], keep='first')

    after = len(df)
    removed = before - after
    if removed > 0:
        print(f"  🗑️  Removed {removed} duplicate listings")
    else:
        print(f"  ✅ No duplicates found")
    return df


# ---------------------------------------------------------------
# STEP 3: MASTER CLEAN FUNCTION — runs all cleaners in order
# ---------------------------------------------------------------

def clean_data(df):
    """
    Runs all cleaning steps in sequence.
    Returns a clean, structured DataFrame.
    """
    print("\n--- Running Data Cleaning ---")

    df = clean_title(df)
    print("  ✅ Title cleaned")

    df = clean_company(df)
    print("  ✅ Company cleaned")

    df = clean_location(df)
    print("  ✅ Location cleaned")

    df = clean_stipend(df)
    print("  ✅ Stipend parsed → Stipend_Min, Stipend_Max, Stipend_Avg added")

    df = clean_duration(df)
    print("  ✅ Duration parsed → Duration_Months added")

    df = clean_date_posted(df)
    print("  ✅ Date Posted cleaned")

    df = clean_skills(df)
    print("  ✅ Skills cleaned")

    df = remove_duplicates(df)

    # Reorder columns logically
    column_order = [
        'Title', 'Company', 'Location',
        'Stipend', 'Stipend_Min', 'Stipend_Max', 'Stipend_Avg',
        'Duration', 'Duration_Months',
        'Skills', 'Date Posted',
        'Link', 'Scraped At'
    ]
    # Only keep columns that actually exist (in case some are missing)
    column_order = [c for c in column_order if c in df.columns]
    df = df[column_order]

    print(f"\n  📊 Clean dataset: {len(df)} rows × {len(df.columns)} columns")
    return df


# ---------------------------------------------------------------
# STEP 4: FILTER FUNCTIONS
# ---------------------------------------------------------------

def filter_by_keyword(df, keyword):
    """
    Filter internships where Title OR Company OR Skills contains the keyword.
    Case-insensitive search.

    Example: filter_by_keyword(df, 'python')
    → returns all rows where 'python' appears in title, company, or skills
    """
    if not keyword or keyword.strip() == '':
        return df

    keyword = keyword.lower().strip()

    # Check each relevant column — use fillna('') so NaN doesn't cause errors
    mask = (
        df['Title'].fillna('').str.lower().str.contains(keyword) |
        df['Company'].fillna('').str.lower().str.contains(keyword) |
        df['Skills'].fillna('').str.lower().str.contains(keyword)
    )
    result = df[mask]
    print(f"  🔍 Keyword '{keyword}': {len(result)} matches")
    return result


def filter_by_location(df, location):
    """
    Filter by location. Case-insensitive, partial match.

    Example: filter_by_location(df, 'mumbai')
    Example: filter_by_location(df, 'work from home')
    """
    if not location or location.strip() == '':
        return df

    location = location.lower().strip()
    mask = df['Location'].fillna('').str.lower().str.contains(location)
    result = df[mask]
    print(f"  📍 Location '{location}': {len(result)} matches")
    return result


def filter_by_stipend(df, min_stipend=0, max_stipend=None):
    """
    Filter by stipend range using the numeric Stipend_Min column.

    Logic: show internships where Stipend_Min >= min_stipend
    Optional: also apply a max cap.

    Example: filter_by_stipend(df, min_stipend=8000)
    → shows all internships paying at least ₹8,000/month
    """
    # Start with rows that have a valid stipend number
    mask = df['Stipend_Min'].notna()

    # Apply minimum filter
    if min_stipend > 0:
        mask = mask & (df['Stipend_Min'] >= min_stipend)

    # Apply maximum filter if specified
    if max_stipend is not None:
        mask = mask & (df['Stipend_Max'] <= max_stipend)

    result = df[mask]
    max_label = f" - ₹{max_stipend:,}" if max_stipend else "+"
    print(f"  💰 Stipend ₹{min_stipend:,}{max_label}/month: {len(result)} matches")
    return result


def filter_by_duration(df, max_months):
    """
    Filter internships up to a maximum duration.

    Example: filter_by_duration(df, max_months=3)
    → shows only 1-3 month internships
    """
    mask = df['Duration_Months'].notna() & (df['Duration_Months'] <= max_months)
    result = df[mask]
    print(f"  📅 Duration ≤ {max_months} months: {len(result)} matches")
    return result


def apply_all_filters(df, keyword=None, location=None,
                      min_stipend=0, max_stipend=None, max_duration=None):
    """
    Convenience function: apply multiple filters at once.
    Any filter left as None is skipped.

    Example:
        apply_all_filters(df,
            keyword='python',
            location='mumbai',
            min_stipend=8000
        )
    """
    print("\n--- Applying Filters ---")
    filtered = df.copy()

    if keyword:
        filtered = filter_by_keyword(filtered, keyword)
    if location:
        filtered = filter_by_location(filtered, location)
    if min_stipend or max_stipend:
        filtered = filter_by_stipend(filtered, min_stipend, max_stipend)
    if max_duration:
        filtered = filter_by_duration(filtered, max_duration)

    print(f"\n  ✅ Final result: {len(filtered)} internships match all filters")
    return filtered


# ---------------------------------------------------------------
# STEP 5: SAVE CLEAN DATA
# ---------------------------------------------------------------

def save_clean_data(df, path='data/internships_clean.csv'):
    """Save the cleaned + filtered DataFrame to CSV"""
    os.makedirs('data', exist_ok=True)
    df.to_csv(path, index=False, encoding='utf-8-sig')
    print(f"\n✅ Saved clean data to: {path}")
    print(f"   {len(df)} rows × {len(df.columns)} columns")

# ---------------------------------------------------------------
# STEP 6: SUMMARY REPORT — useful to verify data quality
# ---------------------------------------------------------------

def print_summary(df):
    """Prints a clean summary of the dataset"""
    print("\n" + "=" * 55)
    print("  DATA SUMMARY")
    print("=" * 55)
    print(f"  Total internships:    {len(df)}")
    print(f"  Unique companies:     {df['Company'].nunique()}")
    print(f"  Unique locations:     {df['Location'].nunique()}")
    print(f"  Work from Home:       {(df['Location'] == 'Work from Home').sum()}")
    print(f"  With stipend data:    {df['Stipend_Min'].notna().sum()}")

    if df['Stipend_Avg'].notna().any():
        avg = df['Stipend_Avg'].mean()
        print(f"  Average stipend:      ₹{avg:,.0f}/month")
        print(f"  Highest stipend:      ₹{df['Stipend_Max'].max():,}/month")

    print(f"\n  Top 5 Locations:")
    for loc, count in df['Location'].value_counts().head(5).items():
        print(f"    {loc:<25} {count} internships")

    print(f"\n  Duration breakdown:")
    for dur, count in df['Duration'].value_counts().items():
        print(f"    {str(dur):<15} {count} internships")

    print("=" * 55)

# ---------------------------------------------------------------
# RUN
# ---------------------------------------------------------------

if __name__ == '__main__':

    # 1. Load raw scraped data
    df = load_raw_data()
    if df is None:
        exit()

    # 2. Clean everything
    df_clean = clean_data(df)

    # 3. Print summary of clean data
    print_summary(df_clean)

    # 4. Save clean data
    save_clean_data(df_clean)

    # ---------------------------------------------------------------
    # 5. FILTER EXAMPLES — try these out!
    # ---------------------------------------------------------------
    print("\n" + "=" * 55)
    print("  FILTER DEMOS")
    print("=" * 55)

    # Example A: Python internships anywhere
    python_jobs = apply_all_filters(df_clean, keyword='python')
    print(python_jobs[['Title', 'Company', 'Location', 'Stipend']].head(3).to_string())

    # Example B: Ahmedabad internships paying ₹8,000+
    ahmedabad_jobs = apply_all_filters(
        df_clean,
        location='ahmedabad',
        min_stipend=8000
    )
    print(ahmedabad_jobs[['Title', 'Company', 'Stipend']].head(3).to_string())

    # Example C: Short internships (≤3 months) paying ₹10,000+
    short_paid = apply_all_filters(
        df_clean,
        min_stipend=10000,
        max_duration=3
    )
    print(short_paid[['Title', 'Company', 'Duration', 'Stipend']].head(3).to_string())

    # Save filtered result to a separate file
    save_clean_data(python_jobs, path='data/filtered_python.csv')