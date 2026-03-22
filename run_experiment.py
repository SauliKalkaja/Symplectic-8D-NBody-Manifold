import numpy as np
import csv
from analytical_engine_8D import Manifold8DEngine

def get_acc(pos, masses, G=1.0):
    n = len(masses); acc = np.zeros((n, 3))
    for i in range(n):
        for j in range(n):
            if i == j: continue
            rv = pos[j] - pos[i]; rm = np.linalg.norm(rv)
            acc[i] += G * masses[j] * rv / (rm**3)
    return acc

def run():
    G = 1.0; masses = [4.0, 3.0, 2.0]
    p_n = np.array([[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 8.0, 2.0]])
    v_n = np.array([[0.0, 0.5, 0.1], [0.0, 1.2, -0.2], [-1.0, 0.0, 0.0]])
    dt, T_total = 0.01, 10.0
    steps = int(T_total / dt)
    
    eng2 = Manifold8DEngine(mu=G*(masses[0]+masses[1]))
    eng3 = Manifold8DEngine(mu=G*(masses[0]+masses[2]))
    r02, v02 = p_n[1]-p_n[0], v_n[1]-v_n[0]
    r03, v03 = p_n[2]-p_n[0], v_n[2]-v_n[0]
    acc_n = get_acc(p_n, masses, G)

    print("Running 8D Master Comparison...")
    with open('8d_master_comparison.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t', 'num_x2', 'num_y2', 'num_z2', 'ul_x2', 'ul_y2', 'ul_z2', 
                    'alpha2', 'M2', 'num_x3', 'num_y3', 'num_z3', 'ul_x3', 'ul_y3', 'ul_z3'])
        
        for s in range(steps + 1):
            t = s * dt
            # 8D Analytical
            ul2, d2 = eng2.propagate(r02, v02, t, {'m': masses[2], 'r_p_vec': p_n[2]-p_n[1]})
            ul3, d3 = eng3.propagate(r03, v03, t, {'m': masses[1], 'r_p_vec': p_n[1]-p_n[2]})
            # Numerical
            rn2, rn3 = p_n[1]-p_n[0], p_n[2]-p_n[0]
            w.writerow([t, *rn2, *ul2, d2['alpha'], d2['M'], *rn3, *ul3])
            
            # Verlet step
            p_n += v_n * dt + 0.5 * acc_n * dt**2
            anext = get_acc(p_n, masses, G)
            v_n += 0.5 * (acc_n + anext) * dt
            acc_n = anext
    print("Results saved to 8d_master_comparison.csv")

if __name__ == "__main__":
    run()