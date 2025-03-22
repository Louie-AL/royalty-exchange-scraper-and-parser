# Royalty Exchange Web Scraper

This project is a modular and scalable web scraper designed to collect and organize structured data from the Royalty Exchange auction platform. It extracts key financial information, offer history, and earnings data for various royalty listings.

## 📁 Project Structure

```
royalty_scraper/
├── main.py                  # Orchestrates the scraping process
├── parser.py                # Parses HTML and JSON into structured data
├── scraper.py               # Fetches HTML pages and JSON from API
├── utils.py                 # Logging and helper utilities
├── config.py                # Output file paths and default asset IDs
├── test/                    # Unit tests (if needed)
├── financials.csv           # Output: Financial metadata per listing
├── offers.csv               # Output: Offers made per listing
├── earnings.csv             # Output: Monthly earnings (if available)
├── income_types_melted.csv  # Output: Detailed earnings breakdown
├── asset_ids.csv            # Optional: Custom input list of asset IDs
└── README.md                # This file
```

## ⚙️ What It Does

For each asset ID:
- Scrapes the listing page (HTML)
- Pulls associated data from JSON API
- Extracts:
  - Financial info (e.g., sale price, earnings history, multiples)
  - Offer data (timestamps, bid amounts, investor IDs)
  - Monthly earnings and income type breakdowns (if available)
- Outputs results to CSV files

## 📦 Features

- Modular code for scraping, parsing, and running
- Parses both HTML and JSON data
- Error handling and logging for traceability
- Can scale to many asset IDs
- Custom input via `asset_ids.csv`

## 🧠 Skills Demonstrated

- Web scraping (Selenium + Requests)
- API reverse engineering via browser dev tools
- HTML parsing with BeautifulSoup
- JSON extraction and transformation
- Data wrangling with Pandas
- Modular Python scripting
- Logging and basic testing structure

## 🗃️ Input Format (asset_ids.csv)

If you want to specify your own list of assets, create a CSV file like:

```
asset_id
6122
6089
6094
```

Place it in the root folder. The program will automatically read from it.

## 🚀 Running the Project

From the terminal:

```bash
python main.py
```

It will:
- Read asset IDs
- Collect data
- Save outputs in CSV files

## 📌 Notes

- Make sure your environment has `selenium`, `bs4`, `pandas`, and `requests` installed.
- Requires Microsoft Edge + Edge WebDriver.