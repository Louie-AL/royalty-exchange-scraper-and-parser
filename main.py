from parser import (
    parse_html, 
    parse_offers, 
    parse_monthly_revenues, 
    parse_income_types_melted,
    parse_full_listing,
    parse_youtube_link
)
from scraper import init_driver, get_html_from_asset, get_json_from_api
from utils import delay, setup_logger
import pandas as pd
import csv


FINANCIALS_OUTPUT = "financials.csv"
OFFERS_OUTPUT = "offers.csv"

def read_asset_ids_from_csv(path: str) -> list:
    with open(path, "r") as f:
        return [int(row["asset_id"]) for row in csv.DictReader(f)]

logger = setup_logger()

all_monthly_revenue = []
all_income_types = []
all_full_listings = []

def main(asset_ids):
    all_financials = []
    all_offers = []

    driver = init_driver()  # Initialize driver once

    for aid in asset_ids:
        try:
            logger.info(f"Processing asset {aid}")
            html = get_html_from_asset(aid, driver)
            json_data = get_json_from_api(aid)
            print(f"[{aid}] earnings_file key present:", "earnings_file" in json_data.get("listing", {}))

            monthly = parse_monthly_revenues(json_data, aid)
            if not monthly.empty:
                all_monthly_revenue.append(monthly)

            melted = parse_income_types_melted(json_data, aid)
            if not melted.empty:
                all_income_types.append(melted)

            full_listing = parse_full_listing(json_data, aid)
            all_full_listings.append(full_listing)

            financial_data = parse_html(html)
            financial_data["Asset ID"] = aid
            all_financials.append(financial_data)

            offers = parse_offers(json_data, aid)
            all_offers.extend(offers)

            youtube_link = parse_youtube_link(html)
            financial_data["YouTube Link"] = youtube_link

            delay()

        except Exception as e:
            logger.error(f"Failed to process asset {aid}: {e}")

    driver.quit()  # Close driver at the end

    pd.DataFrame(all_financials).to_csv(FINANCIALS_OUTPUT, index=False)
    pd.DataFrame(all_offers).to_csv(OFFERS_OUTPUT, index=False)
    pd.DataFrame(all_full_listings).to_csv("raw_listing_data.csv", index=False)

    print(f"Monthly revenue collected for {len(all_monthly_revenue)} assets.")
    print(f"Income types collected for {len(all_income_types)} assets.")

    if all_monthly_revenue:
        pd.concat(all_monthly_revenue).to_csv("earnings.csv", index=False)

    if all_income_types:
        pd.concat(all_income_types).to_csv("income_types_melted.csv", index=False)

    logger.info("Scraping completed successfully.")

if __name__ == "__main__":
    asset_ids = read_asset_ids_from_csv("asset_ids.csv")
    main(asset_ids)
