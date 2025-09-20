import pandas as pd
from difflib import get_close_matches

# ---------- Load Cleaned Data ----------
df = pd.read_csv("myapp/land_prices_with_correct_per_cent.csv")

# Keep only valid rows
df = df.dropna(subset=["district", "locality", "area_sqft", "price_num"])
df = df[df["area_sqft"] > 0]

# Compute cents and per cent price
df["cents"] = df["area_sqft"] / 435.6
df["price_per_cent_calc"] = df["price_num"] / df["cents"]

# ---------- Districts and Localities Mapping ----------
district_localities = {
    district: df[df["district"] == district]["locality"].unique().tolist()
    for district in df["district"].unique()
}

# ---------- Functions ----------
def get_districts():
    """Return list of available districts"""
    return sorted(df["district"].dropna().unique().tolist())

def get_price_info_fuzzy(district, locality):
    """
    Predict average price per cent and total price for a given locality.
    Uses fuzzy matching if locality is misspelled.
    Returns: per_cent, total_price, fallback_flag, matched_locality
    """
    # Exact match first
    subset = df[(df["district"].str.lower() == district.lower()) &
                (df["locality"].str.lower() == locality.lower())]
    if not subset.empty:
        avg_per_cent = subset["price_per_cent_calc"].mean()
        avg_total = subset["price_num"].mean()
        return round(avg_per_cent, 2), round(avg_total, 2), False, locality  # exact match

    # Fuzzy match within district
    localities_list = district_localities.get(district, [])
    closest = get_close_matches(locality, localities_list, n=1, cutoff=0.6)
    if closest:
        matched_locality = closest[0]
        subset = df[(df["district"].str.lower() == district.lower()) &
                    (df["locality"] == matched_locality)]
        avg_per_cent = subset["price_per_cent_calc"].mean()
        avg_total = subset["price_num"].mean()
        return round(avg_per_cent, 2), round(avg_total, 2), True, matched_locality  # fuzzy match

    # Fallback to district average
    subset = df[df["district"].str.lower() == district.lower()]
    if subset.empty:
        return None, None, None, None
    avg_per_cent = subset["price_per_cent_calc"].mean()
    avg_total = subset["price_num"].mean()
    return round(avg_per_cent, 2), round(avg_total, 2), True, None  # district fallback
