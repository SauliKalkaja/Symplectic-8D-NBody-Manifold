import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import wasserstein_distance
import time

# Import your engine
from analytical_engine_8D import Manifold8DEngine

def run_noise_sweep(N_particles=10000, num_steps=100, jump_days=1000):
    print(f"Starting Noise Sweep: {num_steps} steps from 1% to 95% noise.")
    print(f"Particles per run: {N_particles} | Total jumps: {N_particles * num_steps}")
    
    mu = 1.0
    engine = Manifold8DEngine(mu=mu)
    
    # Define our noise levels (from 0.01 to 0.95)
    noise_levels = np.linspace(0.01, 0.95, num_steps)
    
    # Data storage for our single master plot
    w_distances = []
    survival_rates = []
    exec_times = []
    
    # Target manifold is an exact Dirac delta at r = 1.0
    target_manifold = np.ones(N_particles)

    total_start_time = time.time()

    for idx, noise in enumerate(noise_levels):
        # 1. Initialize Perfectly Secular States
        angles = np.random.uniform(0, 2*np.pi, N_particles)
        r_secular = np.column_stack((np.cos(angles), np.sin(angles), np.zeros(N_particles)))
        v_secular = np.column_stack((-np.sin(angles), np.cos(angles), np.zeros(N_particles)))
        
        # 2. Inject the specific noise level for this run
        r_noisy = r_secular + np.random.normal(0, noise, r_secular.shape)
        v_noisy = v_secular + np.random.normal(0, noise, v_secular.shape)
        
        # 3. Execute the jump
        final_positions = np.zeros((N_particles, 3))
        survived = 0
        
        run_start = time.time()
        for i in range(N_particles):
            try:
                final_pos = engine.propagate(
                    planet_idx=None, bodies=None, 
                    r_input=r_noisy[i], v_input=v_noisy[i], 
                    T=jump_days, pert_params={'M_int': 0}, mc_mode=True
                )
                final_positions[i] = final_pos
                
                # Check if it stayed bound (rough heuristic: didn't fly off to infinity)
                if np.linalg.norm(final_pos) < 50.0:
                    survived += 1
            except Exception:
                # Ejected or mathematically unstable due to extreme noise
                final_positions[i] = r_noisy[i] * 1000 # Send to "infinity"
                
        run_time = time.time() - run_start
        exec_times.append(run_time)
        
        # 4. Calculate metrics
        r_final = np.linalg.norm(final_positions, axis=1)
        
        # Filter out extreme ejections (r > 50) from the Wasserstein calculation 
        # so we are measuring the bound fluid disk, not the escaping gas
        bound_r_final = r_final[r_final < 50.0]
        bound_target = np.ones(len(bound_r_final))
        
        if len(bound_r_final) > 0:
            w_dist = wasserstein_distance(bound_r_final, bound_target)
        else:
            w_dist = np.nan # Total systemic destruction
            
        w_distances.append(w_dist)
        survival_rates.append((survived / N_particles) * 100)
        
        # Print progress every 10 steps
        if (idx + 1) % 10 == 0:
            print(f"Step {idx+1}/{num_steps} | Noise: {noise*100:.0f}% | W1 Dist: {w_dist:.2f} | Survival: {survival_rates[-1]:.1f}%")

    print(f"\nSweep completed in {time.time() - total_start_time:.2f} seconds.")

    # 5. Generate the Master Plot
    plt.style.use('dark_background')
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Axis 1: Wasserstein Distance (Dispersion)
    color1 = 'cyan'
    ax1.set_xlabel('Injected Chaotic Noise (%)', fontsize=12)
    ax1.set_ylabel('Fluid Dispersion ($W_1$ Distance)', color=color1, fontsize=12)
    ax1.plot(noise_levels * 100, w_distances, color=color1, lw=3, label='Macro-Dispersion')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.2)

    # Axis 2: Survival Rate (Bound particles)
    ax2 = ax1.twinx()  
    color2 = 'red'
    ax2.set_ylabel('System Survival Rate (%)', color=color2, fontsize=12)  
    ax2.plot(noise_levels * 100, survival_rates, color=color2, lw=2, linestyle='dashed', label='Bound Particles')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(0, 105)

    plt.title(f'SSMP Phase-Mixing Sweep: {num_steps} Runs, $N={N_particles}$/run, $\\tau={jump_days}$ units', fontsize=14)
    
    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right')

    plt.tight_layout()
    plt.savefig('noise_scaling_sweep.png', dpi=300)
    print("Graph saved as 'noise_scaling_sweep.png'.")
    plt.show()

if __name__ == "__main__":
    run_noise_sweep(N_particles=10000, num_steps=100, jump_days=1000)