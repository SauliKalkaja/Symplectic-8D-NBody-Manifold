# 🪐 The Symplectic Macroeconomic Engine

**A 6D/8D Phase-Space Model of Global Financial Capitalism and Modern Monetary Theory (MMT)**

Mainstream neoclassical economics traditionally models global markets as frictionless systems of infinite growth. It relies on agent-based models that treat the economy as a spreadsheet of isolated actors, consistently failing to predict the systemic debt crises that periodically fracture the global economy.

This repository proposes a radical heterodox framework: **The global economy is a continuous, gravitational phase-space fluid.** By mapping Modern Monetary Theory (MMT) sectoral balances onto a Symplectic Phase-Space Manifold, we demonstrate that runaway inequality, systemic bankruptcies, and sovereign debt crises are not "behavioral failures" or "glitches." They are strict topological requirements of a closed macroeconomic system.

## 📐 The Mathematical Framework

This engine treats the economy using the exact same $\mathcal{O}(1)$ Analytical Propagator we developed to resolve gravitational singularities in celestial mechanics. 

1. **Sectoral Balances as Geometric Torsion ($M$):** MMT dictates that a government surplus and a trade deficit mathematically drain the private sector. We quantify this macroeconomic stress as Geometric Torsion ($M$).
2. **The Symplectic Lock ($\alpha\beta = 1$):** Economic agents exist within this manifold governed by two strict conjugates:
   * **$\alpha$ (Real Space):** Real purchasing power, physical assets, retained wealth.
   * **$\beta$ (Imaginary Buffer):** Debt, leverage, credit capacity.
   To survive, agents must conserve their phase-space volume ($\alpha\beta = 1$). If the system extracts their real wealth ($\alpha < 1$), their debt buffer is mathematically forced to expand ($\beta > 1$). This is the geometric proof of the "Middle-Class Squeeze."
3. **Parabolic Ejections ($e \ge 1$):** When an agent's debt buffer ($\beta$) crosses a critical topological limit, the local manifold tears. In orbital mechanics, this is an ejection to a hyperbolic trajectory. In economics, this is systemic bankruptcy.

## 🌍 Global N-Body Simulation (1950–2026)

Instead of relying on fragile discrete time-step integration (which causes exponential drift), our $\mathcal{O}(1)$ engine evaluates static geometric path integrals. This allows us to simulate **800,000 discrete phase-space agents across 150+ nations over a 75-year timeframe** in a fraction of a second.

* **Aphelion (The Global North):** Advanced economies surf the phase space seamlessly near the baseline ($\beta \approx 1.0$), exporting their geometric stress.
* **Perihelion (The Global South):** Developing nations orbit deep within the economic gravity well, violently absorbing exported Torsion ($M$), driving their $\beta$ buffers into the parabolic danger zone.

The continuous engine natively captures historical singularities without hard-coded triggers, including:
* The 1980s Latin American Debt Crisis (Volcker Shock)
* The 1997 Asian Financial Crisis (IMF Structural Adjustments)
* The 2008 Global Financial Crash (Where metric shear finally ripped through the Global North's Bottom 90%)
* The 2020 COVID-19 Shock (Where direct fiscal routing successfully expanded $\alpha$ and compressed $\beta$)

## ⚙️ Repository Contents

* `fetch_global_economic_state.py`: Fetches and interpolates US-specific macroeconomic data (World Bank) and Top 10% / Bottom 90% bifurcations (World Inequality Database).
* `fetch_all_countries_state.py`: The global N-Body pipeline. Uses Pareto inversion on Gini coefficients to mathematically derive the topological shear boundary for every nation on Earth, dynamically allocating 800,000 agents based on historical global populations.
* `SymplecticMacroEngine.py`: The core $\mathcal{O}(1)$ mathematical propagator. Processes the data, applies the $\alpha\beta=1$ quadratic roots, calculates the real-time $\alpha/\beta$ deformation, and plots the systemic ejections.
* `global_economic_state_multi_body.csv`: The clean, generated fuel line for the 75-year global simulation.

## 🚀 How to Run

1. Install the required dependencies:
   ```bash
   pip install pandas numpy matplotlib seaborn requests
