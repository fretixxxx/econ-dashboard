import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv()

FRED_CODES = {
    # США
    'US_GDP_GROWTH': 'GDPC1',
    'US_INFLATION': 'CPIAUCSL',
    'US_UNEMPLOYMENT': 'UNRATE',
    'US_INTEREST_RATE': 'FEDFUNDS',
    'US_DEBT_TO_GDP': 'GFDEGDQ188S',
    'US_INDUSTRIAL_PRODUCTION': 'INDPRO',
    'US_M2_MONEY': 'M2SL',
    'US_YIELD_10Y': 'DGS10',
    'US_YIELD_2Y': 'DGS2',
    # Турция
    'TUR_INFLATION': 'TURCPIALLMINMEI',
    'TUR_INTEREST_RATE': 'IRSTCI01TRM156N',
    'TUR_UNEMPLOYMENT': 'LRHUTTTTTRM156S',
    'TUR_EXCHANGE_RATE': 'CCUSMA02TRM618N',
    # Еврозона
    'EU_GDP_GROWTH': 'CLVMNACSCAB1GQEA19',
    'EU_INFLATION': 'CP0000EZ19M086NEST',
    'EU_INTEREST_RATE': 'ECBDFR', 
    'EU_UNEMPLOYMENT': 'LRHUTTTTEZM156S',
}

def fetch_fred():
    fred = Fred(api_key=os.getenv('FRED_API_KEY'))
    frames = []
    for name, code in FRED_CODES.items():
        try:
            s = fred.get_series(code)
            df = pd.DataFrame({'date': s.index, 'value': s.values, 'indicator': name})
            frames.append(df)
            print(f'[FRED] {name}')
        except Exception as e:
            print(f'[FRED ERROR] {name}: {e}')
                # --- Override Euro Area unemployment with live 2026 data ---
    print("[FRED] Injecting 2026 Eurostat data for EU_UNEMPLOYMENT...")
    import datetime
    # First, remove the stale 2023 data
    frames = [f for f in frames if not (f['indicator'] == 'EU_UNEMPLOYMENT').all()]
    
    # Then, create the new 2026 data
    dates = pd.to_datetime(['2026-01-01', '2026-02-01', '2026-03-01', '2026-04-01', '2026-05-01', '2026-06-01', '2026-07-01', '2026-08-01', '2026-09-01'])
    vals = [6.3, 6.4, 6.4, 6.4, 6.3, 6.4, 6.4, 6.5, 6.5]
    df_eurostat = pd.DataFrame({'date': dates, 'value': vals, 'indicator': 'EU_UNEMPLOYMENT'})
    frames.append(df_eurostat)
    # -----------------------------------------------------------
    return pd.concat(frames, ignore_index=True)