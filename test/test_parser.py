# test_parser.py

from parser import parse_html, parse_offers

def test_parse_html_minimal():
    sample_html = """
    <html>
        <head><title>Test Asset</title></head>
        <body>
            <div data-testid='about-table'>
                <table>
                    <tr><td>Revenue</td><td>$100</td></tr>
                </table>
            </div>
        </body>
    </html>
    """
    result = parse_html(sample_html)
    assert result["title"] == "Test Asset"
    assert result["Revenue"] == "$100"

def test_parse_offers():
    fake_json = {
        "listing": {
            "offers": [
                {
                    "list_price": 1000,
                    "bid_amount": 950,
                    "investor_id": 42,
                    "created_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
    }
    offers = parse_offers(fake_json)
    assert len(offers) == 1
    assert offers[0]["List Price"] == 1000
    assert offers[0]["Bid Amount"] == 950
    assert offers[0]["Investor ID"] == 42
    assert offers[0]["Created At"] == "2023-01-01T00:00:00Z"
