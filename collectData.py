"""
collectData.py
--------------
Fetches labor statistics from the BLS Public API and saves them to data/USLaborStats.csv.

Run once manually to perform the initial historical backfill (back to 1976).
After that, this script is called monthly by a GitHub Actions workflow to
append only the newest data point rather than re-fetching everything.

BLS API docs: https://www.bls.gov/developers/api_python.htm
Registration (free, higher rate limits): https://www.bls.gov/developers/
"""

import os
import json
import logging
from datetime import datetime

import pandas as pd
import requests

# Load .env when running locally; skip gracefully in CI/GitHub Actions
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
API_URL    = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
API_KEY    = os.getenv("BLS_API_KEY", "")           # Set in repo secrets
START_YEAR = int(os.getenv("BLS_START_YEAR", "1976"))
END_YEAR   = datetime.now().year
OUTPUT_FILE = "data/USLaborStats.csv"

# BLS enforces a 20-year window per request when fetching multiple series;
# see year_chunks() below for how this is handled.
CHUNK_SIZE = 20


# ------------------------------------------------------------------
# Series catalog
# ------------------------------------------------------------------
# Keys are BLS series IDs; values are the column names used in the CSV.
# Note: earnings and hours series (CES05...) start in 2006, so earlier
# rows for those columns will be NaN — this is expected and correct.
SERIES_KEYS = {
    "CES0000000001": "Total-Nonfarm-Payrolls",      # All employees, thousands, total nonfarm, SA
    "LNS14000000":   "Unemployment-Rate",            # Unemployment rate, %, SA
    "LNS11000000":   "Civilian-Labor-Force-Level",  # Civilian labor force, thousands, SA
    "CES0500000002": "Average-weekly-hours",        # Avg weekly hours, total private, SA
    "CES0500000003": "Average-Hourly-Earnings",     # Avg hourly earnings, total private, SA
    "CUUR0000SA0":   "Consumer-Price-Index",       # CPI-U, all items, not SA (trailing space intentional — matches BLS field)
}


# ------------------------------------------------------------------
# API helpers
# ------------------------------------------------------------------

def fetch_bls_data(series_ids: list, start_year: int, end_year: int) -> dict:
    """
    POST a request to the BLS v2 API for the given series and year range.
    Returns the parsed JSON response dict.
    Raises on HTTP errors or JSON parse failures so the caller can decide
    whether to retry or abort.
    """
    payload = json.dumps({
        "seriesid":       series_ids,
        "startyear":      str(start_year),
        "endyear":        str(end_year),
        "registrationkey": API_KEY,
    })
    headers = {"Content-type": "application/json"}

    try:
        resp = requests.post(API_URL, data=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        logger.info(f"Fetched {len(series_ids)} series for {start_year}–{end_year}")
        return json.loads(resp.text)
    except requests.exceptions.Timeout:
        logger.error("Request timed out after 30 seconds")
        raise
    except requests.exceptions.HTTPError as exc:
        logger.error(f"HTTP error: {exc}")
        raise
    except requests.exceptions.RequestException as exc:
        logger.error(f"Request failed: {exc}")
        raise
    except json.JSONDecodeError as exc:
        logger.error(f"Could not parse JSON response: {exc}")
        raise


def year_chunks(start: int, end: int, size: int = CHUNK_SIZE):
    """
    Yield (chunk_start, chunk_end) pairs that respect the BLS 20-year limit.
    Example: year_chunks(1976, 2025) → (1976,1995), (1996,2015), (2016,2025)
    """
    for y in range(start, end + 1, size):
        yield y, min(y + size - 1, end)


# ------------------------------------------------------------------
# Data transformation
# ------------------------------------------------------------------

def json_to_dataframe(json_data: dict) -> pd.DataFrame:
    """
    Parse the BLS JSON response into a tidy wide-format DataFrame with
    one row per month and one column per series.

    Only monthly periods (M01–M12) are kept; annual averages (M13) are dropped.
    """
    records = []
    for series in json_data["Results"]["series"]:
        series_id  = series["seriesID"]
        col_name   = SERIES_KEYS.get(series_id, series_id)

        for item in series["data"]:
            # Skip non-monthly codes (e.g., M13 = annual average)
            if not ("M01" <= item["period"] <= "M12"):
                continue

            month    = int(item["period"].replace("M", ""))
            date_str = f"{item['year']}-{month:02d}-01"

            # BLS returns "null" as a string for missing values
            if item["value"] == "null":
                continue

            try:
                records.append({
                    "Date":   date_str,
                    "Series": col_name,
                    "Value":  float(item["value"]),
                })
            except ValueError:
                # Skip malformed numeric strings rather than crashing
                logger.warning(f"Could not parse value '{item['value']}' for {series_id}")

    # Pivot from long to wide: one column per series, indexed by Date
    df = (
        pd.DataFrame(records)
        .pivot(index="Date", columns="Series", values="Value")
        .reset_index()
    )
    df["Date"] = pd.to_datetime(df["Date"])
    logger.info(f"Parsed {len(df)} monthly rows from API response")
    return df


# ------------------------------------------------------------------
# CSV helpers
# ------------------------------------------------------------------

def get_latest_date(csv_path: str) -> pd.Timestamp | None:
    """
    Return the most recent Date in the existing CSV, or None if the file
    does not yet exist. Used to decide how far back the incremental fetch
    needs to go.
    """
    if not os.path.exists(csv_path):
        return None
    existing = pd.read_csv(csv_path, parse_dates=["Date"])
    return existing["Date"].max()


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    logger.info("Starting BLS data collection")

    series_ids  = list(SERIES_KEYS.keys())
    latest_date = get_latest_date(OUTPUT_FILE)

    if latest_date is not None:
        # On monthly runs we only re-fetch from the year of the last record;
        # the append logic below then discards any rows already in the CSV.
        start_year = latest_date.year
        logger.info(f"Existing data found. Latest date: {latest_date.date()}")
    else:
        start_year = START_YEAR
        logger.info("No existing CSV found — performing full historical backfill")

    # Collect responses across all 20-year chunks into one combined structure
    combined = {"Results": {"series": []}}
    for chunk_start, chunk_end in year_chunks(start_year, END_YEAR):
        response = fetch_bls_data(series_ids, chunk_start, chunk_end)
        combined["Results"]["series"].extend(response["Results"]["series"])

    new_df = json_to_dataframe(combined)

    # Append-only logic: skip rows that are already in the CSV
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE, parse_dates=["Date"])
        new_df = new_df[new_df["Date"] > existing_df["Date"].max()]

        if new_df.empty:
            logger.info("No new rows to append — CSV is already up to date")
            return

        final_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    final_df.sort_values("Date").to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Appended {len(new_df)} new row(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
