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

# ---------- header ----------
st.title("🌍 Global Macroeconomic Dashboard")
st.markdown("Real-time indicators across major economies with expert analysis")

# ---------- sidebar ----------
st.sidebar.header("🔍 Settings")
country = st.sidebar.selectbox("Select Economy", ["United States"])

prefix_map = {"United States": "US"}
prefix = prefix_map[country]

# ---------- tabs ----------
tab1, tab2 = st.tabs(["📊 Dashboard", "📝 Analysis"])

with tab1:
    # ---------- metric cards (simple version) ----------
    indicators = [
        (f'{prefix}_GDP_GROWTH',    'Real GDP (billions)',   'level'),
        (f'{prefix}_INFLATION',     'CPI Index (1984=100)',  'level'),
        (f'{prefix}_UNEMPLOYMENT',  'Unemployment Rate',     'rate'),
    ]
    cols = st.columns(3)
    for i, (ind, label, ind_type) in enumerate(indicators[:3]):
        val, dt = get_latest(df, ind)
        with cols[i]:
            if val is not None:
                if ind_type == 'level':
                    formatted = f"{val:,.2f}"
                else:
                    formatted = f"{val:.2f}%"
                st.markdown(f"""
                <div class="indicator-box">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{formatted}</div>
                    <div style="color: #95a5a6; font-size:0.8rem;">as of {dt}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"No data for {label}")

    # ---------- charts ----------
    c1, c2 = st.columns(2)
    with c1:
        fig = make_chart(df, f'{prefix}_GDP_GROWTH', 'Real GDP (billions)', '#2ca02c')
        if fig: st.plotly_chart(fig, use_container_width=True)
        fig = make_chart(df, f'{prefix}_INFLATION', 'CPI Index (1984=100)', '#d62728')
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = make_chart(df, f'{prefix}_UNEMPLOYMENT', 'Unemployment Rate', '#9467bd')
        if fig: st.plotly_chart(fig, use_container_width=True)
        fig = make_chart(df, f'{prefix}_INTEREST_RATE', 'Policy Interest Rate', '#ff7f0e')
        if fig: st.plotly_chart(fig, use_container_width=True)

with tab2:
    analysis_dict = {
        "United States": ANALYSIS_US,
    }
    st.markdown(analysis_dict.get(country, "Analysis not available."))

st.markdown("---")
st.caption("Data: FRED, World Bank, Yahoo Finance | Built with Streamlit")