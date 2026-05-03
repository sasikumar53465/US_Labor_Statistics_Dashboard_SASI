
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
from datetime import datetime

# ---------------DATA series catalog information ------------------
"""
# Note: Year range has been reduced to the system-allowed limit of 20 years . This is API setting for multiple series data retrieval. 
# The API will return data for the specified series and year range, which can then be processed and saved to a CSV file. 
# Each series has a unique ID and associated metadata that describes the data being collected.

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

API_URL = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
HEADERS = {'Content-type': 'application/json'}
START_YEAR = 2006
END_YEAR = datetime.now().year
APIkey = "faede8bf50b74aa9bda54c9812e2985a"
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
    PAYLOAD = json.dumps({"seriesid": series_ids,
                        "startyear": str(START_YEAR),
                        "endyear": str(END_YEAR),
                        "registrationkey": APIkey})

    p = requests.post(API_URL, data=PAYLOAD, headers=HEADERS)
    
    return json.loads(p.text)



    
"""  with open("data/USLaborStats.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["series_id", "Date", "value"]) 
"""
# Create a dataframe from the json data
def create_df(json_data):
    
    records = []
    for series in json_data["Results"]["series"]:
            series_id = series["seriesID"]
            name = SERIES_KEYS.get(series_id, series_id)
            for item in series["data"]:
                
                if item["year"] == "2026":
                    print(series["seriesID"], item["period"], item["value"])

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
    return df

def main():
    series_ids = list(SERIES_KEYS.keys())
    json_data = fetch_json_data(series_ids, START_YEAR, END_YEAR)
    df = create_df(json_data)
# Save CSV
    
    df = df.sort_values("Date").reset_index(drop=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(df)} rows to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()