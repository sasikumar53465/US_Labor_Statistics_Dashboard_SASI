
"""
CollectData.py
Fetches labor statistics from the BLS Public API and saves them to data/USLaborStats.csv.
Run this script once to collect historical data, then monthly via GitHub Actions.

"""

import os
import requests
import json
import csv
import pandas as pd
import logging
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is only needed for local development

# ---------------DATA series catalog information ------------------
"""
# Note: Year range has been reduced to the system-allowed limit of 20 years . This is API setting for multiple series data retrieval. 
# The API will return data for the specified series and year range, which can then be processed and saved to a CSV file. 
# Each series has a unique ID and associated metadata that describes the data being collected.
 Some labor series (e.g., earnings and weekly hours) were introduced later by BLS; 
 earlier dates are represented as missing values to accurately reflect historical availability.

                "seriesID": "CES0000000001",
                "catalog": 
                    "series_title": "All employees, thousands, total nonfarm, seasonally adjusted",
                    "series_id": "CES0000000001",
                    "seasonality": "Seasonally Adjusted",
                    "survey_name": "Employment, Hours, and Earnings from the Current Employment Statistics survey (National)",
                    "survey_abbreviation": "CE",
                    "measure_data_type": "ALL EMPLOYEES, THOUSANDS",
                    "commerce_industry": "Total nonfarm",
                    "commerce_sector": "Total nonfarm"
                
                "seriesID": "LNS14000000",
                "catalog": {
                    "series_title": "(Seas) Unemployment Rate",
                    "series_id": "LNS14000000",
                    "seasonality": "Seasonally Adjusted",
                    "survey_name": "Labor Force Statistics from the Current Population Survey",
                    "survey_abbreviation": "LN",
                    "measure_data_type": "Percent or rate",
                    "commerce_industry": "All Industries",
                    "occupation": "All Occupations",
                    "cps_labor_force_status": "Unemployment rate",
                    "demographic_age": "16 years and over",
                    "demographic_ethnic_origin": "All Origins",
                    "demographic_race": "All Races",
                    "demographic_gender": "Both Sexes",
                    "demographic_education": "All educational levels"

                "seriesID": "LNS11000000",
                "catalog": {
                    "series_title": "(Seas) Civilian Labor Force Level",
                    "series_id": "LNS11000000",
                    "seasonality": "Seasonally Adjusted",
                    "survey_name": "Labor Force Statistics from the Current Population Survey",
                    "survey_abbreviation": "LN",
                    "measure_data_type": "Number in thousands",
                    "commerce_industry": "All Industries",
                    "occupation": "All Occupations",
                    "cps_labor_force_status": "Civilian labor force",
                    "demographic_age": "16 years and over",
                    "demographic_ethnic_origin": "All Origins",
                    "demographic_race": "All Races",
                    "demographic_gender": "Both Sexes",
                    "demographic_education": "All educational levels" 
                    
                "seriesID": "CES0500000002",
                "catalog": {
                    "series_title": "Average weekly hours of all employees, total private, seasonally adjusted",
                    "series_id": "CES0500000002",
                    "seasonality": "Seasonally Adjusted",
                    "survey_name": "Employment, Hours, and Earnings from the Current Employment Statistics survey (National)",
                    "survey_abbreviation": "CE",
                    "measure_data_type": "AVERAGE WEEKLY HOURS OF ALL EMPLOYEES",
                    "commerce_industry": "Total private",
                    "commerce_sector": "Total private"
                    
                "seriesID": "CES0500000003",
                "catalog": {
                    "series_title": "Average hourly earnings of all employees, total private, seasonally adjusted",
                    "series_id": "CES0500000003",
                    "seasonality": "Seasonally Adjusted",
                    "survey_name": "Employment, Hours, and Earnings from the Current Employment Statistics survey (National)",
                    "survey_abbreviation": "CE",
                    "measure_data_type": "AVERAGE HOURLY EARNINGS OF ALL EMPLOYEES",
                    "commerce_industry": "Total private",
                    "commerce_sector": "Total private"


                "seriesID": "CUUR0000SA0",
                "catalog": {
                    "series_title": "All items in U.S. city average, all urban consumers, not seasonally adjusted",
                    "series_id": "CUUR0000SA0",
                    "seasonality": "Not Seasonally Adjusted",
                    "survey_name": "Consumer Price Index for All Urban Consumers (CPI-U)",
                    "survey_abbreviation": "CU",
                    "measure_data_type": "All items",
                    "area": "U.S. city average",
                    "item": "All items"                                                           
                    
"""
# --------------------------------------------------
# --------------------------------------------------
# Config
# --------------------------------------------------

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_URL = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
HEADERS = {'Content-type': 'application/json'}
START_YEAR = int(os.getenv("BLS_START_YEAR", "2007"))
END_YEAR = datetime.now().year
APIkey = os.getenv("BLS_API_KEY", "")
OUTPUT_FILE = "data/USLaborStats.csv"


