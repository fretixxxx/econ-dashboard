import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from analysis.usa import ANALYSIS_US

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

# ---------- helper: compute YoY growth for a level indicator ----------
def compute_yoy_growth_series(df, indicator):
    """Return a DataFrame with 'date' and 'value' as YoY percent change."""
    sub = df[df['indicator'] == indicator].sort_values('date').copy()
    if sub.empty:
        return pd.DataFrame(columns=['date', 'value'])
    
    # Find value one year earlier for each date
    yoy_values = []
    for idx, row in sub.iterrows():
        current_date = row['date']
        # target date 1 year ago
        prev_date = current_date - pd.DateOffset(years=1)
        # get closest value
        prev_val, _ = get_value_at_date(df, indicator, prev_date)
        if prev_val and prev_val != 0:
            growth = (row['value'] - prev_val) / prev_val * 100
            yoy_values.append({'date': current_date, 'value': growth})
        else:
            yoy_values.append({'date': current_date, 'value': None})
    
    growth_df = pd.DataFrame(yoy_values).dropna(subset=['value'])
    return growth_df

# ---------- header ----------
st.title("🌍 Global Macroeconomic Dashboard")
st.markdown("Real-time indicators across major economies with expert analysis")

# ---------- sidebar ----------
st.sidebar.header("🔍 Settings")
country = st.sidebar.selectbox("Select Economy", ["United States"])

# --- GDP display mode (new) ---
gdp_mode = st.sidebar.radio(
    "GDP display",
    options=["Billions", "YoY Growth %"],
    horizontal=True,
    key="gdp_mode"
)

# date filter for charts
st.sidebar.subheader("📅 Chart date range")
apply_range = st.sidebar.checkbox("Apply date range to charts", value=False)
if apply_range:
    col_s, col_e = st.sidebar.columns(2)
    with col_s:
        filter_start = st.date_input("Start", value=datetime(2020, 1, 1), key="filter_start")
    with col_e:
        filter_end = st.date_input("End", value=datetime(2026, 12, 31), key="filter_end")

prefix_map = {"United States": "US"}
prefix = prefix_map[country]

# indicator definitions (labels & types)
INDICATORS = [
    (f'{prefix}_GDP_GROWTH',    'Real GDP (billions)',   'level'),
    (f'{prefix}_INFLATION',     'CPI Index (1984=100)',  'level'),
    (f'{prefix}_INFLATION',     'Inflation Rate',        'inflation'),   # new entry for inflation %
    (f'{prefix}_UNEMPLOYMENT',  'Unemployment Rate',     'rate'),
    (f'{prefix}_INTEREST_RATE', 'Policy Interest Rate',  'rate'),
]

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

# ---------- filtered data ----------
if apply_range:
    mask = (df['date'] >= pd.to_datetime(filter_start)) & (df['date'] <= pd.to_datetime(filter_end))
    df_filtered = df[mask].copy()
else:
    df_filtered = df.copy()

# ---------- tabs ----------
tab1, tab2 = st.tabs(["📊 Dashboard", "📝 Analysis"])

# ==================== DASHBOARD TAB ====================
with tab1:

    # ---------- period growth expander ----------
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

    # ---------- metric cards (top) ----------
    # ---------- metric cards (top) ----------
    gdp_ind = f'{prefix}_GDP_GROWTH'
    cpi_ind = f'{prefix}_INFLATION'
    unemp_ind = f'{prefix}_UNEMPLOYMENT'
    rate_ind = f'{prefix}_INTEREST_RATE'

    gdp_val, gdp_date = get_latest(df_filtered, gdp_ind)
    cpi_val, cpi_date = get_latest(df_filtered, cpi_ind)
    unemp_val, unemp_date = get_latest(df_filtered, unemp_ind)
    rate_val, rate_date = get_latest(df_filtered, rate_ind)

    # GDP display logic
    if gdp_val is not None:
        if gdp_mode == "Billions":
            gdp_display = f"{gdp_val:,.2f}"
            gdp_label = "Real GDP (billions)"
        else:
            yoy_gdp = get_yoy_growth(df_filtered, gdp_ind, pd.to_datetime(gdp_date))
            gdp_display = f"{yoy_gdp:.2f}%" if yoy_gdp is not None else "N/A"
            gdp_label = "GDP Growth (YoY %)"
    else:
        gdp_display = "N/A"
        gdp_label = "Real GDP"

    # Inflation rate (always YoY %)
    if cpi_val is not None:
        yoy_cpi = get_yoy_growth(df_filtered, cpi_ind, pd.to_datetime(cpi_date))
        cpi_display = f"{yoy_cpi:.2f}%" if yoy_cpi is not None else "N/A"
    else:
        cpi_display = "N/A"

    # Unemployment & interest rate are percentages
    unemp_display = f"{unemp_val:.2f}%" if unemp_val is not None else "N/A"
    rate_display = f"{rate_val:.2f}%" if rate_val is not None else "N/A"

    # Display three metric cards
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
        # --- GDP Growth (YoY %) instead of level ---
        gdp_growth_df = compute_yoy_growth_series(df_filtered, f'{prefix}_GDP_GROWTH')
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

        # --- CPI Level chart ---
        fig_cpi = make_chart(df_filtered, f'{prefix}_INFLATION', 'CPI Index (1984=100)', '#d62728')
        if fig_cpi: st.plotly_chart(fig_cpi, use_container_width=True)

    with c2:
        fig_unemp = make_chart(df_filtered, f'{prefix}_UNEMPLOYMENT', 'Unemployment Rate', '#9467bd')
        if fig_unemp: st.plotly_chart(fig_unemp, use_container_width=True)
        fig_rate = make_chart(df_filtered, f'{prefix}_INTEREST_RATE', 'Cental Bank Interest Rate', '#ff7f0e')
        if fig_rate: st.plotly_chart(fig_rate, use_container_width=True)

# ==================== ANALYSIS TAB ====================
with tab2:
    analysis_dict = {
        "United States": ANALYSIS_US,
    }
    st.markdown(analysis_dict.get(country, "Analysis not available."))

# ---------- footer ----------
st.markdown("---")
st.caption("Data: FRED, World Bank, Yahoo Finance | Built with Streamlit")