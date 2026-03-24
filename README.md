# 🌌 Stable Secular Manifold Propagator (SSMP)

**Breaking the O(N) Barrier in N-Body Simulations**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

SSMP is a high-performance numerical engine that replaces traditional procedural integration methods (like RK4 or Hermite) with a **Stable Secular Manifold Jump**. By treating orbital evolution as an analytical geodesic on an 8D phase-space trace, SSMP achieves **O(1) time complexity**. 

This means a 1,000-day orbital jump takes the exact same computational time as a 1-day jump.

---

## 🚀 Why Use SSMP?

- **⚡ 3,862x Speedup:** Verified side-by-side against standard 4th-order Runge-Kutta (RK4) integrators.
- **📐 O(1) Complexity:** Analytical Path Reconstruction allows for instant "time-jumping" without iterative stepping.
- **🛡️ High-Chaos Stability:** Successfully handles up to 5% positional noise and *e ≥ 1* transitions where standard methods diverge.
- **🛰️ NASA-Grade Precision:** 0.05 km mean sync drift against NASA JPL Horizons data over 30-day intervals.

---

## 📊 Benchmarks 

*Results from a 30-Day Solar System Stress Test*

| Metric | 🌌 8D Manifold (SSMP) | 🐢 Standard RK4 (Baseline) | Improvement |
| :--- | :--- | :--- | :--- |
| **Execution Time** | `0.000275 s` | `1.060217 s` | **3862.2x Faster** |
| **Complexity** | **O(1)** (Constant) | **O(N)** (Procedural) | Step-less Jump |
| **Path Drift** | `52.4 meters` | Reference | Negligible |
| **Stability** | `100%` (0 Breaches) | Variable | Manifold-Locked |

---

## ⚠️ Usage and Physical Constraints

**Note on Numerical Dissipation:** SSMP utilizes a Stable Secular Manifold approach. To ensure O(1) performance and long-term stability in chaotic regimes, it employs a Numerical Dissipation Filter. 

**Symplecticity:** While the engine preserves the Delaunay action variables within machine epsilon (ε_dp), it is **not a pure symplectic integrator**. It acts as a contractive map that suppresses high-frequency chaotic noise.

- ✅ **Best For:** Long-duration secular stability, mission planning, and galactic-scale simulations.
- ❌ **Not For:** Exact energy conservation studies, Lyapunov exponent mapping, or resonance-crossing probability analysis.

---

## 🛠️ Repository Structure

- `analytical_engine_8D.py`: The core SSMP propagator and mathematical engine.
- `8D_Solar_System_Audit.py`: Streamlit-based NASA JPL Horizons validation tool.
- `manifold_diagnostics.py`: Structural verification suite testing complexity, drift, and noise scaling.
- `hard_test_monte_carlo.py`: High-chaos comparative performance testing script.
- `main.py` & `run_experiment.py`: Entry points for running base simulations.
- `config.json`: Base configuration settings for the engine.

---

## 💻 Getting Started

### Prerequisites
Ensure you have Python installed (Python 3.8+ recommended). 

### Installation
Clone the repository and install the required dependencies:
```bash
git clone [https://github.com/SauliKalkaja/Symplectic-8D-NBody-Manifold.git](https://github.com/SauliKalkaja/Symplectic-8D-NBody-Manifold.git)
cd Symplectic-8D-NBody-Manifold
pip install -r requirements.txt
