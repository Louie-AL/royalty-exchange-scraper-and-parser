# test_scraper.py

from scraper import get_json_from_api

def test_get_json_from_api_valid():
    asset_id = "6122"  # You can use a known existing asset ID
    data = get_json_from_api(asset_id)
    assert "listing" in data
    assert "offers" in data["listing"]
