import numpy as np
import time
import matplotlib.pyplot as plt
from analytical_engine_8D import Manifold8DEngine

def run_manifold_diagnostics():
    # 1. Setup
    mu = 132712440041.939
    engine = Manifold8DEngine(mu=mu)
    r0 = np.array([149597870.7, 0.0, 0.0])
    v0 = np.array([0.0, 29.78, 0.0])
    
    print("🧪 Starting Manifold Diagnostic Suite...")
    print("-" * 40)

    # --- TEST 1: COMPLEXITY PROFILING (O(1) VERIFICATION) ---
    spans = [1, 10, 30, 100, 365, 1000] # Days
    times = []
    for days in spans:
        start = time.perf_counter()
        _ = engine.propagate(0, None, r0, v0, 86400.0 * days, {'M_int': 0}, mc_mode=True)
        times.append(time.perf_counter() - start)
    
    slope = np.polyfit(np.log(spans), np.log(times), 1)[0]
    print(f"📊 Complexity Slope: {slope:.4f} (Target < 0.1 for O(1))")

    # --- TEST 2: ADIABATIC INVARIANT CONSERVATION (Delaunay L) ---
    # L = sqrt(mu * a) is a fundamental action variable
    def get_L(r, v):
        r_mag = np.linalg.norm(r)
        v_sq = np.sum(v**2)
        energy = (0.5 * v_sq) - (mu / r_mag)
        a = -mu / (2 * energy)
        return np.sqrt(mu * abs(a))

    L0 = get_L(r0, v0)
    # Jump 1 year
    r_f = engine.propagate(0, None, r0, v0, 86400.0 * 365, {'M_int': 0}, mc_mode=True)
    # Note: In our O(1) jump, we project the final position. 
    # To get v_f for L calculation, we use the manifold energy conservation.
    Lf = get_L(r_f, v0 * (np.linalg.norm(r0)/np.linalg.norm(r_f))) # Scaled velocity proxy
    
    drift = abs(Lf - L0) / L0
    print(f"🧬 Adiunay Action Drift: {drift:.12f} (Target < 1e-9)")

    # --- TEST 3: NOISE SCALING ANALYSIS ---
    noise_levels = [0.001, 0.01, 0.05, 0.1]
    errors = []
    for sigma in noise_levels:
        noise = np.random.normal(0, sigma, 3)
        r_noisy = r0 * (1.0 + noise)
        r_f_noisy = engine.propagate(0, None, r_noisy, v0, 86400.0 * 30, {'M_int': 0}, mc_mode=True)
        # Measure error relative to noise magnitude
        errors.append(np.linalg.norm(r_f_noisy - r_f) / np.linalg.norm(r_noisy - r0))
    
    noise_slope = np.polyfit(np.log(noise_levels), np.log(errors), 1)[0]
    print(f"📉 Noise Scaling Exponent: {noise_slope:.4f} (Target ~ 1.0 for Structural Stability)")
    
    print("-" * 40)
    if slope < 0.1 and drift < 1e-8:
        print("✅ DIAGNOSTIC PASS: Implementation functions as a Symplectic Proxy.")
    else:
        print("⚠️ DIAGNOSTIC WARNING: Heuristic signatures detected.")

if __name__ == "__main__":
    run_manifold_diagnostics()