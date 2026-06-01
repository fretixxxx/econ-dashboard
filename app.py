import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from analysis.usa import ANALYSIS_US
from analysis.turkey import ANALYSIS_TUR

# ---------- page config & styles ----------
st.set_page_config(page_title="Global Economic Dashboard", layout="wide", page_icon="🌍")

st.markdown("""
<style>
.indicator-box {
    background: #ffffff;
    padding: 1.2rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 1rem;
}
.metric-value {
    font-size: 2.2rem;
    font-weight: bold;
    color: #1f77b4;
}
.metric-label {
    font-size: 0.9rem;
    color: #7f8c8d;
    text-transform: uppercase;
    letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# ---------- data loading ----------
@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv('data/economic_data.csv', parse_dates=['date'])
    return df

df = load_data()

def get_value_at_date(df, indicator, target_date):
    """Return the value of indicator closest to target_date."""
    sub = df[(df['indicator'] == indicator) & (df['date'].notna())].copy()
    if sub.empty:
        return None, None
    sub['diff'] = (sub['date'] - pd.to_datetime(target_date)).abs()
    closest = sub.loc[sub['diff'].idxmin()]
    return closest['value'], closest['date']

def get_yoy_growth(df, indicator, current_date):
    """Compute year-over-year percent change for an indicator at a specific date."""
    prev_date = current_date - pd.DateOffset(years=1)
    val_current, _ = get_value_at_date(df, indicator, current_date)
    val_prev, _ = get_value_at_date(df, indicator, prev_date)
    if val_current is not None and val_prev is not None and val_prev != 0:
        return (val_current - val_prev) / val_prev * 100
    return None

def compute_yoy_growth_series(df, indicator):
    """Return a DataFrame with 'date' and 'value' as YoY percent change."""
    sub = df[df['indicator'] == indicator].sort_values('date').copy()
    if sub.empty:
        return pd.DataFrame(columns=['date', 'value'])
    
    yoy_values = []
    for idx, row in sub.iterrows():
        current_date = row['date']
        prev_date = current_date - pd.DateOffset(years=1)
        prev_val, _ = get_value_at_date(df, indicator, prev_date)
        if prev_val and prev_val != 0:
            growth = (row['value'] - prev_val) / prev_val * 100
            yoy_values.append({'date': current_date, 'value': growth})
        else:
            yoy_values.append({'date': current_date, 'value': None})
    
    growth_df = pd.DataFrame(yoy_values).dropna(subset=['value'])
    return growth_df

def get_latest(df, indicator):
    sub = df[df['indicator'] == indicator].dropna(subset=['value'])
    if sub.empty:
        return None, None
    last = sub.sort_values('date').iloc[-1]
    return last['value'], last['date'].strftime('%b %d, %Y')

def make_chart(df, indicator, title, color='#1f77b4'):
    sub = df[df['indicator'] == indicator].dropna().sort_values('date')
    if sub.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sub['date'], y=sub['value'],
        line=dict(color=color, width=2.5),
        fill='tozeroy',
        fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.1)'
    ))
    fig.update_layout(
        title=title,
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode='x unified',
        template='plotly_white'
    )
    return fig

# ---------- country configuration ----------
COUNTRY_CONFIG = {
    "United States": {
        "prefix": "US",
        "gdp_is_level": True,      # GDP stored as billions -> need toggle + YoY calc
        "inflation_is_level": True, # CPI index -> need YoY calc
    },
    "Turkey": {
        "prefix": "TUR",
        "gdp_is_level": False,      # GDP already a growth rate
        "inflation_is_level": False, # Inflation already a growth rate
    },
}

# ---------- header ----------
st.title("🌍 Global Macroeconomic Dashboard")
st.markdown("Real-time indicators across major economies with expert analysis")

# ---------- sidebar ----------
st.sidebar.header("🔍 Settings")
country = st.sidebar.selectbox("Select Economy", list(COUNTRY_CONFIG.keys()))

config = COUNTRY_CONFIG[country]
prefix = config["prefix"]
gdp_is_level = config["gdp_is_level"]
inflation_is_level = config["inflation_is_level"]

# GDP toggle only for the US (where GDP is a level)
if gdp_is_level:
    gdp_mode = st.sidebar.radio(
        "GDP display",
        options=["Billions", "YoY Growth %"],
        horizontal=True,
        key="gdp_mode"
    )
else:
    gdp_mode = None  # no toggle

# Date filter for charts
st.sidebar.subheader("📅 Chart date range")
apply_range = st.sidebar.checkbox("Apply date range to charts", value=False)
if apply_range:
    col_s, col_e = st.sidebar.columns(2)
    with col_s:
        filter_start = st.date_input("Start", value=datetime(2020, 1, 1), key="filter_start")
    with col_e:
        filter_end = st.date_input("End", value=datetime(2026, 12, 31), key="filter_end")

# ---------- filtered data ----------
if apply_range:
    mask = (df['date'] >= pd.to_datetime(filter_start)) & (df['date'] <= pd.to_datetime(filter_end))
    df_filtered = df[mask].copy()
else:
    df_filtered = df.copy()

# ---------- tabs ----------
tab1, tab2 = st.tabs(["📊 Dashboard", "📝 Analysis"])

with tab1:

    # ---------- period growth expander ----------
    # Only show when GDP is a level (US) – otherwise the calculation is meaningless
    if gdp_is_level:
        with st.expander("📈 Calculate GDP / Inflation growth for a custom period", expanded=False):
            colA, colB, colC = st.columns(3)
            with colA:
                growth_start = st.date_input("Start date", value=datetime(2024, 1, 1), key="growth_start")
            with colB:
                growth_end = st.date_input("End date", value=datetime(2025, 1, 1), key="growth_end")
            with colC:
                st.write("")
                st.write("")
                if st.button("Compute Growth"):
                    gdp_ind = f'{prefix}_GDP_GROWTH'
                    cpi_ind = f'{prefix}_INFLATION'

                    val_gdp_start, _ = get_value_at_date(df, gdp_ind, growth_start)
                    val_gdp_end, _   = get_value_at_date(df, gdp_ind, growth_end)
                    val_cpi_start, _ = get_value_at_date(df, cpi_ind, growth_start)
                    val_cpi_end, _   = get_value_at_date(df, cpi_ind, growth_end)

                    if val_gdp_start is None or val_gdp_end is None:
                        st.error("Insufficient GDP data for this date range.")
                    elif val_cpi_start is None or val_cpi_end is None:
                        st.error("Insufficient CPI data for this date range.")
                    else:
                        gdp_change = (val_gdp_end - val_gdp_start) / val_gdp_start * 100
                        cpi_change = (val_cpi_end - val_cpi_start) / val_cpi_start * 100

                        days = (growth_end - growth_start).days
                        years = days / 365.25

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("GDP Total Change", f"{gdp_change:.2f}%")
                            if years >= 1.0:
                                gdp_cagr = ((val_gdp_end / val_gdp_start) ** (1 / years) - 1) * 100
                                st.caption(f"Annualized (CAGR): {gdp_cagr:.2f}% over {years:.1f} years")
                        with col2:
                            st.metric("CPI Total Change", f"{cpi_change:.2f}%")
                            if years >= 1.0:
                                cpi_cagr = ((val_cpi_end / val_cpi_start) ** (1 / years) - 1) * 100
                                st.caption(f"Annualized: {cpi_cagr:.2f}% over {years:.1f} years")

    # ---------- metric cards ----------
    gdp_ind = f'{prefix}_GDP_GROWTH'
    cpi_ind = f'{prefix}_INFLATION'
    unemp_ind = f'{prefix}_UNEMPLOYMENT'
    rate_ind = f'{prefix}_INTEREST_RATE'

    gdp_val, gdp_date = get_latest(df_filtered, gdp_ind)
    cpi_val, cpi_date = get_latest(df_filtered, cpi_ind)
    unemp_val, unemp_date = get_latest(df_filtered, unemp_ind)
    rate_val, rate_date = get_latest(df_filtered, rate_ind)

    # --- GDP card ---
    if gdp_val is not None:
        if gdp_is_level and gdp_mode == "Billions":
            gdp_display = f"{gdp_val:,.2f}"
            gdp_label = "Real GDP (billions)"
        else:
            if gdp_is_level:
                yoy_gdp = get_yoy_growth(df_filtered, gdp_ind, pd.to_datetime(gdp_date))
                gdp_display = f"{yoy_gdp:.2f}%" if yoy_gdp is not None else "N/A"
            else:
                gdp_display = f"{gdp_val:.2f}%"  # already a growth rate
            gdp_label = "GDP Growth (YoY %)"
    else:
        gdp_display = "N/A"
        gdp_label = "GDP Growth"

    # --- Inflation card ---
    if cpi_val is not None:
        if inflation_is_level:
            yoy_cpi = get_yoy_growth(df_filtered, cpi_ind, pd.to_datetime(cpi_date))
            cpi_display = f"{yoy_cpi:.2f}%" if yoy_cpi is not None else "N/A"
        else:
            cpi_display = f"{cpi_val:.2f}%"
    else:
        cpi_display = "N/A"

    unemp_display = f"{unemp_val:.2f}%" if unemp_val is not None else "N/A"
    rate_display = f"{rate_val:.2f}%" if rate_val is not None else "N/A"

    cols = st.columns(3)
    card_data = [
        (gdp_label, gdp_display, gdp_date),
        ("Inflation Rate", cpi_display, cpi_date),
        ("Unemployment Rate", unemp_display, unemp_date),
    ]

    for i, (label, value, dt) in enumerate(card_data):
        with cols[i]:
            st.markdown(f"""
            <div class="indicator-box">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div style="color: #95a5a6; font-size:0.8rem;">as of {dt if dt else 'N/A'}</div>
            </div>
            """, unsafe_allow_html=True)

    # ---------- charts ----------
    c1, c2 = st.columns(2)
    with c1:
        # --- GDP chart ---
        if gdp_is_level:
            # US: show YoY growth series
            gdp_growth_df = compute_yoy_growth_series(df_filtered, gdp_ind)
            if not gdp_growth_df.empty:
                fig_gdp = go.Figure()
                fig_gdp.add_trace(go.Scatter(
                    x=gdp_growth_df['date'], y=gdp_growth_df['value'],
                    line=dict(color='#2ca02c', width=2.5),
                    fill='tozeroy',
                    fillcolor='rgba(44,160,44,0.1)'
                ))
                fig_gdp.update_layout(
                    title='GDP Growth (YoY %)',
                    height=300,
                    margin=dict(l=10, r=10, t=40, b=10),
                    hovermode='x unified',
                    template='plotly_white'
                )
                st.plotly_chart(fig_gdp, use_container_width=True)
            else:
                st.warning("Not enough data to compute GDP growth.")
        else:
            # Turkey: already a growth rate, just plot directly
            fig_gdp = make_chart(df_filtered, gdp_ind, 'GDP Growth (YoY %)', '#2ca02c')
            if fig_gdp: st.plotly_chart(fig_gdp, use_container_width=True)

        # --- Inflation chart ---
        infl_title = 'CPI Index (1984=100)' if inflation_is_level else 'Inflation Rate (YoY %)'
        fig_infl = make_chart(df_filtered, cpi_ind, infl_title, '#d62728')
        if fig_infl: st.plotly_chart(fig_infl, use_container_width=True)

    with c2:
        fig_unemp = make_chart(df_filtered, unemp_ind, 'Unemployment Rate', '#9467bd')
        if fig_unemp: st.plotly_chart(fig_unemp, use_container_width=True)

        fig_rate = make_chart(df_filtered, rate_ind, 'Policy Interest Rate', '#ff7f0e')
        if fig_rate: st.plotly_chart(fig_rate, use_container_width=True)

with tab2:
    analysis_dict = {
        "United States": ANALYSIS_US,
        "Turkey": ANALYSIS_TUR,
    }
    st.markdown(analysis_dict.get(country, "Analysis not available."))

st.markdown("---")
st.caption("Data: FRED, World Bank, Yahoo Finance | Built with Streamlit")