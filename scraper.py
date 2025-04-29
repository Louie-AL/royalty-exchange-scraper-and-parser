# scraper.py

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import requests
import time
from utils import setup_logger

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    service = EdgeService(EdgeChromiumDriverManager().install())
    return webdriver.Edge(service=service, options=options)

def get_html_from_asset(asset_id: str, driver, delay: float = 5.0) -> str:
    url = f"https://auctions.royaltyexchange.com/orderbook/asset-detail/{asset_id}/"
    driver.get(url)
    time.sleep(delay)
    return driver.page_source

def get_json_from_api(asset_id: str) -> dict:
    url = f"https://auctions.royaltyexchange.com/orderbook/api/listings/{asset_id}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json() # Log only when response is succesful, and skip when the endpoint returns 404 or other errors
    logger = setup_logger()
    logger.warning(f"Listing JSON for asset {asset_id} returned {response.status_code}")
    return {}

