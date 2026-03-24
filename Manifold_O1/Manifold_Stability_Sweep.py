import sys
import random
import numpy as np
import pandas as pd
from astroquery.jplhorizons import Horizons
from datetime import datetime, timedelta

from analytical_engine_8D import Manifold8DEngine
from analytical_engine_6D import Manifold6DEngine

AU_TO_KM = 149597870.7
SPEED_OF_LIGHT_KM_S = 299792.458
C_SQ = SPEED_OF_LIGHT_KM_S ** 2
SEC_TO_DAYS = 86400.0

BODIES = [
    {'name': 'Sun',     'id': '10',  'gm': 132712440041.939},
    {'name': 'Mercury', 'id': '199', 'gm': 22031.868},
    {'name': 'Venus',   'id': '299', 'gm': 324858.592},
    {'name': 'Earth',   'id': '3',   'gm': 403503.235}, 
    {'name': 'Jupiter', 'id': '5',   'gm': 126712764.8}
]

def main():
    steps = 100
    total_days = 3650 # 10 years of daily data
    
    print("===============================================================")
    print(f"      🪐 RANDOMIZED MONTE CARLO STABILITY SWEEP: {steps} JUMPS")
    print("===============================================================")
    
    start_date = datetime.today().strftime('%Y-%m-%d')
    end_date = (datetime.today() + timedelta(days=total_days)).strftime('%Y-%m-%d')

    print(f"\n[1/3] Fetching 10-Year Daily Ground Truth Array from Horizons...")
    
    trajectories = {}
    for body in BODIES:
        print(f"      -> Downloading daily vectors for {body['name']}...")
        # Fetching 1-day steps to create a solid 3650-day database
        obj = Horizons(id=body['id'], location='@0', epochs={'start': start_date, 'stop': end_date, 'step': '1d'})
        vecs = obj.vectors()
        trajectories[body['name']] = {
            'r': np.array([vecs['x'], vecs['y'], vecs['z']]).T * AU_TO_KM,
            'v': np.array([vecs['vx'], vecs['vy'], vecs['vz']]).T * (AU_TO_KM / SEC_TO_DAYS)
        }

    print("\n[2/3] Initializing Symplectic Engines...")
    engine_8D = Manifold8DEngine(mu=BODIES[0]['gm'], c_sq=C_SQ)
    engine_6D = Manifold6DEngine(mu=BODIES[0]['gm'])
    
    results = []
    
    target_name = 'Mercury'
    target_idx = 1
    
    # Initial state (Day 0)
    r_init_sun = trajectories['Sun']['r'][0]
    v_init_sun = trajectories['Sun']['v'][0]
    r_init_target = trajectories[target_name]['r'][0] - r_init_sun
    v_init_target = trajectories[target_name]['v'][0] - v_init_sun

    # Generate 100 completely random days between Day 1 and Day 3649
    random_jump_days = sorted(random.sample(range(1, total_days), steps))

    print(f"\n[3/3] Executing {steps} Randomized Analytical Jumps for {target_name}...\n")
    
    for jump_days in random_jump_days:
        time_sec = jump_days * SEC_TO_DAYS
        
        # Ground truth for this specific random day
        r_truth_sun = trajectories['Sun']['r'][jump_days]
        r_truth_target = trajectories[target_name]['r'][jump_days] - r_truth_sun
        
        # N-Body Perturbation state at Day 0
        r_rel_0 = [trajectories[b['name']]['r'][0] - r_init_sun for b in BODIES]
        m_int_sum = sum([BODIES[j]['gm'] / max(1e-6, np.linalg.norm(r_rel_0[j] - r_init_target)**3) for j in range(1, len(BODIES)) if j != target_idx])
        pert_params = {'M_int': m_int_sum * 10.0, 'm': BODIES[4]['gm'], 'r_p_vec': r_rel_0[4]} # Jupiter is index 4

        # --- 8D PROPAGATION ---
        try:
            raw_8d = engine_8D.propagate(target_idx, BODIES, r_rel_0, [trajectories[b['name']]['v'][0] - v_init_sun for b in BODIES], time_sec, pert_params)
        except TypeError:
            raw_8d = engine_8D.propagate(r_init_target, v_init_target, time_sec, pert_params)
            
        pos_8d = raw_8d[0] if isinstance(raw_8d, tuple) else raw_8d
        metrics_8d = raw_8d[1] if isinstance(raw_8d, tuple) and len(raw_8d) > 1 else {"alpha": 1.0, "M": getattr(engine_8D, 'latest_torsion_trace', 0.0)}

        # --- 6D PROPAGATION ---
        try:
            pos_6d = engine_6D.propagate(target_idx, BODIES, r_rel_0, [trajectories[b['name']]['v'][0] - v_init_sun for b in BODIES], time_sec, pert_params)
        except TypeError:
            pos_6d = engine_6D.propagate(r_init_target, v_init_target, time_sec, pert_params)
            if isinstance(pos_6d, tuple): pos_6d = pos_6d[0]

        # --- ERROR CALCULATION ---
        actual_dist = np.linalg.norm(r_truth_target)
        error_8d = np.linalg.norm(pos_8d - r_truth_target)
        error_6d = np.linalg.norm(pos_6d - r_truth_target)
        
        # --- UNIT NORMALIZATION FOR TRACE ---
        m_torsion_day = metrics_8d['M'] * (SEC_TO_DAYS**2)
        beta_day = (m_torsion_day + np.sqrt(m_torsion_day**2 + 4.0)) / 2.0
        alpha_day = 1.0 / beta_day
        trace_sq = (alpha_day + beta_day)**2

        results.append({
            'Jump (Days)': jump_days,
            '8D Err (km)': f"{error_8d:.2f}",
            '6D Err (km)': f"{error_6d:.2f}",
            'Δ Err (km)': f"{error_6d - error_8d:.2f}",
            'Trace²': f"{trace_sq:.10f}",
            'M²': f"{m_torsion_day**2:.4e}"
        })

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    df.to_csv("Mercury_Randomized_Sweep.csv", index=False)
    print("\n✅ Sweep complete. Data saved to 'Mercury_Randomized_Sweep.csv'")

if __name__ == "__main__":
    main()