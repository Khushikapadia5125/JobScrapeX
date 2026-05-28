# app.py
# ---------------------------------------------------------------
# JobScrapeX — Day 9-10
# Streamlit dashboard for browsing internship listings
# Run with: streamlit run app.py
# ---------------------------------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from cleaner import (
    load_raw_data, clean_data, save_clean_data,
    filter_by_keyword, filter_by_location,
    filter_by_stipend, filter_by_duration
)
from scraper import scrape_internshala
from exporter import export_csv, export_excel

# ---------------------------------------------------------------
# PAGE CONFIG — must be the very first Streamlit call
# ---------------------------------------------------------------

st.set_page_config(
    page_title="JobScrapeX",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------
# CUSTOM CSS — makes it look polished
# ---------------------------------------------------------------

st.markdown("""
<style>
    /* Main background */
    .main { background-color: #f8f9fa; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Sidebar background only */
    [data-testid="stSidebar"] {
        background-color: #1F3864;
    }

    /* Sidebar plain text and labels → white */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] markdown,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #ffffff !important;
        font-weight: 600;
    }

    /* Sidebar input boxes → white background, dark text */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background-color: #ffffff !important;
        color: #1F3864 !important;
        border-radius: 6px !important;
    }

    /* Sidebar selectbox → white background, dark text */
    [data-testid="stSidebar"] [data-baseweb="select"] {
        background-color: #ffffff !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        background-color: #ffffff !important;
        color: #1F3864 !important;
    }

    /* Sidebar selectbox dropdown options */
    [data-baseweb="popover"] * {
        color: #1F3864 !important;
        background-color: #ffffff !important;
    }

    /* Sidebar slider track label text */
    [data-testid="stSidebar"] [data-testid="stSlider"] div,
    [data-testid="stSidebar"] [data-testid="stSlider"] p,
    [data-testid="stSidebar"] [data-testid="stSlider"] span {
        color: #ffffff !important;
    }

    /* Download buttons → white bg, dark text, fully visible */
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button {
        background-color: #ffffff !important;
        color: #1F3864 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        width: 100% !important;
        padding: 10px !important;
    }
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button p {
        color: #1F3864 !important;
    }
    [data-testid="stSidebar"] [data-testid="stDownloadButton"] button:hover {
        background-color: #e8f0fe !important;
    }

    /* Scrape Now button → keep gradient */
    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background: linear-gradient(135deg, #2E75B6, #4a9fd4) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        width: 100% !important;
        padding: 10px !important;
    }
    [data-testid="stSidebar"] [data-testid="stButton"] button p {
        color: #ffffff !important;
    }

    /* Header banner */
    .header-banner {
        background: linear-gradient(135deg, #1F3864 0%, #2E75B6 100%);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .header-banner h1 { color: white !important; margin: 0; font-size: 2rem; }
    .header-banner p  { color: #cce4ff !important; margin: 5px 0 0 0; font-size: 0.95rem; }

    /* Job cards */
    .job-card {
        background: white;
        border: 1px solid #e8eaf0;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .job-title   { font-size: 1.05rem; font-weight: 700; color: #1F3864; margin-bottom: 2px; }
    .job-company { font-size: 0.9rem; color: #555; margin-bottom: 8px; }
    .job-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .badge-location { background: #e8f0fe; color: #1a56db; }
    .badge-stipend  { background: #e6f4ea; color: #1e7e34; }
    .badge-duration { background: #fef3e2; color: #c47d0e; }
    .badge-date     { background: #fce8f3; color: #9c27b0; }

    /* Skills tags */
    .skill-tag {
        display: inline-block;
        background: #f0f4f8;
        color: #444;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin: 2px 3px 2px 0;
        border: 1px solid #dde3ea;
    }

    /* Section title */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1F3864;
        border-left: 4px solid #2E75B6;
        padding-left: 10px;
        margin: 20px 0 12px 0;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------
# DATA LOADING — with caching so it doesn't reload every click
# ---------------------------------------------------------------

@st.cache_data(ttl=300)   # cache for 5 minutes, then auto-refresh
def load_data():
    """
    Load and clean data. Uses cache so the dashboard stays fast.
    ttl=300 means cached data expires after 5 minutes.
    """
    raw = load_raw_data('data/internships_raw.csv')
    if raw is None or raw.empty:
        return pd.DataFrame(), None

    df = clean_data(raw)

    # Get last scraped time from the data itself
    if 'Scraped At' in df.columns:
        last_scraped = df['Scraped At'].max()
    else:
        last_scraped = 'Unknown'

    return df, last_scraped


def get_filter_options(df):
    """Extract unique values for filter dropdowns"""
    locations = sorted(df['Location'].dropna().unique().tolist())
    durations = sorted(
        df['Duration'].dropna().unique().tolist(),
        key=lambda x: float(str(x).split()[0]) if str(x).split()[0].replace('.','').isdigit() else 99
    )
    return locations, durations


# ---------------------------------------------------------------
# SCRAPE FRESH DATA — triggered by button click
# ---------------------------------------------------------------

def run_fresh_scrape(pages=5):
    """
    Runs the full scrape → clean → save pipeline.
    Called when user clicks 'Scrape Now' button.
    """
    with st.spinner(f'Scraping {pages} pages from Internshala... (this takes ~{pages*2}s)'):
        df_raw = scrape_internshala(max_pages=pages)

    if df_raw.empty:
        st.error("Scraping failed. Check your internet connection.")
        return False

    with st.spinner('Cleaning data...'):
        df_clean = clean_data(df_raw)
        save_clean_data(df_clean)
        export_csv(df_clean)

    # Clear cache so dashboard reloads with fresh data
    st.cache_data.clear()
    return True


# ---------------------------------------------------------------
# RENDER A SINGLE JOB CARD
# ---------------------------------------------------------------

def render_job_card(row):
    """Renders one internship as a styled HTML card"""

    title    = row.get('Title',    'N/A')
    company  = row.get('Company',  'N/A')
    location = row.get('Location', 'N/A')
    stipend  = row.get('Stipend',  'N/A')
    duration = row.get('Duration', 'N/A')
    skills   = row.get('Skills',   '')
    date     = row.get('Date Posted', '')
    link     = row.get('Link',     '#')

    # Build skills HTML
    skills_html = ''
    if pd.notna(skills) and skills and skills != 'N/A':
        skill_list = [s.strip() for s in str(skills).split(',')][:6]  # max 6 skills shown
        skills_html = ''.join([f'<span class="skill-tag">{s}</span>' for s in skill_list])
        if len(str(skills).split(',')) > 6:
            skills_html += '<span class="skill-tag">+more</span>'

    # Build badge for date
    date_badge = f'<span class="job-badge badge-date">🕐 {date}</span>' if date and date != 'N/A' else ''

    card_html = f"""
    <div class="job-card">
        <div class="job-title">{title}</div>
        <div class="job-company">🏢 {company}</div>
        <div>
            <span class="job-badge badge-location">📍 {location}</span>
            <span class="job-badge badge-stipend">💰 {stipend}</span>
            <span class="job-badge badge-duration">📅 {duration}</span>
            {date_badge}
        </div>
        {f'<div style="margin-top:8px">{skills_html}</div>' if skills_html else ''}
        <div style="margin-top:10px">
            <a href="{link}" target="_blank"
               style="color:#2E75B6; font-size:0.85rem; font-weight:600; text-decoration:none;">
               🔗 View on Internshala →
            </a>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


# ---------------------------------------------------------------
# CHARTS
# ---------------------------------------------------------------

def render_charts(df):
    """Renders the analytics charts section"""

    st.markdown('<div class="section-title">📊 Analytics</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Top 10 locations bar chart
        st.markdown("**Top Locations**")
        loc_counts = df['Location'].value_counts().head(10).reset_index()
        loc_counts.columns = ['Location', 'Count']
        st.bar_chart(loc_counts.set_index('Location'), color='#2E75B6')

    with col2:
        # Stipend distribution
        st.markdown("**Stipend Distribution (₹/month)**")
        stipend_data = df['Stipend_Avg'].dropna()
        if not stipend_data.empty:
            # Bin stipends into ranges
            bins   = [0, 5000, 10000, 15000, 20000, 30000, 50000, float('inf')]
            labels = ['<5k', '5-10k', '10-15k', '15-20k', '20-30k', '30-50k', '50k+']
            binned = pd.cut(stipend_data, bins=bins, labels=labels)
            dist   = binned.value_counts().sort_index().reset_index()
            dist.columns = ['Range', 'Count']
            st.bar_chart(dist.set_index('Range'), color='#1e7e34')

    col3, col4 = st.columns(2)

    with col3:
        # Duration breakdown
        st.markdown("**Duration Breakdown**")
        dur_counts = df['Duration'].value_counts().reset_index()
        dur_counts.columns = ['Duration', 'Count']
        st.bar_chart(dur_counts.set_index('Duration'), color='#c47d0e')

    with col4:
        # Top companies by listing count
        st.markdown("**Most Active Companies**")
        comp_counts = df['Company'].value_counts().head(8).reset_index()
        comp_counts.columns = ['Company', 'Listings']
        st.bar_chart(comp_counts.set_index('Company'), color='#9c27b0')


# ---------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------

def main():

    # --- Load data ---
    df, last_scraped = load_data()

    # ---------------------------------------------------------------
    # SIDEBAR
    # ---------------------------------------------------------------

    with st.sidebar:
        st.markdown("## 💼 JobScrapeX")
        st.markdown("---")

        # --- Scrape controls ---
        st.markdown("### 🔄 Refresh Data")
        pages_to_scrape = st.slider(
            "Pages to scrape",
            min_value=1,
            max_value=20,
            value=5,
            help="Each page has ~40 internships. More pages = more data but takes longer."
        )

        if st.button("🚀 Scrape Now"):
            success = run_fresh_scrape(pages=pages_to_scrape)
            if success:
                st.success("✅ Fresh data scraped!")
                st.rerun()   # reload the whole app with new data
            else:
                st.error("❌ Scrape failed")

        st.markdown("---")

        # Only show filters if data is loaded
        if df.empty:
            st.warning("No data yet. Click 'Scrape Now' to get started!")
            return

        # --- Filters ---
        st.markdown("### 🔍 Filters")

        # Keyword search
        keyword = st.text_input(
            "Search keyword",
            placeholder="e.g. Python, Marketing, Design...",
            help="Searches Title, Company and Skills"
        )

        # Location filter
        locations, durations = get_filter_options(df)
        location_options = ['All Locations'] + locations
        selected_location = st.selectbox("📍 Location", location_options)
        location_filter = None if selected_location == 'All Locations' else selected_location

        # Stipend filter
        st.markdown("💰 Minimum Stipend (₹/month)")
        min_stipend = st.select_slider(
            "min_stipend",
            options=[0, 2000, 3000, 5000, 8000, 10000, 15000, 20000, 30000, 50000],
            value=0,
            format_func=lambda x: f'₹{x:,}' if x > 0 else 'Any',
            label_visibility='collapsed'
        )

        # Duration filter
        duration_options = ['Any Duration'] + durations
        selected_duration = st.selectbox("📅 Max Duration", duration_options)
        duration_months = None
        if selected_duration != 'Any Duration':
            # Extract number from e.g. "3 Months" → 3
            try:
                duration_months = int(str(selected_duration).split()[0])
            except Exception:
                duration_months = None

        # Sort options
        st.markdown("---")
        st.markdown("### 📋 Sort By")
        sort_by = st.selectbox(
            "Sort",
            ['Stipend (High → Low)', 'Stipend (Low → High)',
             'Duration (Short first)', 'Company (A-Z)'],
            label_visibility='collapsed'
        )

        # Download section
        st.markdown("---")
        st.markdown("### 💾 Download")

        csv_path   = 'data/internships_clean.csv'
        excel_path = 'data/internships_export.xlsx'

        if os.path.exists(csv_path):
            with open(csv_path, 'rb') as f:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    file_name='internships.csv',
                    mime='text/csv'
                )

        if os.path.exists(excel_path):
            with open(excel_path, 'rb') as f:
                st.download_button(
                    label="⬇️ Download Excel",
                    data=f,
                    file_name='internships.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

    # ---------------------------------------------------------------
    # MAIN CONTENT AREA
    # ---------------------------------------------------------------

    if df.empty:
        st.markdown("""
        <div class="header-banner">
            <h1>💼 JobScrapeX</h1>
            <p>No data found. Click "Scrape Now" in the sidebar to get started!</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # --- Apply filters ---
    filtered_df = df.copy()

    if keyword and keyword.strip():
        kw = keyword.lower().strip()
        mask = (
            filtered_df['Title'].fillna('').str.lower().str.contains(kw) |
            filtered_df['Company'].fillna('').str.lower().str.contains(kw) |
            filtered_df['Skills'].fillna('').str.lower().str.contains(kw)
        )
        filtered_df = filtered_df[mask]

    if location_filter:
        filtered_df = filtered_df[
            filtered_df['Location'].fillna('').str.lower().str.contains(location_filter.lower())
        ]

    if min_stipend > 0:
        filtered_df = filtered_df[
            filtered_df['Stipend_Min'].fillna(0) >= min_stipend
        ]

    if duration_months:
        filtered_df = filtered_df[
            filtered_df['Duration_Months'].fillna(99) <= duration_months
        ]

    # --- Apply sort ---
    if sort_by == 'Stipend (High → Low)':
        filtered_df = filtered_df.sort_values('Stipend_Avg', ascending=False, na_position='last')
    elif sort_by == 'Stipend (Low → High)':
        filtered_df = filtered_df.sort_values('Stipend_Avg', ascending=True, na_position='last')
    elif sort_by == 'Duration (Short first)':
        filtered_df = filtered_df.sort_values('Duration_Months', ascending=True, na_position='last')
    elif sort_by == 'Company (A-Z)':
        filtered_df = filtered_df.sort_values('Company', ascending=True)

    # ---------------------------------------------------------------
    # HEADER BANNER
    # ---------------------------------------------------------------

    st.markdown(f"""
    <div class="header-banner">
        <h1>💼 JobScrapeX</h1>
        <p>Internship listings scraped from Internshala &nbsp;|&nbsp;
           Last scraped: <strong>{last_scraped}</strong> &nbsp;|&nbsp;
           Built with Python + BeautifulSoup + Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------------
    # METRIC CARDS ROW
    # ---------------------------------------------------------------

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("📋 Total Scraped", len(df))
    with m2:
        st.metric("🔍 Matching Filters", len(filtered_df))
    with m3:
        st.metric("🏢 Companies", filtered_df['Company'].nunique())
    with m4:
        avg = filtered_df['Stipend_Avg'].mean()
        st.metric("💰 Avg Stipend", f"₹{avg:,.0f}" if pd.notna(avg) else "N/A")
    with m5:
        wfh = (filtered_df['Location'] == 'Work from Home').sum()
        st.metric("🏠 Work from Home", wfh)

    st.markdown("---")

    # ---------------------------------------------------------------
    # TABS: Listings | Analytics | Raw Table
    # ---------------------------------------------------------------

    tab1, tab2, tab3 = st.tabs(["📋 Listings", "📊 Analytics", "🗃️ Raw Table"])

    # ---------------------------------------------------------------
    # TAB 1: JOB LISTINGS (card view)
    # ---------------------------------------------------------------

    with tab1:
        if filtered_df.empty:
            st.info("No internships match your current filters. Try adjusting them.")
        else:
            st.markdown(
                f'<div class="section-title">Showing {len(filtered_df)} internships</div>',
                unsafe_allow_html=True
            )

            # Pagination — show 15 cards per page
            CARDS_PER_PAGE = 15
            total_pages = max(1, -(-len(filtered_df) // CARDS_PER_PAGE))  # ceiling division

            if total_pages > 1:
                page_num = st.number_input(
                    f"Page (1–{total_pages})",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    step=1
                )
            else:
                page_num = 1

            start_idx = (page_num - 1) * CARDS_PER_PAGE
            end_idx   = start_idx + CARDS_PER_PAGE
            page_data = filtered_df.iloc[start_idx:end_idx]

            for _, row in page_data.iterrows():
                render_job_card(row.to_dict())

            if total_pages > 1:
                st.markdown(f"*Page {page_num} of {total_pages} — {len(filtered_df)} total results*")

    # ---------------------------------------------------------------
    # TAB 2: ANALYTICS CHARTS
    # ---------------------------------------------------------------

    with tab2:
        if filtered_df.empty:
            st.info("No data to chart with current filters.")
        else:
            render_charts(filtered_df)

    # ---------------------------------------------------------------
    # TAB 3: RAW DATA TABLE
    # ---------------------------------------------------------------

    with tab3:
        st.markdown(
            f'<div class="section-title">Raw Data — {len(filtered_df)} rows</div>',
            unsafe_allow_html=True
        )

        # Columns to show in table (hide internal numeric columns by default)
        display_cols = ['Title', 'Company', 'Location', 'Stipend',
                        'Duration', 'Skills', 'Date Posted']
        display_cols = [c for c in display_cols if c in filtered_df.columns]

        st.dataframe(
            filtered_df[display_cols],
            use_container_width=True,
            height=500,
            column_config={
                'Title':       st.column_config.TextColumn('Title', width='medium'),
                'Company':     st.column_config.TextColumn('Company', width='medium'),
                'Location':    st.column_config.TextColumn('Location', width='small'),
                'Stipend':     st.column_config.TextColumn('Stipend', width='medium'),
                'Duration':    st.column_config.TextColumn('Duration', width='small'),
                'Skills':      st.column_config.TextColumn('Skills', width='large'),
                'Date Posted': st.column_config.TextColumn('Posted', width='small'),
            }
        )

        # Download filtered results directly from table
        csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="⬇️ Download this filtered view as CSV",
            data=csv_data,
            file_name=f'jobscrapex_filtered_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
            mime='text/csv'
        )


# ---------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------

if __name__ == '__main__':
    main()