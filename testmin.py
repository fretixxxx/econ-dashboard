import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from analysis.usa import ANALYSIS_US

st.set_page_config(page_title="Test", layout="wide")

@st.cache_data(ttl=3600)
def load_data():
    return pd.read_csv('data/economic_data.csv', parse_dates=['date'])

df = load_data()
st.title("Minimal Dashboard")

# Only US
prefix = "US"
ind = f'{prefix}_GDP_GROWTH'
sub = df[df['indicator'] == ind].dropna().sort_values('date')
if not sub.empty:
    fig = go.Figure(go.Scatter(x=sub['date'], y=sub['value']))
    st.plotly_chart(fig)

st.markdown("### Analysis")
st.markdown(ANALYSIS_US)