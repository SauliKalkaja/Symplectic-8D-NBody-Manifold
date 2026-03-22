import numpy as np
import pandas as pd
import json
from analytical_engine_8D import MultiBody8DEngine

def get_acc(p, m, G):
    a = np.zeros_like(p)
    for i in range(len(m)):
        for j in range(len(m)):
            if i == j: continue
            rv = p[j]-p[i]; rm = np.linalg.norm(rv)
            a[i] += G * m[j] * rv / rm**3
    return a

def run_monte_carlo(num_tests=100):
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    G = config['constants']['G']
    m_base = np.array([b['mass'] for b in config['bodies'].values()])
    p_base = np.array([b['position'] for b in config['bodies'].values()])
    v_base = np.array([b['velocity'] for b in config['bodies'].values()])
    
    T_max, dt = 10.0, 0.01
    steps = int(T_max/dt)
    mc_results = []

    print(f"Starting Multi-Body Monte Carlo ({num_tests} runs)...")
    
    for i in range(num_tests):
        m = m_base * (1 + np.random.uniform(-0.1, 0.1, 3))
        p_rk = p_base + np.random.uniform(-0.5, 0.5, (3, 3))
        v_rk = v_base + np.random.uniform(-0.1, 0.1, (3, 3))
        
        bodies = [{'name': f'body_{j}', 'gm': G*m[j]} for j in range(3)]
        engine = MultiBody8DEngine(mu_sun=bodies[0]['gm'])
        acc_rk = get_acc(p_rk, m, G)
        err2_sum, err3_sum = 0, 0
        
        for s in range(steps):
            r_vecs = p_rk - p_rk[0]
            v_vecs = v_rk - v_rk[0]
            
            pj2 = engine.propagate(1, bodies, r_vecs, v_vecs, dt)
            pj3 = engine.propagate(2, bodies, r_vecs, v_vecs, dt)
            
            p_rk_next = p_rk + v_rk * dt + 0.5 * acc_rk * dt**2
            err2_sum += np.linalg.norm((p_rk_next[1]-p_rk_next[0]) - pj2)
            err3_sum += np.linalg.norm((p_rk_next[2]-p_rk_next[0]) - pj3)
            
            p_rk = p_rk_next
            anext = get_acc(p_rk, m, G); v_rk += 0.5 * (acc_rk + anext) * dt; acc_rk = anext

        mc_results.append({'id': i+1, 'mean_b2': err2_sum/steps, 'mean_b3': err3_sum/steps})

    df = pd.DataFrame(mc_results)
    df.to_csv('monte_carlo_validation.csv', index=False)
    print(df.describe()[['mean_b2', 'mean_b3']])

if __name__ == "__main__":
    run_monte_carlo()
