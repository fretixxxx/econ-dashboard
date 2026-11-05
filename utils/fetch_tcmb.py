import os
import pandas as pd
from evdspy import get_series
from dotenv import load_dotenv

load_dotenv()

def fetch_tcmb_data():
    api_key = os.getenv('EVDS_API_KEY')
    if not api_key:
        print("[TCMB ERROR] No EVDS_API_KEY found in .env")
        return pd.DataFrame()

    frames = []
    
    # Series Codes:
    # TP.FG.J0 = CPI (Consumer Price Index)
    # TP.ISG.UNM = Unemployment Rate (You may need to verify this exact code on EVDS)
    series_map = {
        'TP.FG.J0': 'TUR_INFLATION_RAW',
        # 'TP.ISG.UNM': 'TUR_UNEMPLOYMENT_RAW'  # Uncomment once code is verified
    }

    for code, name in series_map.items():
        try:
            # Fetch data starting from 2010 to calculate YoY properly
            df = get_series(code, start_date="01-01-2010", api_key=api_key)
            if df is None or df.empty:
                continue
                
            # evdspy returns a dataframe with a date column and value column
            # Rename columns for consistency
            df = df.rename(columns={df.columns[0]: 'date', df.columns[1]: 'value'})
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date', 'value'])
            df = df.sort_values('date')
            
            if name == 'TUR_INFLATION_RAW':
                # Calculate YoY % change (12 months)
                df['value'] = df['value'].pct_change(periods=12) * 100
                df['indicator'] = 'TUR_INFLATION'
            else:
                df['indicator'] = name
                
            df = df.dropna(subset=['value'])
            frames.append(df[['date', 'value', 'indicator']])
            print(f"[TCMB] Fetched {name}")
            
        except Exception as e:
            print(f"[TCMB ERROR] {name}: {e}")

    if not frames:
        return pd.DataFrame()
        
    return pd.concat(frames, ignore_index=True)