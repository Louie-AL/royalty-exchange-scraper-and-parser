"""
Generate the legacy week2_songs.csv from the three standard scraper outputs:
    • financials.csv
    • raw_listing_data.csv
    • (offers.csv not needed)

Output column order (exactly as the legacy file):
    type , name , year , asset_id , title , artist
"""

from __future__ import annotations
import pandas as pd, re, pathlib

# ── helpers ────────────────────────────────────────────────────────────────
YEAR_RE   = re.compile(r"\b(19|20)\d{2}\b")           # four-digit recording year
SPLIT_RE  = re.compile(r"\s*[-–]\s*|\s+by\s+", re.I)  # "Title – Artist" or "Title by Artist"

def _parse_track(raw: str):
    """Return (title, artist, year | None) from a single track string."""
    if pd.isna(raw) or not str(raw).strip():
        return "", "", None

    s = str(raw).strip().strip('"\'')
    # year (take last 4-digit number)
    yrs  = YEAR_RE.findall(s)
    year = int(yrs[-1]) if yrs else None
    if year:
        s = YEAR_RE.sub("", s).strip(" ()-–")

    # split on " – " or " by "
    parts = SPLIT_RE.split(s, 1)
    title, artist = (parts + [""])[:2]          # ensure two items
    return title.strip(), artist.strip(), year

# ── loader / builder ───────────────────────────────────────────────────────
def load(fin="financials.csv", raw="raw_listing_data.csv"):
    return pd.read_csv(fin), pd.read_csv(raw)

def build(fin: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    # listing-level metadata
    raw_cols = {c.lower(): c for c in raw.columns}
    meta = (
        raw[[raw_cols.get("listing id","Listing ID"),
             raw_cols.get("title","title"),
             raw_cols.get("term","term")]]
        .rename(columns={
            raw_cols.get("listing id","Listing ID"): "asset_id",
            raw_cols.get("title","title"):           "name",
            raw_cols.get("term","term"):             "type"
        })
    )

    # explode Tracks Included
    track_col = next(c for c in fin.columns if c.lower().startswith("tracks"))
    tracks = (
        fin.loc[~fin[track_col].isna(), ["Listing ID", track_col]]
           .rename(columns={"Listing ID": "asset_id"})
           .assign(**{
               track_col: lambda d: (
                   d[track_col]
                     .astype(str)
                     .str.split(r"\s*[;|\n]\s*")        # split on ";" or newline
               )
           })
           .explode(track_col, ignore_index=True)
           .rename(columns={track_col: "raw_track"})
    )

    # parse each raw_track
    parsed = tracks["raw_track"].apply(_parse_track).tolist()
    tracks[["title","artist","year"]] = pd.DataFrame(parsed, index=tracks.index)

    # merge metadata
    songs = tracks.merge(meta, on="asset_id", how="left")

    # final order
    songs = songs[["type","name","year","asset_id","title","artist"]]
    songs["year"] = songs["year"].astype("Int64")  # nullable int
    return songs

# ── entry-point ───────────────────────────────────────────────────────────
def main(output="week2_songs.csv"):
    fin, raw = load()
    songs = build(fin, raw)
    pathlib.Path(output).write_text("")       # touch even if empty
    songs.to_csv(output, index=False)
    print(f"✅ wrote {len(songs):,} rows → {output}")

if __name__ == "__main__":
    main()
