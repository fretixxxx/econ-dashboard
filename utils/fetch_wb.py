import wbdata
import pandas as pd

WB_CODES = {
    'JP_GDP_GROWTH': ('NY.GDP.MKTP.KD.ZG', 'JPN'),
    'JP_INFLATION': ('FP.CPI.TOTL.ZG', 'JPN'),
    'JP_UNEMPLOYMENT': ('SL.UEM.TOTL.ZS', 'JPN'),
    'ID_GDP_GROWTH': ('NY.GDP.MKTP.KD.ZG', 'IDN'),
    'ID_INFLATION': ('FP.CPI.TOTL.ZG', 'IDN'),
    'ID_UNEMPLOYMENT': ('SL.UEM.TOTL.ZS', 'IDN'),
    'TUR_GDP_GROWTH': ('NY.GDP.MKTP.KD.ZG', 'TUR'),
}

def fetch_wb():
    frames = []
    for name, (indicator, country) in WB_CODES.items():
        try:
            data = wbdata.get_dataframe({indicator: indicator}, country=country)
            if data.empty:
                continue
            data = data.reset_index()
            data.columns = ['date', 'value']
            data['indicator'] = name
            data['date'] = pd.to_datetime(data['date'], errors='coerce')
            data = data.dropna(subset=['date'])
            frames.append(data)
            print(f'[WB] {name}')
        except Exception as e:
            print(f'[WB ERROR] {name}: {e}')
    return pd.concat(frames, ignore_index=True)