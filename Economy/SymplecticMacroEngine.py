import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Configuration & Symplectic Constants ---
INPUT_FILE = 'global_economic_state_multi_body.csv'
BETA_CRITICAL = 4.0      # Parabolic Ejection Threshold (Debt is 4x Real Wealth)
SCALING_FACTOR = 0.015   # Converts GDP Balance % into Geometric Torsion (M)

# Define the "Aphelion" Core (Advanced economies with reserve currencies)
GLOBAL_NORTH = [
    'USA', 'GBR', 'DEU', 'FRA', 'JPN', 'CAN', 'ITA', 'AUS', 'NLD', 
    'CHE', 'SWE', 'NOR', 'DNK', 'FIN', 'BEL', 'AUT', 'NZL', 'IRL', 
    'ESP', 'PRT', 'GRC', 'KOR', 'ISR', 'SGP'
]

def calculate_symplectic_root(balance):
    """
    Calculates the exact geometric root for spatial deformation.
    Bypasses discrete time-stepping (O(1) Analytical Propagator).
    """
    M = abs(balance) * SCALING_FACTOR
    return (M + np.sqrt(M**2 + 4.0)) / 2.0

def main():
    print("--- Igniting the Symplectic N-Body Macro Engine ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Run the fetcher script first.")
        return

    df = pd.read_csv(INPUT_FILE)
    years = sorted(df['Year'].unique())
    
    # Initialize Phase Space Manifolds for each cohort in each country
    manifolds = {}
    for country in df['Country_Code'].unique():
        manifolds[(country, 'Top_10')] = {'alpha': 1.0, 'beta': 1.0}
        manifolds[(country, 'Bottom_90')] = {'alpha': 1.0, 'beta': 1.0}

    results = []
    ejections = []

    print(f"Tracking {df['Agent_Count'].sum() / len(years):,.0f} agents across {len(df['Country_Code'].unique())} countries...")

    for year in years:
        year_data = df[df['Year'] == year]
        yearly_ejections = {'Global_North_Bot90': 0, 'Global_South_Bot90': 0, 'Top_10': 0}
        
        for _, row in year_data.iterrows():
            country = row['Country_Code']
            is_north = country in GLOBAL_NORTH
            
            # 1. Allocate Agents (The Fluid Mass)
            top10_agents = int(row['Agent_Count'] * row['Top_10_Share'])
            bot90_agents = int(row['Agent_Count']) - top10_agents
            
            # 2. Process Top 10% Manifold
            root_top = calculate_symplectic_root(row['Top_10_Balance'])
            if row['Top_10_Balance'] >= 0:
                manifolds[(country, 'Top_10')]['alpha'] *= root_top      # Surplus -> Wealth Expands
            else:
                manifolds[(country, 'Top_10')]['alpha'] *= (1.0 / root_top) # Deficit -> Wealth Condenses
            
            # The Symplectic Lock: alpha * beta = 1
            manifolds[(country, 'Top_10')]['beta'] = 1.0 / manifolds[(country, 'Top_10')]['alpha']
            
            # Check for Parabolic Ejection (e >= 1)
            if manifolds[(country, 'Top_10')]['beta'] > BETA_CRITICAL:
                yearly_ejections['Top_10'] += top10_agents
                manifolds[(country, 'Top_10')]['alpha'] = 1.0 # System reset after bankruptcy
                manifolds[(country, 'Top_10')]['beta'] = 1.0
                
            # 3. Process Bottom 90% Manifold
            root_bot = calculate_symplectic_root(row['Bottom_90_Balance'])
            if row['Bottom_90_Balance'] >= 0:
                manifolds[(country, 'Bottom_90')]['alpha'] *= root_bot
            else:
                manifolds[(country, 'Bottom_90')]['alpha'] *= (1.0 / root_bot)
                
            # The Symplectic Lock: alpha * beta = 1
            manifolds[(country, 'Bottom_90')]['beta'] = 1.0 / manifolds[(country, 'Bottom_90')]['alpha']
            
            # Check for Parabolic Ejection (e >= 1)
            if manifolds[(country, 'Bottom_90')]['beta'] > BETA_CRITICAL:
                if is_north:
                    yearly_ejections['Global_North_Bot90'] += bot90_agents
                else:
                    yearly_ejections['Global_South_Bot90'] += bot90_agents
                manifolds[(country, 'Bottom_90')]['alpha'] = 1.0 # System reset after bankruptcy
                manifolds[(country, 'Bottom_90')]['beta'] = 1.0

            # 4. Record the specific state for this year
            results.append({
                'Year': year,
                'Country': country,
                'Region': 'Global North' if is_north else 'Global South',
                'Top10_Beta': manifolds[(country, 'Top_10')]['beta'],
                'Bot90_Beta': manifolds[(country, 'Bottom_90')]['beta'],
                'Top10_Agents': top10_agents,
                'Bot90_Agents': bot90_agents
            })
            
        ejections.append({
            'Year': year,
            'Global_North_Bot90': yearly_ejections['Global_North_Bot90'],
            'Global_South_Bot90': yearly_ejections['Global_South_Bot90'],
            'Top_10_Ejections': yearly_ejections['Top_10']
        })

    print("Simulation complete. Generating visual proofs...")
    
    res_df = pd.DataFrame(results)
    ej_df = pd.DataFrame(ejections)

    # Calculate population-weighted global averages for beta
    def weighted_avg(x, col, weight_col):
        if x[weight_col].sum() == 0: return 1.0
        return np.average(x[col], weights=x[weight_col])

    global_beta = res_df.groupby(['Year', 'Region']).apply(
        lambda x: pd.Series({
            'Avg_Bot90_Beta': weighted_avg(x, 'Bot90_Beta', 'Bot90_Agents'),
            'Avg_Top10_Beta': weighted_avg(x, 'Top10_Beta', 'Top10_Agents')
        })
    ).reset_index()

    # --- PLOTTING ---
    plt.style.use('dark_background')

    # Plot 1: Beta Expansion (The Debt Buffer)
    plt.figure(figsize=(14, 7))
    sns.lineplot(data=global_beta[global_beta['Region']=='Global South'], x='Year', y='Avg_Bot90_Beta', color='crimson', label='Global South (Bottom 90%) - Perihelion', linewidth=2.5)
    sns.lineplot(data=global_beta[global_beta['Region']=='Global North'], x='Year', y='Avg_Bot90_Beta', color='orange', label='Global North (Bottom 90%) - Middle Orbit', linewidth=2.5)
    sns.lineplot(data=global_beta[global_beta['Region']=='Global North'], x='Year', y='Avg_Top10_Beta', color='cyan', label='Global North (Top 10%) - Aphelion', linewidth=2.5)
    
    plt.axhline(BETA_CRITICAL, color='red', linestyle='--', alpha=0.7, label='Parabolic Ejection Limit (Bankruptcy)')
    plt.title('Symplectic Phase-Space: Global Debt Buffer Expansion (1960-2024)', fontsize=16, pad=20)
    plt.ylabel('Beta (Debt Buffer / Leverage Multiplier)', fontsize=12)
    plt.xlabel('Year', fontsize=12)
    plt.grid(color='#333333', linestyle='--', alpha=0.5)
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.savefig('Global_Beta_Expansion.png', dpi=300)
    plt.close()

    # Plot 2: Parabolic Ejections (Systemic Collapses)
    plt.figure(figsize=(14, 7))
    plt.bar(ej_df['Year'], ej_df['Global_South_Bot90'], color='crimson', label='Global South (Bottom 90%)', alpha=0.8)
    plt.bar(ej_df['Year'], ej_df['Global_North_Bot90'], bottom=ej_df['Global_South_Bot90'], color='orange', label='Global North (Bottom 90%)', alpha=0.8)
    plt.bar(ej_df['Year'], ej_df['Top_10_Ejections'], bottom=ej_df['Global_South_Bot90']+ej_df['Global_North_Bot90'], color='cyan', label='Top 10%', alpha=0.8)
    
    plt.title('Macroscopic Ejections: Systemic Bankruptcies & Manifold Tears', fontsize=16, pad=20)
    plt.ylabel('Number of Agents Ejected', fontsize=12)
    plt.xlabel('Year', fontsize=12)
    plt.grid(color='#333333', linestyle='--', alpha=0.5, axis='y')

    # Find coordinates to annotate the historical peaks automatically
    max_y = ej_df[['Global_South_Bot90', 'Global_North_Bot90', 'Top_10_Ejections']].sum(axis=1).max()
    
    try:
        y1980s = ej_df[(ej_df['Year'] > 1980) & (ej_df['Year'] < 1990)]['Global_South_Bot90'].idxmax()
        plt.annotate('1980s Latin American\nDebt Crisis', xy=(ej_df.loc[y1980s, 'Year'], max_y*0.3), xytext=(1970, max_y*0.6), arrowprops=dict(facecolor='white', shrink=0.05, width=1, headwidth=8), color='white')
    except: pass
    
    try:
        y1997 = ej_df[(ej_df['Year'] > 1995) & (ej_df['Year'] < 2002)]['Global_South_Bot90'].idxmax()
        plt.annotate('1997 Asian Financial Crisis\n(IMF Shock)', xy=(ej_df.loc[y1997, 'Year'], max_y*0.4), xytext=(1988, max_y*0.8), arrowprops=dict(facecolor='white', shrink=0.05, width=1, headwidth=8), color='white')
    except: pass
    
    try:
        y2008 = ej_df[(ej_df['Year'] > 2005) & (ej_df['Year'] < 2012)]['Global_North_Bot90'].idxmax()
        plt.annotate('2008 Global Financial Crash', xy=(ej_df.loc[y2008, 'Year'], max_y*0.2), xytext=(2000, max_y*0.5), arrowprops=dict(facecolor='white', shrink=0.05, width=1, headwidth=8), color='white')
    except: pass

    plt.legend()
    plt.tight_layout()
    plt.savefig('Global_Parabolic_Ejections.png', dpi=300)
    plt.close()

    print("Success! Plots saved as 'Global_Beta_Expansion.png' and 'Global_Parabolic_Ejections.png'.")

if __name__ == "__main__":
    main()