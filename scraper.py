# scraper.py

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time
import requests

def get_html_from_asset(asset_id: str, delay: float = 5.0) -> str:
    url = f"https://auctions.royaltyexchange.com/orderbook/asset-detail/{asset_id}/"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

    driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)

    try:
        driver.get(url)
        time.sleep(delay)
        html = driver.page_source
    finally:
        driver.quit()

    return html

def get_json_from_api(asset_id: str) -> dict:
    url = f"https://auctions.royaltyexchange.com/orderbook/api/listings/{asset_id}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


