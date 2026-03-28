import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class BifurcatedUSACrash:
    def __init__(self, torsion_scaling=4.0, critical_beta=1.4):
        """
        Initializes a Bifurcated 6D Symplectic Economic Manifold.
        We track Main Street and Wall Street as separate phase-space entities.
        """
        # Main Street Manifold (Bottom 95%)
        self.alpha_ms = 1.0
        self.beta_ms = 1.0
        
        # Wall Street Manifold (Top 5%)
        self.alpha_ws = 1.0
        self.beta_ws = 1.0
        
        self.torsion_scaling = torsion_scaling
        self.critical_beta = critical_beta
        self.prev_ms_balance = 0.0
        
        self.history = []

    def calculate_root(self, balance_pct):
        """Calculates the exact quadratic root for the Symplectic Lock based on sectoral balance."""
        m_econ = abs(balance_pct) * self.torsion_scaling
        if balance_pct < 0:
            return 2.0 / (m_econ + np.sqrt(m_econ**2 + 4)) # Squeeze
        else:
            return (m_econ + np.sqrt(m_econ**2 + 4)) / 2.0 # Relief

    def analytical_jump(self, year, gov_balance_pct, foreign_balance_pct):
        """
        Accounting Identity: (S - I) + (T - G) + (M - X) = 0
        Note: A US Trade Deficit means the Foreign sector runs a SURPLUS (M-X > 0).
        """
        # 1. Total Macro Torsion applied to the Private Sector
        total_private_balance = -(gov_balance_pct + foreign_balance_pct)
        
        # 2. The Bifurcation: Routing the Kinetic Stress
        if total_private_balance < 0:
            # THE SQUEEZE: The economy is accumulating debt.
            # Main Street is forced to absorb 90% of the deficit (Subprime debt).
            ms_balance = total_private_balance * 0.90
            ws_balance = total_private_balance * 0.10
        else:
            # THE RELIEF: The government bails out the system.
            # Wall Street absorbs 90% of the wealth injection (TARP, QE).
            ms_balance = total_private_balance * 0.10
            ws_balance = total_private_balance * 0.90
            
        # 3. Update Main Street Manifold
        scaling_ms = self.calculate_root(ms_balance)
        self.alpha_ms *= scaling_ms
        self.beta_ms = 1.0 / self.alpha_ms
        
        # 4. Update Wall Street Manifold
        scaling_ws = self.calculate_root(ws_balance)
        self.alpha_ws *= scaling_ws
        self.beta_ws = 1.0 / self.alpha_ws
        
        # 5. Bankruptcies (e >= 1 Parabolic Ejections)
        # Bankruptcies hit Main Street when their debt buffer is critically overloaded
        # AND the system experiences violent metric shear.
        metric_shear_ms = abs(ms_balance - self.prev_ms_balance)
        baseline_noise = np.random.uniform(5, 15)
        
        if self.beta_ms > self.critical_beta:
            stress_multiplier = (self.beta_ms - self.critical_beta) * 50
            # Explosive ejection when shear hits an overloaded buffer
            systemic_ejections = (metric_shear_ms * 1000) * stress_multiplier
        else:
            systemic_ejections = 0
            
        bankruptcies = baseline_noise + systemic_ejections
        
        # Log state
        self.history.append({
            'Year': year,
            'Total_Priv_Balance': total_private_balance,
            'Alpha_MS': self.alpha_ms, 'Beta_MS': self.beta_ms,
            'Alpha_WS': self.alpha_ws, 'Beta_WS': self.beta_ws,
            'Bankruptcies': bankruptcies
        })
        self.prev_ms_balance = ms_balance

    def generate_plots(self):
        df = pd.DataFrame(self.history)
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 13), sharex=True)
        fig.suptitle('Symplectic Bifurcation: The Middle-Class Squeeze (2000-2012)', fontsize=16, fontweight='bold', color='white')

        # PLOT 1: The Divergence of Real Wealth (Alpha)
        ax1.plot(df['Year'], df['Alpha_WS'], label='Wall Street Real Wealth ($\\alpha_{WS}$)', color='#f1c40f', linewidth=3)
        ax1.plot(df['Year'], df['Alpha_MS'], label='Main Street Real Wealth ($\\alpha_{MS}$)', color='#3498db', linewidth=3)
        ax1.axhline(1.0, color='white', linewidth=1, linestyle='--', alpha=0.5)
        ax1.set_title('Real Spatial Metric ($\\alpha$): The Wealth Divide', fontsize=12, color='white')
        ax1.set_ylabel('Wealth Multiplier', color='white')
        ax1.legend(loc='upper left', frameon=True, facecolor='#2c3e50', edgecolor='none', labelcolor='white')
        ax1.grid(True, alpha=0.2)

        # PLOT 2: The Crushing Debt Buffer (Beta)
        ax2.plot(df['Year'], df['Beta_WS'], label='Wall Street Debt Buffer ($\\beta_{WS}$)', color='#e67e22', linewidth=3)
        ax2.plot(df['Year'], df['Beta_MS'], label='Main Street Debt Buffer ($\\beta_{MS}$)', color='#e74c3c', linewidth=3)
        ax2.axhline(1.0, color='white', linewidth=1, linestyle='--', alpha=0.5)
        ax2.axhline(self.critical_beta, color='#ff7979', linewidth=1, linestyle=':', label='Critical $\\beta$ Threshold (Bankruptcy Zone)')
        ax2.set_title('Imaginary Buffer ($\\beta$): The Middle-Class Debt Trap', fontsize=12, color='white')
        ax2.set_ylabel('Debt/Leverage Multiplier', color='white')
        ax2.legend(loc='upper left', frameon=True, facecolor='#2c3e50', edgecolor='none', labelcolor='white')
        ax2.grid(True, alpha=0.2)

        # PLOT 3: Strict Non-Cumulative Bankruptcies
        ax3.bar(df['Year'], df['Bankruptcies'], color='#c0392b', alpha=0.8, edgecolor='black', linewidth=1.5)
        ax3.set_title('Main Street Ejections (Bankruptcies): $e \\geq 1$ Parabolic Transitions', fontsize=12, color='white')
        ax3.set_ylabel('Ejection Volume', color='white')
        ax3.set_xlabel('Year', color='white')
        ax3.set_xticks(df['Year'])
        ax3.grid(True, alpha=0.2, axis='y')

        # Dark mode styling
        for ax in [ax1, ax2, ax3]:
            ax.set_facecolor('#1e272e')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('#485460')

        fig.patch.set_facecolor('#2f3640')
        plt.savefig("BifurcatedUSACrash.png", dpi=300, bbox_inches='tight')
        plt.tight_layout()
        plt.show()

