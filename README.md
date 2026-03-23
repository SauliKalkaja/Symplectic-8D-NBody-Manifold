# 🌌 Stable Secular Manifold Propagator (SSMP)
**Breaking the Procedural Barrier in Orbital Mechanics & Ensemble Dynamics**

SSMP is a high-performance numerical engine that replaces traditional procedural integration (like RK4 or Hermite) with a **Stable Secular Manifold Jump**. By treating orbital evolution against a central potential as an analytical geodesic on an 8D phase-space trace, SSMP achieves **O(1) time complexity per particle**—meaning a 1,000-day jump takes the exact same computational time as a 1-day jump.

Originally designed for precision single-body simulations, the SSMP architecture has been scaled to model **Macroscopic Ensemble Dynamics**, acting as an ultra-fast, rigorous statistical tool for simulating the natural phase-mixing of highly perturbed debris disks and planetary rings.

---

## 🚀 The Hook: Why Use SSMP?

* ⚡ **3,862x Speedup:** Verified side-by-side against standard 4th-order Runge-Kutta (RK4) integrators in discrete solar system stress tests.
* 📐 **O(1) Temporal Complexity:** Bypasses iterative $\mathcal{O}(N_{\text{steps}})$ procedural discretization entirely.
* 🛡️ **High-Chaos Stability:** Natively resolves extreme kinetic noise and $e \ge 1$ hyperbolic transitions where standard methods stall or mathematically crash.
* 🛰️ **NASA-Grade Secular Precision:** 0.05 km mean sync drift against the NASA JPL Horizons database over 30-day intervals.
* 🌌 **Macroscopic Phase-Mixing:** Accurately models the natural radial dispersion and kinetic ejection of massive (10,000+ particle) debris disks in seconds.

---

## 📊 Part 1: Discrete Validation (The Baseline)
Tested over a 30-Day Solar System Stress Test against standard RK4 procedural integration.

| Metric | 8D Manifold (SSMP) | Standard RK4 (Baseline) | Improvement |
| :--- | :--- | :--- | :--- |
| **Execution Time** | 0.000275 s | 1.060217 s | **3862.2x Faster** |
| **Complexity** | O(1) (Constant) | O(N) (Procedural) | Step-less Jump |
| **Path Drift** | 52.4 meters | Reference | Negligible |
| **Stability** | 100% (0 Breaches) | Variable | Manifold-Locked |

---

## 🌊 Part 2: Macroscopic Ensemble Dynamics
To evaluate the engine's viability for statistical mechanics and macroscopic systems, the SSMP was stress-tested using a massive Monte Carlo parameter sweep.

**The Benchmark:** 1,000,000 independent analytical jumps (10,000 particles across 100 noise intervals) over a secular integration time of 1,000 units. 
**Execution Time:** ~12 seconds on standard consumer hardware. *(For comparison, a standard adaptive-step integrator would require $\mathcal{O}(10^9 - 10^{10})$ force evaluations to achieve this).*

![Ensemble Phase-Mixing](ensemble_dynamics/noise_scaling_sweep.png)
*(Above: Macroscopic phase-mixing and survival rates of the ensemble as a function of injected kinetic chaos. The solid cyan line represents the radial dispersion via the 1st Wasserstein distance, while the dashed red line tracks the bound survival fraction.)*

### Key Empirical Discoveries:
1.  **Natural Radial Dispersion (< 15% Noise):** The engine correctly propagates altered eccentricities and semi-major axes. This results in the natural, physically expected Hamiltonian phase-mixing of the debris disk into a wider steady-state radial distribution.
2.  **The Escape Threshold (> 15% Noise):** As kinetic variance pushes elements across the $e \ge 1$ boundary layer, the survival rate cleanly drops. The engine natively resolves the physical ejection and escape trajectories of the particles without crashing the solver.

---

## ⚠️ Usage and Physical Scope

**Note on System Architecture:** This engine evaluates discrete analytical jumps for test particles against a **fixed central potential**. 

* **Symplecticity:** While the engine preserves the Delaunay action variables within machine epsilon, it is *not* a standard procedural symplectic integrator. 
* **Best For:** Long-duration secular stability, mission planning, macro-scale debris disk phase-mixing, and statistical orbital mechanics.
* **Not For:** Simulating mutual, self-gravitating $N$-body interactions (where particles dynamically pull on each other), or exact microscopic energy conservation studies.

---

## 🛠️ Repository Structure

* `analytical_engine_8D.py` : The core O(1) SSMP mathematical propagator.
* 📁 **`discrete_validation/`** : Tools for tracking specific planetary bodies.
    * `8D_Solar_System_Audit.py` : Streamlit-based NASA JPL Horizons validation tool.
    * `manifold_diagnostics.py` : Structural verification suite.
* 📁 **`ensemble_dynamics/`** : Tools for macroscopic statistical evaluation.
    * `ensemble_validation.py` : Kernel Density Estimation (KDE) of the phase-space fluid.
    * `noise_scaling_sweep.py` : Monte Carlo macroscopic stress test.

---

## 📜 License & Acknowledgments

This project is open-source (MIT License). It represents a multi-year journey into the geometry of the N-body problem, refined through an iterative AI-assisted formulation and rigorous computational physics peer-review audits.
