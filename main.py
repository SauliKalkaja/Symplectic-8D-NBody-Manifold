import numpy as np
import json
from analytical_engine_8D import Manifold8DEngine

def run_synchronized_audit():
    # Load standardized configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json missing.")
        return

    # Initialize Engine with standard Heliocentric Mu
    engine = Manifold8DEngine(mu=config.get('mu', 132712440041.939))

    # Initial State (1 AU baseline)
    r0 = np.array(config['initial_r'])
    v0 = np.array(config['initial_v'])
    
    # 30-Day Analytical Jump (Secular Anchor Integral)
    T_jump = 86400.0 * 30 
    
    print("🌌 Executing Single-Body Manifold Jump...")
    print(f"   Initial Distance: {np.linalg.norm(r0):,.2f} km")

    # Perform the O(1) jump
    r_final = engine.propagate(0, None, r0, v0, T_jump, {'M_int': 0}, mc_mode=True)

    print("\n" + "─"*40)
    print(f"✅ Mirror Result (T + 30 Days)")
    print(f"   Final Distance: {np.linalg.norm(r_final):,.2f} km")
    print(f"   Stability Check: {np.linalg.norm(r_final) / np.linalg.norm(r0) * 100:.6f}% Magnitude Retention")
    print("─"*40)

if __name__ == "__main__":
    run_synchronized_audit()
