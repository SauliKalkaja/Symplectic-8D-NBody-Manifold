import numpy as np
import json
from analytical_engine_8D import Manifold8DEngine

def run_single_body_audit():
    # Load the flat-structure config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json missing.")
        return

    # Initialize Engine using the new class name and flat keys
    # The theory now uses 'mu' (GM) directly to calculate the torsion M
    mu_val = config.get('mu', 132712440041.939)
    engine = Manifold8DEngine(mu=mu_val)

    # Initial State Vectors (1 AU Baseline)
    r0 = np.array(config['initial_r'])
    v0 = np.array(config['initial_v'])
    
    # 30-Day Analytical Jump
    T_jump = 86400.0 * 30 
    
    # Interaction torsion is zero for a single-body test
    pert_params = {'M_int': 0.0}

    print("🌌 Executing Single-Body Manifold Jump...")
    print(f"   Initial Distance: {np.linalg.norm(r0):,.2f} km")

    # Perform the O(1) Analytical Jump
    # In this framework, the path is a geodesic that preserves det(J)=1
    r_final = engine.propagate(0, None, r0, v0, T_jump, pert_params, mc_mode=True)

    print("\n" + "─"*40)
    print(f"✅ Jump Result (T + 30 Days)")
    print(f"   Final Distance: {np.linalg.norm(r_final):,.2f} km")
    print(f"   Stability Check: {np.linalg.norm(r_final) / np.linalg.norm(r0) * 100:.6f}% Magnitude Retention")
    print("─"*40)

if __name__ == "__main__":
    run_single_body_audit()
