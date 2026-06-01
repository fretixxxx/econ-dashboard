import yfinance as yf
import pandas as pd

TICKERS = {
    'US_SP500': '^GSPC',
    'JP_NIKKEI': '^N225',
    'USD_TRY': 'TRY=X',
    'EUR_USD': 'EURUSD=X',
    'USD_JPY': 'JPY=X',
    'USD_IDR': 'IDR=X',
    'US_10Y': '^TNX',
}

def fetch_yahoo():
    frames = []
    for name, ticker in TICKERS.items():
        try:
            data = yf.download(ticker, period='10y', progress=False)
            if data.empty:
                continue

            # Извлекаем Close: в зависимости от структуры колонок
            if 'Close' in data.columns:
                series = data['Close']
            elif isinstance(data.columns, pd.MultiIndex):
                series = data.xs('Close', axis=1, level=0)
            else:
                series = data.iloc[:, 0]  # fallback: первая колонка

            # Если это DataFrame, берём первый столбец
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]

            # Убираем временную зону
            series.index = pd.to_datetime(series.index).tz_localize(None)

            df = pd.DataFrame({
                'date': series.index,
                'value': series.values,
                'indicator': name
            })
            frames.append(df)
            print(f'[Yahoo] {name}')
        except Exception as e:
            print(f'[Yahoo ERROR] {name}: {e}')

    if not frames:
        print('[Yahoo] No data retrieved.')
        return pd.DataFrame(columns=['date', 'value', 'indicator'])

    return pd.concat(frames, ignore_index=True)