# US Labor Statistics Dashboard

A Streamlit dashboard that displays US labor statistics data collected automatically from the Bureau of Labor Statistics (BLS) API. New data is collected monthly via GitHub Actions.

## Features

-  **Interactive Visualizations**: Explore labor statistics with Plotly charts
-  **Date Range Filtering**: Filter data by custom date ranges
-  **Automatic Data Updates**: Monthly data collection via GitHub Actions
-  **Data Export**: Download filtered data as CSV
-  **Real-time Dashboard**: View the latest labor statistics

## Data Series Included

1. **Total Nonfarm Payrolls** - All employees in thousands (seasonally adjusted)
      -measure_data_type: ALL EMPLOYEE in THOUSANDS
2. **Unemployment Rate** - Percentage of labor force (seasonally adjusted)
      -commerce_industry: All Industries,occupation: All Occupations
      -demographic_age: 16 years and over ,demographic_ethnic_origin: All Origins
      -demographic_race: All Races,demographic_gender: Both Sexes,
      -demographic_education: All educational levels
3. **Civilian Labor Force Level** - Total labor force in thousands (seasonally adjusted)
      -commerce_industry: All Industries,occupation: All Occupations
      -demographic_age: 16 years and over ,demographic_ethnic_origin: All Origins
      -demographic_race: All Races,demographic_gender: Both Sexes,
      -demographic_education: All educational levels
4. **Average Weekly Hours** - Hours worked per week (seasonally adjusted)
      -commerce_industry:Total private
5. **Average Hourly Earnings** - Hourly wage in dollars (seasonally adjusted)
      -commerce_industry:Total private
6. **Consumer Price Index** - All items index (not seasonally adjusted)
      -area: U.S. city average

## Setup Instructions

### Local Development

#### Prerequisites
- Python 3.11+
- pip
- Git

#### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd US_Labor_Statistics_Dashboard_SASI
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get BLS API Key**
   - Visit https://www.bls.gov/developers/home.htm
   - Register for an API key (free)
   - This key is already included in the repository for testing, but you should get your own for production

5. **Set environment variable**
   ```bash
   # On Windows (Command Prompt):
   set BLS_API_KEY=your_api_key_here
   
   # On Windows (PowerShell):
   $env:BLS_API_KEY="your_api_key_here"
   
   # On macOS/Linux:
   export BLS_API_KEY=your_api_key_here
   ```

6. **Run the Streamlit dashboard**
   ```bash
   streamlit run app.py
   ```
   
   The dashboard will open at `http://localhost:8501`

### Collecting Data Manually

To manually collect the latest BLS data:

```bash
export BLS_API_KEY=your_api_key_here  # Set the API key first
python collectData.py
```

This will update `data/USLaborStats.csv` with the latest available data from BLS.

## GitHub Actions Setup

The project includes automatic monthly data collection via GitHub Actions.

### Configuration Steps

1. **Add BLS API Key Secret to GitHub**
   - Go to your repository settings
   - Navigate to "Secrets and variables" → "Actions"
   - Click "New repository secret"
   - Name: `BLS_API_KEY`
   - Value: Your BLS API key from https://www.bls.gov/developers/home.htm
   - Click "Add secret"

2. **Workflow Details**
   - **File**: `.github/workflows/collect-bls-data.yml`
   - **Schedule**: First day of each month at 10 AM UTC
   - **Manual Trigger**: You can also manually trigger the workflow from the Actions tab
   - **Behavior**: 
     - Runs `collectData.py` with your API key
     - Only commits changes if new data is available
     - Automatically pushes updated CSV to the repository

### Manual Workflow Trigger

To collect data immediately (without waiting for the scheduled time):

1. Go to your GitHub repository
2. Click the "Actions" tab
3. Select "Collect BLS Labor Statistics Data" workflow
4. Click "Run workflow"
5. Click the green "Run workflow" button

## Project Structure

```
├── .github/
│   └── workflows/
│       └── collect-bls-data.yml       # GitHub Actions workflow
├── .streamlit/
│   ├── config.toml                    # Streamlit configuration
│   └── secrets.toml                   # Local secrets (not committed)
├── app.py                              # Main Streamlit dashboard
├── collectData.py                      # BLS API data collection script
├── data/
│   └── USLaborStats.csv                # Labor statistics data
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
└── LICENSE
```

## How It Works

### Data Collection Flow

1. **Monthly Trigger**: GitHub Actions runs on the first day of each month
2. **API Call**: `collectData.py` fetches new data from BLS API
3. **Data Processing**: 
   - Converts API response to DataFrame
   - Validates and cleans data
   - Handles missing values
4. **CSV Update**: Latest data appended to `data/USLaborStats.csv`
5. **Git Commit**: If new data available, commits and pushes to repository
6. **Dashboard Refresh**: Next time someone views the dashboard, new data loads automatically

### Dashboard Features

- **Three Tabs**:
  - **Employment Metrics**: Payrolls, unemployment, labor force
  - **Earnings & Hours**: Wages and hours worked
  - **Price Index**: Consumer price inflation
  
- **Date Range Filtering**: Select custom date ranges in sidebar
- **Key Metrics**: Shows current values at top of each tab
- **Interactive Charts**: Hover for exact values, zoom, pan
- **Data Download**: Export filtered data as CSV

## Technical Details

### Technologies Used

- **Data Collection**: Python, Requests library, pandas
- **Dashboard**: Streamlit, Plotly
- **Automation**: GitHub Actions, YAML workflows
- **Data Format**: CSV (comma-separated values)
- **API**: Bureau of Labor Statistics Public Data API

### API Constraints

- 20-year data window per API call (BLS API limitation)
- Monthly data points only (no weekly or daily data collected)
- Data is seasonally adjusted (where available)
- Free API tier available at https://www.bls.gov/developers/home.htm

## License

See LICENSE file for details.

## Data Source

All data is sourced from the [Bureau of Labor Statistics Public Data API](https://www.bls.gov/developers/home.htm).

## Course Information

**Course**: Econ 8320 - Tools for Data Analysis  
**Semester**: Spring 2026  
**University**: University of Nebraska Omaha

This project demonstrates:
- API data collection and automation
- Data cleaning and processing with pandas
- Interactive dashboard creation with Streamlit
- CI/CD automation with GitHub Actions
- Cloud deployment and monitoring
