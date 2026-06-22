#!/usr/bin/env python3
"""
Quick validation script to verify the dashboard app can load and process data
"""

import pandas as pd
import sys

def validate_data():
    """Validate that the CSV file can be loaded and contains expected columns."""
    try:
        df = pd.read_csv('data/USLaborStats.csv')
        df['Date'] = pd.to_datetime(df['Date'])

        print("CSV file loaded successfully")
        print(f"  - Records: {len(df)}")
        print(f"  - Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
        print(f"  - Columns: {', '.join(df.columns)}")

        # Check for required columns
        required_columns = [
            'Date', 'Total-Nonfarm-Payrolls', 'Unemployment-Rate',
            'Civilian-Labor-Force-Level', 'Average-Hourly-Earnings',
            'Average-weekly-hours', 'Consumer-Price-Index'
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"✗ Missing columns: {', '.join(missing_columns)}")
            return False

        print("All required columns present")

        # Check data types
        numeric_columns = [col for col in df.columns if col != 'Date']
        for col in numeric_columns:
            non_numeric = df[~df[col].isna() & ~df[col].apply(lambda x: isinstance(x, (int, float)))].shape[0]
            if non_numeric > 0:
                print(f"✗ Column '{col}' contains non-numeric values")
                return False

        print("All numeric columns have correct data types")

        # Check for missing values
        missing_pct = (df.isna().sum() / len(df) * 100).round(1)
        print("\n  Missing values by column:")
        for col in df.columns:
            if col != 'Date':
                pct = missing_pct[col]
                if pct > 0:
                    print(f"    {col}: {pct}%")

        return True

    except FileNotFoundError:
        print("CSV file not found at data/USLaborStats.csv")
        return False
    except Exception as e:
        print(f" Error loading data: {e}")
        return False

if __name__ == "__main__":
    success = validate_data()
    sys.exit(0 if success else 1)
