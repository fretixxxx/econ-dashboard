import pandas as pd
from utils.fetch_fred import fetch_fred
from utils.fetch_wb import fetch_wb
from utils.fetch_yahoo import fetch_yahoo
from utils.fetch_tcmb import fetch_tcmb_data

def main():
    print("Fetching FRED...")
    df1 = fetch_fred()
    print("Fetching World Bank...")
    df2 = fetch_wb()
    print("Fetching Yahoo Finance...")
    df3 = fetch_yahoo()

    # 1. Combine the base data sources
    all_data = pd.concat([df1, df2, df3], ignore_index=True)

    # 2. Stop the old FRED EU_UNEMPLOYMENT data from overwriting our 2026 fix
    all_data = all_data[all_data['indicator'] != 'EU_UNEMPLOYMENT']

    # 3. Load the 2026 Euro Area data we injected and append it
    df_eurostat = pd.read_csv('data/economic_data.csv')
    df_eurostat = df_eurostat[df_eurostat['indicator'] == 'EU_UNEMPLOYMENT']
    all_data = pd.concat([all_data, df_eurostat], ignore_index=True)

    # 4. Clean, save, and print
    all_data = all_data.dropna(subset=['value'])
    all_data.to_csv('data/economic_data.csv', index=False)
    print(f"Saved {len(all_data)} rows to data/economic_data.csv")
if __name__ == '__main__':
    main()