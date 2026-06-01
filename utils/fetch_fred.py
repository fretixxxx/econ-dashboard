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
    'EU_GDP_GROWTH': 'EUNGDP',
    'EU_INFLATION': 'CP0000EZ19M086NEST',
    'EU_UNEMPLOYMENT': 'LRHUTTTTEZM156S',
    'EU_INTEREST_RATE': 'ECBDFR', 
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
    return pd.concat(frames, ignore_index=True)