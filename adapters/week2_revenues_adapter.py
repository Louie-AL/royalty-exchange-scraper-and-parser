"""
Build week2_revenues.csv using only financials.csv & raw_listing_data.csv
(the two files the current pipeline already produces).

Output columns, matching the legacy order:
    name | type | year | quarter | revenue | ID
"""
from __future__ import annotations
import pandas as pd, pathlib, re, datetime as dt

# ---------- helpers -----------------------------------------------------------
NUM_RE    = re.compile(r"([0-9.,]+)")
DOLLAR_RE = re.compile(r"[$,]")

def _num(x):
    "Convert $-strings like '$1,234' → float(1234)"
    if pd.isna(x):
        return None
    s = DOLLAR_RE.sub("", str(x))
    m = NUM_RE.search(s)
    return float(m.group().replace(",", "")) if m else None


# ---------- loader / builder --------------------------------------------------
def load(fin="financials.csv", raw="raw_listing_data.csv"):
    return pd.read_csv(fin), pd.read_csv(raw)

def build(fin: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    fin = fin.copy()

    # numeric LTM revenue
    fin["revenue"] = fin["Last 12 Months"].apply(_num)

    # choose a reference date for year / quarter
    fin["tx_date"] = pd.to_datetime(fin["Last Transaction Date"],
                                    errors="coerce")
    today = pd.Timestamp.today().normalize()
    fin["tx_date"] = fin["tx_date"].fillna(today)

    fin["year"]    = fin["tx_date"].dt.year
    fin["quarter"] = fin["tx_date"].dt.quarter

    fin = fin.rename(columns={"Listing ID": "ID"})[["ID","year","quarter",
                                                    "revenue"]]

    # ---- pull name / type from raw_listing_data -----------------------------
    raw_cols = {c.lower(): c for c in raw.columns}
    id_col   = raw_cols.get("listing id") or raw_cols.get("listing_id")
    name_col = raw_cols.get("title")
    type_col = raw_cols.get("term")

    raw_sub = (
        raw[[id_col, name_col, type_col]]
        .rename(columns={id_col: "ID", name_col: "name", type_col: "type"})
    )

    df = fin.merge(raw_sub, on="ID", how="left")

    # final column order
    df = df[["name", "type", "year", "quarter", "revenue", "ID"]]
    df.sort_values(["year", "quarter", "ID"], inplace=True)
    return df


# ---------- entry-point -------------------------------------------------------
def main(output="week2_revenues.csv"):
    fin, raw = load()
    out = build(fin, raw)
    pathlib.Path(output).write_text("")          # touch even if empty
    out.to_csv(output, index=False)
    print(f"✅ wrote {len(out):,} rows → {output}")

if __name__ == "__main__":
    main()
