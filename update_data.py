import pandas as pd
from utils.fetch_fred import fetch_fred
from utils.fetch_wb import fetch_wb
from utils.fetch_yahoo import fetch_yahoo

def main():
    print("Fetching FRED...")
    df1 = fetch_fred()
    print("Fetching World Bank...")
    df2 = fetch_wb()
    print("Fetching Yahoo Finance...")
    df3 = fetch_yahoo()

    all_data = pd.concat([df1, df2, df3], ignore_index=True)
    all_data = all_data.dropna(subset=['value'])
    all_data.to_csv('data/economic_data.csv', index=False)
    print(f"Saved {len(all_data)} rows to data/economic_data.csv")

if __name__ == '__main__':
    main()