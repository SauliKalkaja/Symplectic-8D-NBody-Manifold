import numpy as np
import pandas as pd
import json
from analytical_engine_8D import Manifold8DEngine

def get_acc(p, m, G):
    a = np.zeros_like(p)
    for i in range(len(m)):
        for j in range(len(m)):
            if i == j: continue
            rv = p[j]-p[i]; rm = np.linalg.norm(rv)
            a[i] += G * m[j] * rv / rm**3
    return a

def run_synchronized_audit():
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    G = config['constants']['G']
    bodies = list(config['bodies'].values())
    m = np.array([b['mass'] for b in bodies])
    p_rk = np.array([b['position'] for b in bodies])
    v_rk = np.array([b['velocity'] for b in bodies])
    
    T_max, dt = 50.0, 0.01
    steps = int(T_max/dt)
    
    # Engines relative to Body 1 (The Anchor)
    eng2 = Manifold8DEngine(mu=G*(m[0]+m[1]))
    eng3 = Manifold8DEngine(mu=G*(m[0]+m[2]))
    
    acc_rk = get_acc(p_rk, m, G)
    residuals = []
    
    print(f"Running Precision 3-Body Audit (T={T_max})...")
    
    for s in range(steps + 1):
        t = s * dt
        r02, v02 = p_rk[1]-p_rk[0], v_rk[1]-v_rk[0]
        r03, v03 = p_rk[2]-p_rk[0], v_rk[2]-v_rk[0]
        
        # High-Precision Sign logic: 1.0 for inner, -1.0 for outer
        pos8d_2 = eng2.propagate(r02, v02, dt, {'m': m[2], 'r_p_vec': p_rk[2]-p_rk[1], 'sign': 1.0})
        pos8d_3 = eng3.propagate(r03, v03, dt, {'m': m[1], 'r_p_vec': p_rk[1]-p_rk[2], 'sign': -1.0})
        
        p_rk_next = p_rk + v_rk * dt + 0.5 * acc_rk * dt**2
        err2 = np.linalg.norm((p_rk_next[1]-p_rk_next[0]) - pos8d_2)
        err3 = np.linalg.norm((p_rk_next[2]-p_rk_next[0]) - pos8d_3)
        residuals.append([t, err2, err3])
        
        p_rk = p_rk_next
        anext = get_acc(p_rk, m, G); v_rk += 0.5 * (acc_rk + anext) * dt; acc_rk = anext

    df = pd.DataFrame(residuals, columns=['t', 'res_body2', 'res_body3'])
    print(f"Audit Complete. Mean Residual B3: {df['res_body3'].mean():.6e}")

if __name__ == "__main__":
    run_synchronized_audit()
