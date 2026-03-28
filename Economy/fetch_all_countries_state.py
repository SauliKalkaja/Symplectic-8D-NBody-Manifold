import pandas as pd
import requests
import numpy as np

# --- Configuration ---
START_YEAR = 1950
END_YEAR = 2026
TOTAL_AGENTS = 800000
OUTPUT_FILE = 'global_economic_state_multi_body.csv'

# World Bank Indicator Codes
INDICATORS = {
    'Gov_Balance_GDP': 'GC.NLD.TOTL.GD.ZS',  # Net lending/borrowing (% of GDP)
    'Foreign_Balance_GDP': 'BN.CAB.XOKA.GD.ZS', # Current account balance (% of GDP)
    'Gini_Index': 'SI.POV.GINI',             # Gini index (0-100)
    'Population': 'SP.POP.TOTL'              # Total Population
}

def fetch_wb_indicator(indicator_code, col_name):
    """Fetches global data for a specific indicator with pagination."""
    print(f"Fetching global data for {col_name}...")
    records = []
    page = 1
    
    while True:
        url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&date={START_YEAR}:{END_YEAR}&per_page=10000&page={page}"
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print(f"  -> Error fetching {col_name} on page {page}")
                break
                
            data = response.json()
            if len(data) < 2:
                break
                
            page_info = data[0]
            items = data[1]
            
            for item in items:
                # Filter out aggregates (World, Regions) by requiring a valid ISO3 country code
                if item['value'] is not None and item['countryiso3code']:
                    records.append({
                        'Country_Name': item['country']['value'],
                        'Country_Code': item['countryiso3code'],
                        'Year': int(item['date']),
                        col_name: float(item['value'])
                    })
            
            if page >= page_info['pages']:
                break
            page += 1
            
        except Exception as e:
            print(f"  -> Exception on page {page}: {e}")
            break

    return pd.DataFrame(records)

def gini_to_top10_share(gini_index):
    """
    The Pareto-Bifurcation Proxy.
    Converts a Gini coefficient (0-100) into a Top 10% income share 
    using the mathematical properties of the Pareto distribution.
    """
    # Convert Gini to decimal (0 to 1)
    g = gini_index / 100.0
    
    # Calculate Pareto shape parameter (alpha)
    # Gini = 1 / (2*alpha - 1) => alpha = (1 + Gini) / (2 * Gini)
    alpha = (1.0 + g) / (2.0 * g)
    
    # Calculate the share of the top P fraction (P = 0.10 for Top 10%)
    # Share = P ^ ((alpha - 1) / alpha)
    p = 0.10
    top_10_share = p ** ((alpha - 1.0) / alpha)
    return top_10_share

def main():
    print("--- Initializing Symplectic N-Body Macro Data Pipeline ---")
    
    # 1. Fetch all indicators
    dfs = []
    for col_name, ind_code in INDICATORS.items():
        df = fetch_wb_indicator(ind_code, col_name)
        dfs.append(df)
        
    # 2. Merge all DataFrames on Country and Year
    print("\nMerging massive multi-body dataset...")
    master_df = dfs[0]
    for df in dfs[1:]:
        master_df = pd.merge(master_df, df, on=['Country_Name', 'Country_Code', 'Year'], how='outer')
        
    # 3. Clean and Interpolate (Per Country)
    print("Interpolating missing geometry (Filling the gaps)...")
    master_df.sort_values(['Country_Code', 'Year'], inplace=True)
    
    # Group by country to interpolate missing years so we don't bleed data across borders
    master_df = master_df.groupby('Country_Code', group_keys=False).apply(
        lambda group: group.interpolate(method='linear').ffill().bfill()
    )
    
    # Drop countries that have absolutely zero data for critical indicators
    master_df.dropna(subset=['Population', 'Gini_Index'], inplace=True)
    
    # Fill remaining macro balances with 0 (Neutral Phase-Space) if entirely missing
    master_df['Gov_Balance_GDP'] = master_df['Gov_Balance_GDP'].fillna(0.0)
    master_df['Foreign_Balance_GDP'] = master_df['Foreign_Balance_GDP'].fillna(0.0)

    # 4. Apply The Pareto-Gini Proxy
    print("Executing Pareto Inversion for 10/90 Bifurcation...")
    master_df['Top_10_Share'] = master_df['Gini_Index'].apply(gini_to_top10_share)
    master_df['Bottom_90_Share'] = 1.0 - master_df['Top_10_Share']

    # 5. Calculate MMT Sectoral Torsion
    # Private Balance = -(Gov Balance + Foreign Balance)
    master_df['Private_Balance_GDP'] = -(master_df['Gov_Balance_GDP'] + master_df['Foreign_Balance_GDP'])
    
    # Bifurcate the geometric stress
    master_df['Top_10_Balance'] = master_df['Private_Balance_GDP'] * master_df['Top_10_Share']
    master_df['Bottom_90_Balance'] = master_df['Private_Balance_GDP'] * master_df['Bottom_90_Share']

    # 6. Distribute the 800,000 Agents (The Fluid Mass)
    print("Spawning 800,000 Phase-Space Agents proportionally by global population...")
    # Calculate total global population per year to find the country's fraction
    global_pop_per_year = master_df.groupby('Year')['Population'].transform('sum')
    master_df['Agent_Count'] = np.round((master_df['Population'] / global_pop_per_year) * TOTAL_AGENTS).astype(int)

    # 7. Final Output Formatting
    master_df = master_df[['Year', 'Country_Name', 'Country_Code', 'Population', 'Agent_Count', 
                           'Gini_Index', 'Top_10_Share', 'Gov_Balance_GDP', 'Foreign_Balance_GDP', 
                           'Private_Balance_GDP', 'Top_10_Balance', 'Bottom_90_Balance']]
    
    master_df.sort_values(['Year', 'Country_Code'], inplace=True)
    master_df.to_csv(OUTPUT_FILE, index=False)
    
    print(f"\nSuccess! N-Body Macro dataset saved to {OUTPUT_FILE}")
    print(f"Total rows (Country-Years): {len(master_df)}")
    print("\nPreview of the 2022 US & Brazil states:")
    print(master_df[(master_df['Year'] == 2022) & (master_df['Country_Code'].isin(['USA', 'BRA']))]
          [['Country_Code', 'Agent_Count', 'Top_10_Share', 'Private_Balance_GDP']])

if __name__ == "__main__":
    main()