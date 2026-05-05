"""
app.py
------
US Labor Statistics Dashboard

Reads from data/USLaborStats.csv (populated by collectData.py / GitHub Actions).
No data collection happens here; this file is purely for exploration and display.

Series included:
  - Total Nonfarm Payrolls (CES0000000001)
  - Unemployment Rate      (LNS14000000)
  - Civilian Labor Force   (LNS11000000)
  - Average Weekly Hours   (CES0500000002)
  - Average Hourly Earnings(CES0500000003)
  - Consumer Price Index   (CUUR0000SA0)
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, date
from scipy import stats  # used for the regression in the Analysis tab
import statsmodels.api as sm

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="US Labor Statistics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------

@st.cache_data
def load_data(path: str = "data/USLaborStats.csv") -> pd.DataFrame:
    """
    Load the pre-built CSV and parse dates.
    Cached so the file is only read once per session.
    """
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df.sort_values("Date").reset_index(drop=True)


df = load_data()

# ------------------------------------------------------------------
# Sidebar — filters
# ------------------------------------------------------------------
st.sidebar.header("Filters")

# Get available years and months from data
years = sorted(df["Date"].apply(lambda x: x.year).unique())
months = list(range(1, 13))

# Start date selectors
start_year = st.sidebar.selectbox("Start Year", years, index=0)
start_month = st.sidebar.selectbox("Start Month", months, index=0, format_func=lambda x: f"{x:02d}")

# End date selectors
end_year = st.sidebar.selectbox("End Year", years, index=len(years)-1)
end_month = st.sidebar.selectbox("End Month", months, index=11, format_func=lambda x: f"{x:02d}")

# Create date objects
start_date = date(int(start_year), int(start_month), 1)
end_date = date(int(end_year), int(end_month), 1)

fdf = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()

st.sidebar.markdown("---")
st.sidebar.info(f"📅 Last data point: {df['Date'].max().strftime('%B %Y')}")
st.sidebar.info(f"📈 {len(df)} monthly observations")

# ------------------------------------------------------------------
# Page header
# ------------------------------------------------------------------
st.title("US Labor Statistics Dashboard")
st.markdown(
    "*Data from the Bureau of Labor Statistics Public API · "
    "Updated monthly via GitHub Actions*"
)

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab_emp, tab_earn, tab_cpi, tab_analysis = st.tabs([
    "Employment", "Earnings & Hours", "Price Index", "Analysis"
])


# ==================== helpers ====================

def line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    y_label: str,
    color: str,
    fill_color: str | None = None,
    height: int = 400,
    extra_traces: list | None = None,
) -> go.Figure:
    """
    Build a simple Plotly line chart with optional overlay traces.
    Keeping chart creation in one place avoids repeated boilerplate.
    """
    valid = df[[x_col, y_col]].dropna()
    fig = go.Figure()

    if len(valid) > 0:
        fig.add_trace(go.Scatter(
            x=valid[x_col],
            y=valid[y_col],
            mode="lines",
            name=y_col,
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=fill_color,
        ))

    if extra_traces:
        for trace in extra_traces:
            fig.add_trace(trace)

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_label,
        hovermode="x unified",
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def summary_stats(series: pd.Series, label: str) -> pd.DataFrame:
    """Return a small descriptive stats table for a single series."""
    clean = series.dropna()
    pct_change = clean.pct_change().dropna() * 100  # month-over-month % change
    return pd.DataFrame({
        "Metric": ["Mean", "Std Dev", "Min", "Max", "Avg MoM Growth (%)"],
        label: [
            f"{clean.mean():.2f}",
            f"{clean.std():.2f}",
            f"{clean.min():.2f}",
            f"{clean.max():.2f}",
            f"{pct_change.mean():.3f}",
        ],
    }).set_index("Metric")


# ==================== TAB 1 — Employment ====================
with tab_emp:
    latest = fdf.iloc[-1] if len(fdf) > 0 else None

    col1, col2, col3 = st.columns(3)
    if latest is not None:
        with col1:
            val = latest.get("Total-Nonfarm-Payrolls", np.nan)
            st.metric(f"Total Nonfarm Payrolls (As of {latest['Date'].strftime('%B %Y')})", f"{val:,.0f}K" if not pd.isna(val) else "N/A")
        with col2:
            val = latest.get("Unemployment-Rate", np.nan)
            st.metric(f"Unemployment Rate (As of {latest['Date'].strftime('%B %Y')})", f"{val:.1f}%" if not pd.isna(val) else "N/A")
        with col3:
            val = latest.get("Civilian-Labor-Force-Level", np.nan)
            st.metric(f"Civilian Labor Force (As of {latest['Date'].strftime('%B %Y')})", f"{val:,.0f}K" if not pd.isna(val) else "N/A")

    st.markdown("---")

    # Side-by-side: payrolls and unemployment
    c1, c2 = st.columns(2)
    with c1:
        fig = line_chart(
            fdf, "Date", "Total-Nonfarm-Payrolls",
            "Total Nonfarm Payrolls (Thousands)", "Employees (K)",
            "#1f77b4","rgba(31,119,180,0.15)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = line_chart(
            fdf, "Date", "Unemployment-Rate",
            "Unemployment Rate (%)", "Rate (%)",
            "#d62728", "rgba(214,39,40,0.15)"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Full-width: civilian labor force
    fig = line_chart(
        fdf, "Date", "Civilian-Labor-Force-Level",
        "Civilian Labor Force Level (Thousands)", "Labor Force (K)",
        "#2ca02c", "rgba(44,160,44,0.15)"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Employment Trends Overview")
    st.markdown(
        "This combined view indexes all three employment series to 100 at the start of the selected period, "
        "allowing for easy comparison of their relative movements. Key insights: Payrolls and unemployment move inversely "
        "(when one rises, the other falls), while the labor force tends to grow during expansions and shrink during recessions."
    )

    # Indexed trends for employment series
    emp_df = fdf[["Date", "Total-Nonfarm-Payrolls", "Unemployment-Rate", "Civilian-Labor-Force-Level"]].dropna().copy()
    if len(emp_df) > 0:
        base_payrolls = emp_df["Total-Nonfarm-Payrolls"].iloc[0]
        base_unemp = emp_df["Unemployment-Rate"].iloc[0]
        base_labor = emp_df["Civilian-Labor-Force-Level"].iloc[0]

        emp_df["Payrolls Index"] = (emp_df["Total-Nonfarm-Payrolls"] / base_payrolls) * 100
        emp_df["Unemployment Index"] = (emp_df["Unemployment-Rate"] / base_unemp) * 100
        emp_df["Labor Force Index"] = (emp_df["Civilian-Labor-Force-Level"] / base_labor) * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=emp_df["Date"], y=emp_df["Payrolls Index"],
            mode="lines", name="Total Nonfarm Payrolls",
            line=dict(color="#1f77b4", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=emp_df["Date"], y=emp_df["Unemployment Index"],
            mode="lines", name="Unemployment Rate",
            line=dict(color="#d62728", width=2, dash="dash")
        ))
        fig.add_trace(go.Scatter(
            x=emp_df["Date"], y=emp_df["Labor Force Index"],
            mode="lines", name="Civilian Labor Force",
            line=dict(color="#2ca02c", width=2)
        ))
        fig.update_layout(
            title="Indexed Employment Trends (Base = 100)",
            xaxis_title="Date", yaxis_title="Index Value (Base = 100)",
            hovermode="x unified", height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Interesting Findings:**")
        st.markdown(
            "- **Inverse Relationship**: Payrolls and unemployment often move in opposite directions. "
            "Sharp drops in payrolls (e.g., during recessions like 2008 or 2020) are accompanied by spikes in unemployment."
        )
        st.markdown(
            "- **Labor Force Dynamics**: The civilian labor force grows steadily during economic booms but can decline during downturns "
            "as discouraged workers drop out. This 'discouraged worker effect' can mask the true severity of unemployment."
        )
        st.markdown(
            "- **Cyclical Patterns**: Over the long term, these series show clear business cycles. Expansions see rising payrolls, "
            "falling unemployment, and labor force growth; contractions reverse these trends."
        )

    # Descriptive stats
    with st.expander("Summary statistics — Employment series"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.dataframe(summary_stats(fdf["Total-Nonfarm-Payrolls"], "Payrolls (K)"))
        with c2:
            st.dataframe(summary_stats(fdf["Unemployment-Rate"], "Unemp. Rate (%)"))
        with c3:
            st.dataframe(summary_stats(fdf["Civilian-Labor-Force-Level"], "Labor Force (K)"))


# ==================== TAB 2 — Earnings & Hours ====================
with tab_earn:
    latest = fdf.iloc[-1] if len(fdf) > 0 else None

    col1, col2 = st.columns(2)
    if latest is not None:
        with col1:
            val = latest.get("Average-Hourly-Earnings", np.nan)
            st.metric(f"Avg Hourly Earnings (As of {latest['Date'].strftime('%B %Y')})", f"${val:.2f}" if not pd.isna(val) else "N/A")
        with col2:
            val = latest.get("Average-weekly-hours", np.nan)
            st.metric(f"Avg Weekly Hours (As of {latest['Date'].strftime('%B %Y')})", f"{val:.1f} hrs" if not pd.isna(val) else "N/A")

    st.markdown("---")

    st.plotly_chart(
        line_chart(
            fdf, "Date", "Average-Hourly-Earnings",
            "Average Hourly Earnings ($)", "$/hr",
            "#ff7f0e", "rgba(255,127,14,0.15)"
        ),
        use_container_width=True,
    )

    st.plotly_chart(
        line_chart(
            fdf, "Date", "Average-weekly-hours",
            "Average Weekly Hours", "Hours/week",
            "#9467bd", "rgba(148,103,189,0.15)"
        ),
        use_container_width=True,
    )

    with st.expander("Summary statistics — Earnings & Hours"):
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(summary_stats(fdf["Average-Hourly-Earnings"], "Avg Hourly ($)"))
        with c2:
            st.dataframe(summary_stats(fdf["Average-weekly-hours"], "Avg Weekly Hrs"))


# ==================== TAB 3 — Price Index ====================
with tab_cpi:
    latest = fdf.iloc[-1] if len(fdf) > 0 else None

    if latest is not None:
        val = latest.get("Consumer-Price-Index", np.nan)
        st.metric(f"Consumer Price Index (CPI-U) (As of {latest['Date'].strftime('%B %Y')})", f"{val:.2f}" if not pd.isna(val) else "N/A")

    st.markdown("---")

    # Real wages: inflation-adjusted hourly earnings
    # Real wage = nominal wage / (CPI / 100) — shows purchasing power
    real_wage_df = fdf[["Date", "Consumer-Price-Index", "Average-Hourly-Earnings"]].dropna().copy()
    if len(real_wage_df) > 0:
        real_wage_df["Real Hourly Earnings"] = real_wage_df["Average-Hourly-Earnings"] / (real_wage_df["Consumer-Price-Index"] / 100)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=real_wage_df["Date"], y=real_wage_df["Real Hourly Earnings"],
            mode="lines", name="Real Hourly Earnings",
            line=dict(color="#17becf", width=2), fill="tozeroy", fillcolor="rgba(23,190,207,0.15)"
        ))
        fig.add_trace(go.Scatter(
            x=real_wage_df["Date"], y=real_wage_df["Average-Hourly-Earnings"],
            mode="lines", name="Nominal Hourly Earnings",
            line=dict(color="#ff7f0e", width=2, dash="dash")
        ))
        fig.update_layout(
            title="Real vs. Nominal Hourly Earnings (Inflation-Adjusted Real, 1982–84 = 100)",
            xaxis_title="Date", yaxis_title="Earnings ($)",
            hovermode="x unified", height=450,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Real earnings adjust nominal wages for inflation using CPI-U. "
            "A rising line indicates improving purchasing power; falling indicates erosion."
        )

    st.plotly_chart(
        line_chart(
            fdf, "Date", "Consumer-Price-Index",
            "Consumer Price Index — All Items (1982–84 = 100)", "Index Value",
            "#17becf", "rgba(23,190,207,0.15)"
        ),
        use_container_width=True,
    )

    with st.expander("Summary statistics — CPI"):
        st.dataframe(summary_stats(fdf["Consumer-Price-Index"], "CPI-U"))


# ==================== TAB 4 — Analysis ====================
with tab_analysis:
    st.subheader("Applied Economic Analysis")
    st.markdown(
        "This section explores three economically meaningful questions using the six "
        "available series. Correlations and the regression below are descriptive — "
        "causal claims require a more controlled research design."
    )

    # ----------------------------------------------------------
    # 1. 12-month rolling average — payrolls and unemployment
    # ----------------------------------------------------------
    st.markdown("### Rolling Averages — Smoothing Cyclical Noise")
    st.markdown(
        "A 12-month rolling mean removes month-to-month sampling noise and makes "
        "business-cycle turning points (recessions, recoveries) easier to read."
    )

    roll_df = fdf[["Date", "Total-Nonfarm-Payrolls", "Unemployment-Rate"]].dropna()
    if len(roll_df) >= 12:
        roll_df = roll_df.set_index("Date")
        roll_df["Payrolls_12m"] = roll_df["Total-Nonfarm-Payrolls"].rolling(12).mean()
        roll_df["Unemp_12m"]    = roll_df["Unemployment-Rate"].rolling(12).mean()
        roll_df = roll_df.reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=roll_df["Date"], y=roll_df["Total-Nonfarm-Payrolls"],
            name="Payrolls (raw)", line=dict(color="#535457", width=1), opacity=0.5
        ))
        fig.add_trace(go.Scatter(
            x=roll_df["Date"], y=roll_df["Payrolls_12m"],
            name="Payrolls (12m avg)", line=dict(color="#1f77b4", width=2.5)
        ))
        fig.update_layout(
            title="Total Nonfarm Payrolls with 12-Month Rolling Average",
            xaxis_title="Date", yaxis_title="Employees (K)",
            hovermode="x unified", height=380
        )
        st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------------------
    # 2. Year-over-year wage growth vs. CPI inflation
    # ----------------------------------------------------------
    st.markdown("### Real Wage Pressure — YoY Wage Growth vs. CPI Inflation")
    st.markdown(
        "Year-over-year (YoY) percentage change converts both series to the same "
        "scale. Months where CPI growth exceeds wage growth represent periods of "
        "real wage erosion — workers' earnings buy less than they did a year prior."
    )

    yoy_df = fdf[["Date", "Average-Hourly-Earnings", "Consumer-Price-Index"]].dropna().copy()
    if len(yoy_df) >= 13:
        yoy_df = yoy_df.sort_values("Date").set_index("Date")
        yoy_df["Wage_YoY"] = yoy_df["Average-Hourly-Earnings"].pct_change(12) * 100
        yoy_df["CPI_YoY"]  = yoy_df["Consumer-Price-Index"].pct_change(12) * 100
        yoy_df["Real_Wage_Gap"] = yoy_df["Wage_YoY"] - yoy_df["CPI_YoY"]
        yoy_df = yoy_df.dropna().reset_index()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yoy_df["Date"], y=yoy_df["Wage_YoY"],
            name="Wage Growth (YoY %)", line=dict(color="#ff7f0e", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=yoy_df["Date"], y=yoy_df["CPI_YoY"],
            name="CPI Inflation (YoY %)", line=dict(color="#17becf", width=2)
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
        fig.update_layout(
            title="Nominal Wage Growth vs. CPI Inflation (Year-over-Year %)",
            xaxis_title="Date", yaxis_title="% Change",
            hovermode="x unified", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Real wage gap bar — positive = real gains, negative = real losses
        fig2 = go.Figure()
        colors = ["#2ca02c" if v >= 0 else "#d62728" for v in yoy_df["Real_Wage_Gap"]]
        fig2.add_trace(go.Bar(
            x=yoy_df["Date"], y=yoy_df["Real_Wage_Gap"],
            name="Real Wage Gap", marker_color=colors
        ))
        fig2.add_hline(y=0, line_color="black", line_width=1)
        fig2.update_layout(
            title="Real Wage Gap (Wage Growth − CPI Inflation)",
            xaxis_title="Date", yaxis_title="Percentage Points",
            height=350
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Green bars = real wage gains; red bars = real wage losses relative to inflation.")

    # ----------------------------------------------------------
    # 3. OLS regression
    # ----------------------------------------------------------
    st.markdown("### OLS Regression — Unemployment vs. Wage Growth")
    st.markdown(
        "This section estimates a simple OLS regression of year-over-year average hourly earnings growth "
        "on the unemployment rate. The relationship is estimated over all months in the selected date range "
        "where both series are available."
    )

    # Build regression dataset
    reg_df = fdf[["Date", "Unemployment-Rate", "Average-Hourly-Earnings"]].dropna().copy()
    reg_df = reg_df.sort_values("Date").set_index("Date")
    reg_df["Wage_YoY"] = reg_df["Average-Hourly-Earnings"].pct_change(12) * 100
    reg_df = reg_df.dropna().reset_index()

    if len(reg_df) >= 20:
        x = reg_df["Unemployment-Rate"]
        y = reg_df["Wage_YoY"]

        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()
        model = model.get_robustcov_results(cov_type='HC0')
        intercept = model.params[0]
        slope = model.params[1]
        r2 = model.rsquared
        p_value = model.pvalues[1]
        se = model.bse[1]

        # Scatter plot with regression line
        x_line = np.linspace(x.min(), x.max(), 200)
        y_line = intercept + slope * x_line

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="markers",
            name="Monthly observation",
            marker=dict(color="#7119c4", opacity=0.5, size=5),
        ))
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line,
            mode="lines",
            name=f"OLS fit (slope = {slope:.3f})",
            line=dict(color="#d62728", width=2),
        ))
        fig.update_layout(
            title="OLS Regression — Unemployment Rate vs. Wage Growth (YoY %)",
            xaxis_title="Unemployment Rate (%)",
            yaxis_title="Wage Growth (YoY %)",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Regression summary table
        # Format p-value: if very small, show in scientific notation
        p_value_str = f"{p_value:.2e}" if p_value < 0.0001 else f"{p_value:.4f}"

        reg_summary = pd.DataFrame([{
            "Intercept (β₀)": f"{intercept:.3f}",
            "Slope (β₁)": f"{slope:.3f}",
            "R²": f"{r2:.3f}",
            "p-value (slope)": p_value_str,
            "Std Error (slope)": f"{se:.4f}",
            "N": len(reg_df),
        }])

        st.dataframe(reg_summary, hide_index=True)

        st.markdown(
            f"**Interpretation:** A one-percentage-point increase in the unemployment rate is "
            f"associated with a **{slope:.2f} pp decrease** in annualized wage growth (p = {p_value_str}). "
            f"The R² of {r2:.2f} indicates the model explains about {r2 * 100:.1f}% of wage growth variation, "
            "so the relationship is statistically significant but only part of the story. "
            "The fitted model uses heteroskedasticity-robust standard errors (HC0), which helps make the "
            "inference on the slope more reliable in the presence of unequal variance. "
            "This is still a simple OLS association, not a causal estimate."
        )
    else:
        st.info("Select a longer date range to estimate the regression (at least 20 overlapping months needed).")

    # ----------------------------------------------------------
    # Cross-correlation heatmap
    # ----------------------------------------------------------
    st.markdown("### Pairwise Correlations")
    st.markdown(
        "Pearson correlations across all six series using the full date range. "
        "These are contemporaneous (same-month) correlations — they describe "
        "co-movement, not causality or lead-lag relationships."
    )
    corr_cols = [
        "Total-Nonfarm-Payrolls", "Unemployment-Rate", "Civilian-Labor-Force-Level",
        "Average-Hourly-Earnings", "Average-weekly-hours", "Consumer-Price-Index"
    ]
    available = [c for c in corr_cols if c in fdf.columns]
    corr_matrix = fdf[available].corr().round(3)

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale="RdYlGn",
        zmin=-1,
        zmax=1,
        colorbar=dict(title="Correlation"),
        text=corr_matrix.values,
        texttemplate="%{text}",
        hovertemplate="%{y} vs %{x}: %{z}<extra></extra>",
    ))
    fig.update_layout(
        title="Correlation Heatmap — Employment, Wages, and Prices",
        xaxis=dict(tickangle=-45),
        yaxis=dict(autorange="reversed"),
        height=520,
        margin=dict(l=60, r=20, t=70, b=120),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Correlation matrix values"):
        st.dataframe(corr_matrix)


# ------------------------------------------------------------------
# Raw data + download
# ------------------------------------------------------------------
st.markdown("---")
st.subheader("Raw Data")

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**Showing data for selected date range**")
with col2:
    st.download_button(
        label="Download CSV",
        data=fdf.to_csv(index=False),
        file_name=f"labor_stats_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

st.dataframe(
    fdf.sort_values("Date", ascending=False),
    use_container_width=True,
    height=300,
)

# ------------------------------------------------------------------
# Footer
# ------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:gray;font-size:0.82em;'>"
    "Data: <a href='https://www.bls.gov/developers/'>Bureau of Labor Statistics Public API</a> · "
    "Built with <a href='https://streamlit.io/'>Streamlit</a>"
    "</div>",
    unsafe_allow_html=True,
)
