# Symplectic 8D NBody Manifold

**Authors:** Sauli Kälkäjä & Google Gemini  
[cite_start]**Date:** March 22, 2026 [cite: 3, 171]

## 🌌 Overview
[cite_start]This project introduces a novel analytical framework for resolving gravitational singularities and the N-body problem by extending classical 4D spacetime into an **8D Complex Hermitian Manifold**[cite: 174, 189]. [cite_start]Traditional numerical integration methods often suffer from cumulative energy drift and coordinate breakdown as radial distances approach the singularity ($r \rightarrow 0$)[cite: 175, 186]. [cite_start]By utilizing a spatiotemporal buffer space $X^{\mu}$ and a zero-trace torsion matrix $\mathbf{M}$, this engine expresses gravitational potential as a volume-preserving symplectic rotation rather than a scalar divergence[cite: 176, 192].

## 🚀 Key Mathematical Pillars
* [cite_start]**Analytical Jumps:** The framework replaces incremental numerical stepping with global analytical jumps, providing a stable, high-precision solution for complex orbital dynamics[cite: 179, 316].
* [cite_start]**Parabolic Transition Rule:** This rule allows for seamless phase rotation between bound elliptical ($e < 1$) and unbound hyperbolic ($e \ge 1$) states without mathematical discontinuity[cite: 177, 227].
* [cite_start]**Symplectic Integrity:** The system ensures that the determinant of the Jacobian $\det(\mathbf{J})$ remains strictly unity, allowing for global analytical jumps across the manifold without numerical drift[cite: 219, 245].
* [cite_start]**Golden Ratio Lock:** The spatial condensation factor $\alpha_s$ is derived as a function of the Golden Ratio ($\phi \approx 1.618$), establishing an equilibrium condition for perfect circular motion[cite: 247, 262].
* [cite_start]**Symplectic Lorentz Invariance:** The manifold maintains the identity $\alpha_s \cdot \beta_s = 1$, ensuring that physical condensation of space-time is balanced by an inverse rotation into imaginary buffer dimensions[cite: 245, 246].

## 📊 Performance Benchmarks (365-Day NASA Audit)
The model's validity is demonstrated through a 365-day analytical jump of the Solar System. [cite_start]Results are compared against NASA JPL Horizons ground truth state vectors[cite: 178, 615].

| Planet | 8D Dist (AU) | NASA Dist (AU) | Position Error (km) |
| :--- | :--- | :--- | :--- |
| **Mercury** | 0.328489 | 0.328489 | **255.92** |
| **Venus** | 0.725829 | 0.725820 | 7,259.91 |
| **Earth** | 0.990997 | 0.991001 | 6,381.34 |
| **Jupiter** | 5.422467 | 5.422403 | 10,371.35 |
| **Saturn** | 10.065969 | 10.065473 | 104,693.33 |

**System Statistics:**
* [cite_start]**System RMSE:** 64,379.05 km [cite: 178]
* [cite_start]**Mean Distance Accuracy:** 99.999393% [cite: 178]
* [cite_start]**Computation Speed:** < 0.01 seconds for a 1-year jump [cite: 179]

## 📂 Repository Structure
[cite_start]The repository includes the following primary computational components[cite: 1012]:
* `analytical_engine_8D.py`: The core 8D manifold propagator incorporating Jacobian partitioning and Parabolic Transition logic.
* `8D_Solar_System_Audit.py`: The validation suite used to synchronize with NASA JPL Horizons for analytical jump testing.
* `run_experiment.py` & `main.py`: Frameworks for multi-run Monte Carlo stability and chaos analysis.
* `config.json`: The centralized parameter manifest for manifold-specific constants ($\kappa$, $\lambda$) and initial state vectors.

## 🛠️ Usage
To replicate the NASA JPL Horizons audit, install the required dependencies (`numpy`, `scipy`, `pandas`, `astroquery`, `streamlit`) and execute:

```bash
streamlit run 8D_Solar_System_Audit.py
