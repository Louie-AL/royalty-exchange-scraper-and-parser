# parser_pa.py

from bs4 import BeautifulSoup

def parse_pa_financials(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    out = {}

    # Main auction metadata
    try: out["Sale Price"] = soup.find(string=lambda t: "$" in t and "Sale Price" in t.parent.text).parent.find_next("span").text.strip()
    except: out["Sale Price"] = None

    try:
        for tr in soup.select("table tbody tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
            if len(cells) == 2:
                out[cells[0]] = cells[1]
    except: pass

    return out


def parse_pa_offers(html: str, asset_id: int) -> list[dict]:
    # These legacy listings usually do not expose full bid history
    soup = BeautifulSoup(html, "html.parser")
    out = []
    try:
        top_bid = soup.find(string="Top Bid").find_next("span").text.strip()
        top_bidder = soup.find(string="Top Bidder").find_next("span").text.strip()
        out.append({
            "Asset ID": asset_id,
            "Bid Amount": top_bid,
            "Bidder": top_bidder,
            "Accepted": True  # synthetic
        })
    except: pass
    return out


def parse_pa_raw_listing(html: str, asset_id: int) -> dict:
    # Attempt to mimic parse_full_listing fallback
    soup = BeautifulSoup(html, "html.parser")
    out = {"Asset ID": asset_id}
    try:
        out["Title"] = soup.find("h1").get_text(strip=True)
    except: out["Title"] = None
    try:
        out["Closing Price"] = soup.find(string="Closing Price").find_next("span").text.strip()
    except: out["Closing Price"] = None
    return out
