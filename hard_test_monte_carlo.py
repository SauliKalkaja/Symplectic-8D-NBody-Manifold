import numpy as np
import json
import time
from analytical_engine_8D import Manifold8DEngine

# --- RK4 Physics Engine ---
def get_accel(r, mu):
    return -mu * r / (np.linalg.norm(r)**3)

def rk4_step(r, v, dt, mu):
    k1_v = get_accel(r, mu)
    k1_r = v
    k2_v = get_accel(r + 0.5*dt*k1_r, mu)
    k2_r = v + 0.5*dt*k1_v
    k3_v = get_accel(r + 0.5*dt*k2_r, mu)
    k3_r = v + 0.5*dt*k2_v
    k4_v = get_accel(r + dt*k3_r, mu)
    k4_r = v + dt*k3_v
    
    v_new = v + (dt/6.0)*(k1_v + 2*k2_v + 2*k3_v + k4_v)
    r_new = r + (dt/6.0)*(k1_r + 2*k2_r + 2*k3_r + k4_r)
    return r_new, v_new

def run_comparative_stress_test(iterations=100):
    with open('config.json', 'r') as f:
        config = json.load(f)

    mu = config['mu']
    engine = Manifold8DEngine(mu=mu)
    
    T_total = 86400.0 * 30  # 30 Days
    dt_rk4 = 60.0           # 60-second steps
    steps = int(T_total / dt_rk4)

    print(f"🔥 Starting Comparative Stress Test: 12D Manifold vs RK4")
    print(f"   ({iterations} runs | {steps} steps per RK4 run)\n")

    manifold_times = []
    rk4_times = []
    drifts = []
    breaches = 0

    for i in range(iterations):
        # 1. Randomized Initial State (5% Noise)
        noise = np.random.normal(0, 0.05, 3)
        r0 = np.array(config['initial_r']) * (1.0 + noise)
        v0 = np.array(config['initial_v'])

        # --- 2. THE ANALYTICAL JUMP ---
        t0 = time.perf_counter()
        r_8d = engine.propagate(0, None, r0, v0, T_total, {'M_int': 0}, mc_mode=True)
        manifold_times.append(time.perf_counter() - t0)

        # --- 3. THE RK4 STEPPING ---
        t1 = time.perf_counter()
        r_rk, v_rk = r0.copy(), v0.copy()
        for _ in range(steps):
            r_rk, v_rk = rk4_step(r_rk, v_rk, dt_rk4, mu)
        rk4_times.append(time.perf_counter() - t1)

        # 4. Compare results
        drift = np.linalg.norm(r_8d - r_rk)
        if np.isnan(drift) or drift > 1e6: # Breach if drift > 1000km
            breaches += 1
        else:
            drifts.append(drift)

        if (i+1) % 10 == 0:
            print(f"   Progress: {i+1}/{iterations} runs...")

    avg_8d = np.mean(manifold_times)
    avg_rk = np.mean(rk4_times)
    
    print("\n" + "█" * 45)
    print(f"📊 STRESS TEST COMPLETE")
    print(f"   Manifold Stability: {(1 - breaches/iterations)*100:.2f}%")
    print(f"   Avg Manifold Time:  {avg_8d:.6f} s")
    print(f"   Avg RK4 Time:       {avg_rk:.6f} s")
    print(f"   Speedup Factor:     {avg_rk / avg_8d:.1f}x faster")
    print(f"   Mean Sync Drift:    {np.mean(drifts):.4f} km")
    print("█" * 45)

if __name__ == "__main__":
    run_comparative_stress_test()
