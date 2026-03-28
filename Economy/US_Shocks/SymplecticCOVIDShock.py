import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class SymplecticCOVIDShock:
    def __init__(self, torsion_scaling=4.0, critical_beta=1.35):
        """
        Pristine, Frictionless Bifurcated 6D Symplectic Economic Manifold.
        """
        self.alpha_ms = 1.0
        self.beta_ms = 1.0
        self.alpha_ws = 1.0
        self.beta_ws = 1.0
        
        self.torsion_scaling = torsion_scaling
        self.critical_beta = critical_beta
        self.prev_ms_balance = 0.0
        
        self.history = []

    def calculate_root(self, balance_pct):
        """PRISTINE CORE: Exact quadratic root for the Symplectic Lock."""
        m_econ = abs(balance_pct) * self.torsion_scaling
        if balance_pct < 0:
            return 2.0 / (m_econ + np.sqrt(m_econ**2 + 4)) # Squeeze
        else:
            return (m_econ + np.sqrt(m_econ**2 + 4)) / 2.0 # Relief

    def analytical_jump(self, year, gov_balance_pct, foreign_balance_pct):
        # 1. Total Macro Torsion applied to the Private Sector
        # (S-I) = (G-T) + (X-M). Note: Gov Deficit is negative, Trade Deficit is positive.
        total_private_balance = -(gov_balance_pct + foreign_balance_pct)
        
        # 2. The Bifurcation Routing: 2020 vs 2008 differences
        if total_private_balance < 0:
            # THE SQUEEZE: Main Street still absorbs 90% of structural decay
            ms_balance = total_private_balance * 0.90
            ws_balance = total_private_balance * 0.10
        else:
            # THE RELIEF (COVID STIMULUS)
            # Unlike 2008 (90/10 split), Stimulus checks & PPP route massive capital to Main Street.
            # We model a 60% Wall Street (QE/Bailouts) / 40% Main Street (Checks/UI) split.
            ms_balance = total_private_balance * 0.40
            ws_balance = total_private_balance * 0.60
            
        # 3. Update Main Street Manifold
        self.alpha_ms *= self.calculate_root(ms_balance)
        self.beta_ms = 1.0 / self.alpha_ms
        
        # 4. Update Wall Street Manifold
        self.alpha_ws *= self.calculate_root(ws_balance)
        self.beta_ws = 1.0 / self.alpha_ws
        
        # 5. Instant Topological Ejections (e >= 1)
        metric_shear_ms = abs(ms_balance - self.prev_ms_balance)
        
        # If Beta is artificially lowered by stimulus, bankruptcies drop BELOW baseline
        if self.beta_ms > self.critical_beta:
            stress_multiplier = (self.beta_ms - self.critical_beta) * 50
            systemic_ejections = (metric_shear_ms * 1000) * stress_multiplier
            baseline_noise = np.random.uniform(5, 15)
        else:
            systemic_ejections = 0
            # A healthy/stimulus-injected Beta reduces the natural failure rate
            health_bonus = max(0, (1.1 - self.beta_ms) * 20) 
            baseline_noise = max(1, np.random.uniform(5, 15) - health_bonus)
            
        bankruptcies = baseline_noise + systemic_ejections
        
        self.history.append({
            'Year': year,
            'Alpha_MS': self.alpha_ms, 'Beta_MS': self.beta_ms,
            'Alpha_WS': self.alpha_ws, 'Beta_WS': self.beta_ws,
            'Bankruptcies': bankruptcies
        })
        self.prev_ms_balance = ms_balance

    def generate_plots(self):
        df = pd.DataFrame(self.history)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 13), sharex=True)
        fig.suptitle('Symplectic Policy Test: The COVID-19 Direct Stimulus (2016-2023)', fontsize=16, fontweight='bold', color='white')

        # PLOT 1: Real Wealth (Alpha)
        ax1.plot(df['Year'], df['Alpha_WS'], label='Wall Street Wealth ($\\alpha_{WS}$)', color='#f1c40f', linewidth=3)
        ax1.plot(df['Year'], df['Alpha_MS'], label='Main Street Wealth ($\\alpha_{MS}$)', color='#3498db', linewidth=3)
        ax1.axhline(1.0, color='white', linewidth=1, linestyle='--', alpha=0.5)
        ax1.set_title('Real Spatial Metric ($\\alpha$): The 40% Main Street Injection', fontsize=12, color='white')
        ax1.set_ylabel('Wealth Multiplier', color='white')
        ax1.legend(loc='upper left', frameon=True, facecolor='#2c3e50', edgecolor='none', labelcolor='white')
        ax1.grid(True, alpha=0.2)

        # PLOT 2: Debt Buffer (Beta)
        ax2.plot(df['Year'], df['Beta_WS'], label='Wall Street Debt Buffer ($\\beta_{WS}$)', color='#e67e22', linewidth=3)
        ax2.plot(df['Year'], df['Beta_MS'], label='Main Street Debt Buffer ($\\beta_{MS}$)', color='#e74c3c', linewidth=3)
        ax2.axhline(1.0, color='white', linewidth=1, linestyle='--', alpha=0.5)
        ax2.axhline(self.critical_beta, color='#ff7979', linewidth=1, linestyle=':', label='Critical $\\beta$ Threshold')
        ax2.set_title('Imaginary Buffer ($\\beta$): Stimulus Pulls Main Street from the Edge', fontsize=12, color='white')
        ax2.set_ylabel('Debt/Leverage', color='white')
        ax2.legend(loc='upper right', frameon=True, facecolor='#2c3e50', edgecolor='none', labelcolor='white')
        ax2.grid(True, alpha=0.2)

        for ax in [ax1, ax2]:
            ax.set_facecolor('#1e272e')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('#485460')

        fig.patch.set_facecolor('#2f3640')
        plt.savefig("SymplecticCOVIDShock.png", dpi=300, bbox_inches='tight')
        plt.tight_layout()
        plt.show()

# ==========================================
# EXECUTION: The COVID-19 Timeline (2016-2023)
# ==========================================
if __name__ == "__main__":
    engine = SymplecticCOVIDShock(torsion_scaling=6.0, critical_beta=1.35)
    
    # [Year, Gov Balance (T-G), Foreign Balance (M-X)]
    usa_data = [
        # The Pre-COVID Squeeze (Steady baseline, creeping debt)
        (2016, -0.03, 0.025),  
        (2017, -0.035, 0.028), 
        (2018, -0.04, 0.03),   
        (2019, -0.045, 0.028), 
        
        # The COVID Shock: Massive Deficits, but routed 40% to Main Street
        (2020, -0.15, 0.03),   # Massive 15% Gov Deficit
        (2021, -0.12, 0.035),  # Continued heavy stimulus
        
        # The Fiscal Cliff & Inflation Squeeze
        (2022, -0.05, 0.04),   # Stimulus shuts off violently. Trade deficit grows. 
        (2023, -0.06, 0.03)    # Main street resumes absorbing the structural squeeze.
    ]
    
    for year, gov_bal, for_bal in usa_data:
        engine.analytical_jump(year, gov_bal, for_bal)
        
    engine.generate_plots()