# ==========================================
# EXECUTION: The USA 2000-2012 Timeline
# ==========================================
if __name__ == "__main__":
    engine = BifurcatedUSACrash(torsion_scaling=6.0, critical_beta=1.35)
    
    # [Year, Gov Balance (T-G), Foreign Balance (M-X)]
    # Note: Trade Deficit = Foreign Surplus = Positive Capital Inflow
    usa_data = [
        # The Squeeze: Gov runs mild deficits, but massive Trade Deficits crush the Private Sector.
        (2000, 0.02, 0.04),    # Gov surplus + Trade deficit = Massive Private Squeeze
        (2001, -0.01, 0.04),   
        (2002, -0.03, 0.045),  
        (2003, -0.04, 0.05),   
        (2004, -0.035, 0.055), 
        (2005, -0.025, 0.06),  # Peak Bubble: Private sector bleeding wealth, replaced by debt
        (2006, -0.015, 0.06),  
        (2007, -0.01, 0.05),   
        
        # The Crash & Bailout: Gov runs massive deficits. Wall Street absorbs the relief.
        (2008, -0.03, 0.045),  # The crash triggers
        (2009, -0.10, 0.025),  # TARP / Massive Gov Deficit (Wall Street gets 90%)
        
        # The Recovery: Main Street left behind
        (2010, -0.08, 0.03),   
        (2011, -0.06, 0.03),   
        (2012, -0.05, 0.025)   
    ]
    
    for year, gov_bal, for_bal in usa_data:
        engine.analytical_jump(year, gov_bal, for_bal)
        
    engine.generate_plots()