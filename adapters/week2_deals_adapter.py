"""
Generate the legacy week2_deals.csv from current Royalty-Exchange scraper outputs.
"""

from __future__ import annotations
import pandas as pd, re, pathlib

# ------------------------------------------------------------
# helpers
# ------------------------------------------------------------
NUM_RE = re.compile(r"([0-9.]+)")            # grab digits & dot once
DOLLAR_RE = re.compile(r"[$,]")           # strip $ and commas

def _num(s: str | float | int):
    if pd.isna(s):
        return None
    s = str(s)
    s = DOLLAR_RE.sub("", s)
    m = NUM_RE.search(s)
    return float(m.group()) if m else None

# ------------------------------------------------------------
# loader / cleaner
# ------------------------------------------------------------
def load_inputs(fin="financials.csv",
                off="offers.csv",
                raw="raw_listing_data.csv"):
    return (pd.read_csv(fin),
            pd.read_csv(off),
            pd.read_csv(raw))

def build_deals(fin: pd.DataFrame,
                offers: pd.DataFrame,
                raw: pd.DataFrame) -> pd.DataFrame:

    # --- clean financials ----------------------------------------------------
    fin = fin.copy()

    fin["multiplier"] = (
        fin["LTM Multiple"]
            .astype(str)                  # make sure it’s str
            .str.extract(NUM_RE, expand=False)
            .astype(float)
    )
    fin["price"]        = fin["Sale Price"].apply(_num)
    fin["LTM"]          = fin["Last 12 Months"].apply(_num)
    fin["age"]          = fin["Dollar Age"].apply(_num)
    fin["market_median"]= fin["Marketplace Median"].apply(_num)
    fin = fin.rename(columns={"Listing ID": "ID"})

    # --- bring in deal_date from filled offers ------------------------------
    off = offers.copy()
    off = off[off["state"].str.lower().eq("filled")]\
            .rename(columns={"Listing ID": "ID",
                             "multiple":   "multiplier",
                             "timestamp":  "deal_date"})
    off["multiplier"] = off["multiplier"].astype(float)

    fin = fin.merge(off[["ID","multiplier","deal_date"]],
                    on=["ID", "multiplier"],
                    how="left")

    # --- add name / type from raw listing data ------------------------------
    raw_cols = {c.lower(): c for c in raw.columns}   # case-flexible
    fin = fin.merge(
        raw[[ raw_cols.get("listing id","Listing ID"),
               raw_cols.get("title","title"),
               raw_cols.get("term","term") ]]
        .rename(columns={ raw_cols.get("listing id","Listing ID"): "ID",
                          raw_cols.get("title","title"):           "name",
                          raw_cols.get("term","term"):             "type"}),
        on="ID",
        how="left"
    )

    # --- final order & formatting -------------------------------------------
    out_cols = ["name","type","deal_date","market_median","multiplier",
                "LTM","age","ID","price"]
    out = fin[out_cols].copy()
    out["deal_date"] = pd.to_datetime(out["deal_date"], errors="coerce").dt.date
    return out

# ------------------------------------------------------------
# entry-point
# ------------------------------------------------------------
def main(output="week2_deals.csv"):
    fin, off, raw = load_inputs()
    deals = build_deals(fin, off, raw)
    pathlib.Path(output).write_text("")   # touch for visibility if empty
    deals.to_csv(output, index=False)
    print(f"✅ wrote {len(deals):,} rows → {output}")

if __name__ == "__main__":
    main()