# --------------------------------------------------
# SERIES_KEYS
# --------------------------------------------------
SERIES_KEYS = {
    "CES0000000001": "Total-Nonfarm-Payrolls",              #  "All employees, thousands, total nonfarm, seasonally adjusted"   
    "LNS14000000": "Unemployment-Rate",                     # (Seas) Unemployment Rate -Seasonally Adjusted- Percent or rate
    "LNS11000000": "Civilian-Labor-Force-Level",            # (Seas) Civilian Labor Force Level -Seasonally Adjusted- Number in thousands
    "CES0500000002": "Average-weekly-hours",                # Average weekly hours of all employees, total private, seasonally adjusted
    "CES0500000003": "Average-Hourly-Earnings",             # Average hourly earnings of all employees, total private, seasonally adjusted
    "CUUR0000SA0": "Consumer-Price-Index "                  # All items in U.S. city average, all urban consumers, not seasonally adjusted
}


def fetch_json_data(series_ids, START_YEAR, END_YEAR):
#    logger.info(f"APIkey is {APIkey}")
    PAYLOAD = json.dumps({"seriesid": series_ids,
                        "startyear": str(START_YEAR),
                        "endyear": str(END_YEAR),
                        "registrationkey": APIkey
                        })
    try:
        p = requests.post(API_URL, data=PAYLOAD, headers=HEADERS, timeout=30)
        p.raise_for_status()
        logger.info(f"Successfully fetched data for {len(series_ids)} series")
        return json.loads(p.text)
    except requests.exceptions.Timeout:
        logger.error("Request timed out after 30 seconds")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise




# Create a dataframe from the json data
def create_df(json_data):

    records = []
    for series in json_data["Results"]["series"]:
            series_id = series["seriesID"]
            name = SERIES_KEYS.get(series_id, series_id)
            for item in series["data"]:

                if "M01" <= item["period"] <= "M12":
                    period = int(item["period"].replace("M", ""))
                    date_str = f"{item['year']}-{period:02d}-01"

                    if item["value"] != "null":
                        try:
                            value = float(item["value"])
                            records.append({"Date": date_str, "Series": name, "Value": value})
                        except ValueError:
                            pass  # Skip invalid values

    df = pd.DataFrame(records).pivot(index="Date", columns="Series", values="Value").reset_index()
    df["Date"] = pd.to_datetime(df["Date"])
    logger.info(f"Created dataframe with {len(df)} rows")
    return df

# Helper function to generate year chunks for API requests
def year_chunks(start, end, chunk_size=20):
    """
    Yield (start_year, end_year) tuples respecting the BLS 20-year limit.
    """
    for y in range(start, end + 1, chunk_size):
        yield y, min(y + chunk_size - 1, end)

# Helper function to get the latest date from the existing CSV file        
def get_latest_date(csv_path):
    if not os.path.exists(csv_path):
        return None
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    return df["Date"].max()

def main():
    logger.info("Starting monthly BLS data collection")

    series_ids = list(SERIES_KEYS.keys())
    latest_date = get_latest_date(OUTPUT_FILE)

    if latest_date is not None:
        start_year = latest_date.year
        logger.info(f"Existing data found. Latest date = {latest_date.date()}")
    else:
        start_year = START_YEAR
        logger.info("No existing data found. Performing initial backfill.")

    # Fetch only the necessary range (<= 20 years automatically)
    combined_json = {"Results": {"series": []}}

    for y in range(start_year, END_YEAR + 1, 20):
        response = fetch_json_data(series_ids, y, min(y + 19, END_YEAR))
        combined_json["Results"]["series"].extend(
            response["Results"]["series"]
        )

    new_df = create_df(combined_json)

    # If CSV exists, append only new rows
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE, parse_dates=["Date"])
        new_df = new_df[new_df["Date"] > existing_df["Date"].max()]
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        final_df = new_df

    if new_df.empty:
        logger.info("No new data to append")
        return

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    final_df.sort_values("Date").to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Appended {len(new_df)} new rows to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()