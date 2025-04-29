# parser.py

from bs4 import BeautifulSoup
import pandas as pd
import re
import io
import requests

def parse_html(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(separator=" ").strip()
    listing_data = {}

    # Extract financials from table
    table_container = soup.find("div", {"data-testid": "about-table"})
    if table_container:
        rows = table_container.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)
                listing_data[key] = value

    # Banner info
    banner_data = {}
    if m := re.search(r"Listing ID\s*\(?(\d+)\)?", text):
        banner_data["Listing ID"] = m.group(1)

    if m := re.search(r"Sale Price\s*\$([\d,]+)", text):
        banner_data["Sale Price"] = f"${m.group(1)}"

    if m := re.search(r"([\d.]+)\s*x\s*LTM", text):
        banner_data["LTM Multiple"] = f"{m.group(1)} x LTM"

    if m := re.search(r"(\d+ offers made by \d+ investors)", text):
        banner_data["Offer Info"] = m.group(1)  

    return {**banner_data, **listing_data}

def parse_offers(json_data: dict, asset_id: str) -> list:
    offers = json_data.get("listing", {}).get("offers", [])
    parsed = []

    for offer in offers:
        parsed.append({
            "Listing ID": asset_id,
            "timestamp": offer.get("created_at"),
            "amount": offer.get("bid_amount"),
            "multiple": offer.get("multiple"),
            "state": offer.get("state"),
            "kind": offer.get("kind"),
            "bidder_index": offer.get("bidder_index")
        })

    return parsed

def parse_monthly_revenues(json_data: dict, asset_id: str) -> pd.DataFrame:
    earnings_url = json_data.get("listing", {}).get("earnings_file")
    print(f"[{asset_id}] earnings_file URL:", earnings_url)

    if not earnings_url:
        return pd.DataFrame()

    try:
        response = requests.get(earnings_url)
        response.raise_for_status()
        print(f"[{asset_id}] File downloaded successfully.")
        
        df = pd.read_csv(io.StringIO(response.text))
        print(f"[{asset_id}] Earnings file shape: {df.shape}")
        print(df.head())  # Optional

        df["Listing ID"] = asset_id
        return df[["Listing ID", "date", "domestic", "international", "unreported", "total"]]
    except Exception as e:
        print(f"[{asset_id}] Failed to load earnings: {e}")
        return pd.DataFrame()

    
    
def parse_income_types_melted(json_data: dict, asset_id: str) -> pd.DataFrame:
    income_data = json_data.get("listing", {}).get("income_summary", {})
    if not income_data:
        return pd.DataFrame()
    df = pd.DataFrame(income_data).T
    df.index.name = "year"
    df = df.reset_index()
    df["Listing ID"] = asset_id
    melted = df.melt(id_vars=["Listing ID", "year"], var_name="income_type", value_name="amount")
    print(f"Income summary keys: {json_data.get('listing', {}).get('income_summary', {}).keys()}")

    return melted[["Listing ID", "year", "income_type", "amount"]]


def parse_full_listing(json_data: dict, asset_id: str) -> dict:
    listing = json_data.get("listing", {}) or {}
    flat = {"listing_id": asset_id}

    # Add top-level keys (excluding large nested stuff)
    for key, value in listing.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            flat[key] = value


    # Flatten valuation block if exists
    valuation = listing.get("valuation")
    flat.update(parse_valuation_block(valuation))

    return flat

def extract_youtube_id(youtube_embed_url: str) -> str:
    """
    Extracts the video ID from a YouTube embed URL.
    Example:
      Input: "https://www.youtube.com/embed/CAwf5KN6zN8?autoplay=0&mute=0&controls=1..."
      Output: "CAwf5KN6zN8"
    """
    if "/embed/" in youtube_embed_url:
        # Split the URL by '/embed/' and then split again by '?' to remove any query parameters.
        return youtube_embed_url.split("/embed/")[1].split("?")[0]
    return ""

def standardize_youtube_url(embed_url: str) -> str:
    """
    Converts a YouTube embed URL into a canonical watch URL.
    """
    video_id = extract_youtube_id(embed_url)
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return ""


def parse_youtube_link(html: str) -> str:

    """
    Finds all YouTube embed iframes and returns their IDs
    as a comma separated string
    """
    video_ids = []
    soup = BeautifulSoup(html, "lxml")
    for iframe in soup.find_all("iframe", src=True):
        src = iframe["src"]
        if "youtube.com/embed/" in src:
            vid = extract_youtube_id(src)
            if vid:
                video_ids.append(vid)
    return ",".join(video_ids)


def parse_valuation_block(valuation_json: dict) -> dict:
    """Flatten the valuation block into simple fields."""
    flattened = {}

    if not valuation_json:
        return flattened

    # Basic fields
    flattened["distribution_frequency"] = valuation_json.get("distribution_frequency")
    flattened["dollar_age"] = valuation_json.get("dollar_age")

    # Earnings by region block
    earnings = valuation_json.get("earnings_by_region", [])
    dates, domestic, intl, unreported, total = [], [], [], [], []
    for record in earnings:
        dates.append(record[0])
        domestic.append(str(record[1].get("domestic", 0)))
        intl.append(str(record[1].get("intl", 0)))
        unreported.append(str(record[1].get("unreported", 0)))
        total.append(str(record[1].get("total", 0)))

    flattened["earnings_date"] = ",".join(dates)
    flattened["earnings_domestic"] = ",".join(domestic)
    flattened["earnings_intl"] = ",".join(intl)
    flattened["earnings_unreported"] = ",".join(unreported)
    flattened["earnings_total"] = ",".join(total)

    # Top Songs
    top_songs = valuation_json.get("top_songs", [])
    flattened["song_names"] = ",".join([song.get("name", "") for song in top_songs])
    flattened["song_earnings"] = ",".join([str(song.get("earnings", "")) for song in top_songs])

    # Top Sources
    top_sources = valuation_json.get("top_sources", [])
    flattened["source_names"] = ",".join([src.get("name", "") for src in top_sources])
    flattened["source_earnings"] = ",".join([str(src.get("earnings", "")) for src in top_sources])

    # Top Income Types
    top_income_types = valuation_json.get("top_income_types", [])
    flattened["income_type_names"] = ",".join([inc.get("name", "") for inc in top_income_types])
    flattened["income_type_earnings"] = ",".join([str(inc.get("earnings", "")) for inc in top_income_types])

    # Top Music Users (optional)
    top_music_users = valuation_json.get("top_music_users", [])
    if top_music_users:
        flattened["music_user_names"] = ",".join([user.get("name", "") for user in top_music_users])
        flattened["music_user_earnings"] = ",".join([str(user.get("earnings", "")) for user in top_music_users])
    else:
        flattened["music_user_names"] = ""
        flattened["music_user_earnings"] = ""

    return flattened
