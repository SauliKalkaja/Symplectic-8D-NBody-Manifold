import numpy as np
import json
from analytical_engine_8D import Manifold8DEngine

def run_test():
    with open('config.json', 'r') as f:
        config = json.load(f)

    engine = Manifold8DEngine(mu=config['mu'])
    r0 = np.array(config['initial_r'])
    v0 = np.array(config['initial_v'])
    
    # 30-day Analytical Jump
    r_f = engine.propagate(0, None, r0, v0, 86400.0 * 30, {'M_int': 0}, mc_mode=True)
    
    print(f"Initial: {np.linalg.norm(r0):,.2f} km")
    print(f"Final:   {np.linalg.norm(r_f):,.2f} km")
    print(f"Stability: {np.linalg.norm(r_f)/np.linalg.norm(r0)*100:.6f}%")

if __name__ == "__main__":
    run_test()