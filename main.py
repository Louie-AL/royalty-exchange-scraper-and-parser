from parser import (
    parse_html, 
    parse_offers, 
    parse_monthly_revenues, 
    parse_income_types_melted,
    parse_full_listing,
    parse_youtube_link,
    extract_next_data
)

from parser_pa import (
    parse_pa_financials,
    parse_pa_offers,
    parse_pa_raw_listing
)

from scraper import init_driver, get_html_from_asset, get_json_from_api, get_html_from_url
from utils import delay, setup_logger
import pandas as pd
import csv


FINANCIALS_OUTPUT = "financials.csv"
OFFERS_OUTPUT = "offers.csv"

def read_asset_ids_from_csv(path: str) -> list:
    with open(path, "r") as f:
        return [int(row["asset_id"]) for row in csv.DictReader(f)]

def read_pa_assets(path: str) -> list[dict]:
    """
    Returns list of {'asset_id': int, 'URL': str}.
    """
    return pd.read_csv(path, dtype={"asset_id":int, "URL":str}).to_dict(orient="records")

logger = setup_logger()

all_monthly_revenue = []
all_income_types = []
all_full_listings = []

def main(asset_ids, pa_assets):
    all_financials = []
    all_offers = []

    driver = init_driver()  # Initialize driver once

    # 1) Separate “new” vs “PAFlow” IDs
    pa_ids = {rec["asset_id"] for rec in pa_assets}
    std_ids = [ aid for aid in asset_ids if aid not in pa_ids]

    logger.info(f"Will JSON+HTML parse {len(std_ids)} new assets, and HTML‐only parse {len(pa_assets)} old assets")

    for aid in std_ids:
    # 2) JSON + HTML scrape for the “new” assets
        try:
            logger.info(f"Processing asset {aid}")
            html = get_html_from_asset(aid, driver)
            json_data = get_json_from_api(aid)
            if not json_data:
                continue
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

    # 3) HTML‐only scrape for your PAFlow (“old”) assets
    for rec in pa_assets:
        aid, url = rec["asset_id"], rec["URL"]
        try:
            html = get_html_from_url(url, driver)

            fin = parse_pa_financials(html)
            fin["Asset ID"] = aid
            all_financials.append(fin)

            offers = parse_pa_offers(html, aid)
            all_offers.extend(offers)

            full_listing = parse_pa_raw_listing(html, aid)
            all_full_listings.append(full_listing)
            # So far, Ive noticed no API response in JSON format here
            # No offers/monthly/income neither
            delay()

        except Exception as e:
            logger.error(f"PAFlow asset {aid} failed: {e}")


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
    std_ids    = read_asset_ids_from_csv("asset_ids.csv")
    pa_assets  = read_pa_assets("asset_ids_PAFlow.csv")
    main(std_ids, pa_assets)
