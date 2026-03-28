import requests
import pandas as pd
import numpy as np

# --- 1. WORLD BANK API INDICATORS ---
# The mapping between real-world metrics and our Symplectic Engine variables
INDICATORS = {
    "SP.POP.TOTL": "Population",
    "SI.POV.GINI": "Gini_Index",                 # Shapes the variance of alpha (Wealth Inequality)
    "BN.CAB.XOKA.GD.ZS": "Trade_Balance_Pct",    # X - M (Foreign Torsion)
    "GC.NLD.TOTL.GD.ZS": "Gov_Balance_Pct"       # G - T (Public Torsion)
}

def fetch_world_bank_data(indicator_code, indicator_name):
    print(f"Fetching {indicator_name}...")
    # mrnev=1 fetches the Most Recent Non-Empty Value for each country
    url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&per_page=300&mrnev=1"
    
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {indicator_name}")
        return pd.DataFrame()
        
    data = response.json()[1] # The first element is metadata, the second is the data array
    
    # Extract relevant fields
    cleaned_data = []
    for item in data:
        # Filter out aggregate regions (like "World", "Euro area", "Arab World")
        if item['country']['value'] and not item['countryiso3code'] == "":
            cleaned_data.append({
                "Country": item['country']['value'],
                "ISO3": item['countryiso3code'],
                indicator_name: item['value'],
                f"{indicator_name}_Year": item['date']
            })
            
    return pd.DataFrame(cleaned_data)

def build_global_matrix():
    print("Initiating World Bank API Data Ingestion...")
    
    # Fetch all data separately
    dfs = []
    for code, name in INDICATORS.items():
        df = fetch_world_bank_data(code, name)
        dfs.append(df)
        
    # Merge them together on Country Code
    master_df = dfs[0]
    for i in range(1, len(dfs)):
        master_df = pd.merge(master_df, dfs[i], on=["Country", "ISO3"], how="outer")

    # --- 2. DATA CLEANING & PREP ---
    print("Cleaning data and applying Symplectic translations...")
    
    # Calculate the global median Gini to use as a fallback
    median_gini = master_df['Gini_Index'].median()
    
    # Fill missing data with geometrically neutral baseline values
    master_df.fillna({
        'Population': 1000000,          # Nominal baseline population
        'Gini_Index': median_gini,      # Global average wealth distribution
        'Trade_Balance_Pct': 0.0,       # Zero trade torsion
        'Gov_Balance_Pct': 0.0          # Zero public deficit torsion
    }, inplace=True)
    
    # Optional: Drop rows that literally have no country name attached
    master_df.dropna(subset=['Country'], inplace=True)
    
    # Sort by largest economies/populations
    master_df = master_df.sort_values(by="Population", ascending=False).reset_index(drop=True)
    
    # We'll take the top 50 countries with complete data
    #master_df = master_df.head(50)

    # --- 3. SYMPLECTIC METRIC TRANSLATION ---
    # Convert percentages to decimals for the 6D Torsion Math
    master_df['Trade_Balance_Dec'] = master_df['Trade_Balance_Pct'] / 100.0
    master_df['Gov_Balance_Dec'] = master_df['Gov_Balance_Pct'] / 100.0
    
    # Calculate initial Sectoral Torsion (M) for each Sovereign
    # M = sqrt((G-T)^2 + (X-M)^2 + (S-I)^2)
    # Since S-I = -(G-T + X-M)
    master_df['Private_Balance_Dec'] = -(master_df['Gov_Balance_Dec'] + master_df['Trade_Balance_Dec'])
    
    master_df['Sovereign_Torsion_M'] = np.sqrt(
        master_df['Gov_Balance_Dec']**2 + 
        master_df['Trade_Balance_Dec']**2 + 
        master_df['Private_Balance_Dec']**2
    )
    
    # Calculate Sovereign Leverage (beta) required to survive current torsion
    # beta = (M + sqrt(M^2 + 4)) / 2
    M_val = master_df['Sovereign_Torsion_M']
    master_df['Sovereign_Leverage_Beta'] = (M_val + np.sqrt(M_val**2 + 4.0)) / 2.0
    
    # Calculate Gini Variance (to distribute citizen wealth later)
    # A Gini of 40 = 0.4. We'll use this as the standard deviation for the alpha distribution
    master_df['Alpha_Variance'] = master_df['Gini_Index'] / 100.0

    # Save to CSV
    filename = "global_economic_state.csv"
    master_df.to_csv(filename, index=False)
    print(f"\nSuccess! Initial State Vectors saved to {filename}")
    print(master_df[['Country', 'Gini_Index', 'Gov_Balance_Pct', 'Trade_Balance_Pct', 'Sovereign_Torsion_M']].head(10))

if __name__ == "__main__":
    build_global_matrix()