# 💼 JobScrapeX

A full-stack web scraping project that scrapes internship listings from 
Internshala, cleans and filters the data, exports to CSV/Excel, and 
displays everything on an interactive Streamlit dashboard.

> Built as a portfolio project by a 3rd year B.E. CS&IT student.

---

## 🖥️ Dashboard Preview

![JobScrapeX Dashboard](assets/dashboard.png)

---

## ✨ Features

- 🔍 **Scrapes real internship data** from Internshala's internal AJAX API
- 📊 **200+ listings** across 5 pages with 9 fields per listing
- 🧹 **Data cleaning** — stipend parsing, deduplication, standardisation
- 🔎 **4 filter types** — keyword, location, stipend range, duration
- 📁 **Dual export** — formatted Excel (with charts) + CSV
- 📈 **Live dashboard** — built with Streamlit, updates on demand
- ⏰ **Auto-scheduler** — re-scrapes every N hours automatically

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| BeautifulSoup4 | HTML parsing |
| Requests | HTTP requests |
| Pandas | Data manipulation |
| Streamlit | Dashboard UI |
| openpyxl / XlsxWriter | Excel export |
| GitHub | Version control |

---

## 📁 Project Structure

```
JobScrapeX/
├── scraper.py        # Scraping logic — hits Internshala AJAX API
├── cleaner.py        # Data cleaning + filter functions
├── exporter.py       # CSV + formatted Excel export
├── app.py            # Streamlit dashboard
├── data/             # Output folder (gitignored)
├── requirements.txt  # All dependencies
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/JobScrapeX.git
cd JobScrapeX
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Scrape data
```bash
python scraper.py
```

### 4. Clean and export
```bash
python cleaner.py
python exporter.py
```

### 5. Launch dashboard
```bash
streamlit run app.py
```

---

## 📊 Sample Data

| Title | Company | Location | Stipend | Duration |
|---|---|---|---|---|
| Python Developer | TechCorp | Mumbai | ₹10,000 - 15,000/month | 3 Months |
| Data Analyst | Analytics Co | Bangalore | ₹15,000/month | 6 Months |
| UI/UX Designer | DesignHub | Work from Home | ₹8,000 - 12,000/month | 3 Months |

---

## ⚙️ Configuration

In `scraper.py`, change these variables to customise scraping:

```python
MAX_PAGES = 5          # number of pages to scrape (~40 listings/page)
SLEEP_BETWEEN_PAGES = 2  # seconds between requests (be polite!)
```

Run with auto-scheduler (re-scrapes every 6 hours):
```bash
python scraper.py --schedule
```

---

## 🔍 How It Works

Internshala uses JavaScript to render listings dynamically. Instead of 
using Selenium, this project intercepts their internal AJAX endpoint:

```
GET https://internshala.com/internships/ajax/search/page-{n}
```

This returns HTML fragments which BeautifulSoup parses to extract all 
fields. Pagination is handled by incrementing the page number.

---

## 📦 Requirements

```
requests==2.31.0
beautifulsoup4==4.12.3
pandas==2.2.1
streamlit==1.33.0
openpyxl==3.1.2
lxml==5.2.1
xlsxwriter==3.2.0
```

---

## 👩‍💻 Author
**Khushi Kapadia** — B.E. Computer Science & IT, 3rd Year
[GitHub](https://github.com/Khushikapadia5125)

---

## 📄 License

© 2026 Khushi Kapadia. All rights reserved.
This project is for portfolio/viewing purposes only.
Copying, modifying, or redistributing is not permitted.