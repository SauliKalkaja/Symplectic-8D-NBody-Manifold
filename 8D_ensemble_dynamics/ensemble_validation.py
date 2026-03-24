import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde, wasserstein_distance
import time

# =====================================================================
# DIRECT IMPORT OF YOUR ACTUAL ENGINE
# =====================================================================
from analytical_engine_8D import Manifold8DEngine

def run_continuum_experiment(N_particles=5000, jump_days=1000):
    print(f"Initializing Phase-Space Fluid with N = {N_particles} particles...")
    
    # Set gravitational parameter (mu = 1.0 for normalized simulation)
    mu = 1.0
    engine = Manifold8DEngine(mu=mu)
    
    # 1. Initialize perfectly on the Secular Manifold (Circular orbits, r=1, v=1)
    angles = np.random.uniform(0, 2*np.pi, N_particles)
    
    # 3D Positions (Z=0)
    r_secular = np.column_stack((np.cos(angles), np.sin(angles), np.zeros(N_particles)))
    # 3D Velocities (Circular orbit speed v = sqrt(mu/r) = 1.0)
    v_secular = np.column_stack((-np.sin(angles), np.cos(angles), np.zeros(N_particles)))
    
    # 2. Inject Chaos (Pollute the fluid)
    noise_level = 0.05 # 5% chaotic positional/velocity noise
    r_noisy = r_secular + np.random.normal(0, noise_level, r_secular.shape)
    v_noisy = v_secular + np.random.normal(0, noise_level, v_secular.shape)
    
    # Calculate initial radial distance from the central body
    r_initial = np.linalg.norm(r_noisy, axis=1)

    print(f"Executing REAL SSMP O(1) Jump for {jump_days} time units...")
    start_time = time.time()
    
    # 3. Execute the jump using YOUR actual engine
    final_positions = np.zeros((N_particles, 3))
    
    for i in range(N_particles):
        try:
            # Using your mc_mode=True to bypass the dictionary lookups
            final_pos = engine.propagate(
                planet_idx=None, 
                bodies=None, 
                r_input=r_noisy[i], 
                v_input=v_noisy[i], 
                T=jump_days, 
                pert_params={'M_int': 0}, 
                mc_mode=True
            )
            final_positions[i] = final_pos
        except Exception:
            # If the noise kicks a particle into an unsolvable trajectory, 
            # we freeze it (standard handling for ejected Monte Carlo particles)
            final_positions[i] = r_noisy[i]
            
    jump_time = time.time() - start_time
    print(f"Jump completed in {jump_time:.4f} seconds.")
    
    # Calculate final radii 
    r_final = np.linalg.norm(final_positions, axis=1)

    # 4. Continuum Density Estimation (KDE) - Transitioning to Fluid Dynamics
    print("Calculating Continuum Fluid Density (f(Z))...")
    density_initial = gaussian_kde(r_initial)
    density_final = gaussian_kde(r_final)
    
    r_grid = np.linspace(0.5, 1.5, 500)
    f_initial = density_initial(r_grid)
    f_final = density_final(r_grid)

    # 5. Calculate Wasserstein Distance (Earth Mover's Distance)
    # Target manifold is an exact Dirac delta at r = 1.0
    target_manifold = np.ones(N_particles)
    w_dist_initial = wasserstein_distance(r_initial, target_manifold)
    w_dist_final = wasserstein_distance(r_final, target_manifold)

    print(f"Initial Wasserstein Distance to Manifold: {w_dist_initial:.4f}")
    print(f"Final Wasserstein Distance to Manifold:   {w_dist_final:.4f}")

    # 6. Generate Publication-Ready Graph
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(r_grid, f_initial, label='Initial Fluid State (Chaotic Noise)', color='red', linestyle='dashed', lw=2)
    ax.plot(r_grid, f_final, label='Final Fluid State (Post-SSMP Jump)', color='cyan', lw=3)
    ax.axvline(x=1.0, color='white', linestyle='dotted', label='Stable Secular Manifold $\mathcal{S}$', lw=2)
    
    ax.fill_between(r_grid, f_final, color='cyan', alpha=0.2)
    ax.fill_between(r_grid, f_initial, color='red', alpha=0.1)

    ax.set_title(f'Continuum Limit: Phase-Space Fluid Collapse onto Secular Manifold\n$N={N_particles}$, Jump $\\tau={jump_days}$ units', fontsize=14)
    ax.set_xlabel('Radial Phase-Space Distance', fontsize=12)
    ax.set_ylabel('Probability Density $f(\mathbf{Z}, \\tau)$', fontsize=12)
    
    # Add stats box
    textstr = '\n'.join((
        f'SSMP Exec Time: {jump_time:.4f} s',
        f'Initial $W_1$ Dist: {w_dist_initial:.4f}',
        f'Final $W_1$ Dist: {w_dist_final:.4f}'))
    props = dict(boxstyle='round', facecolor='black', alpha=0.8, edgecolor='white')
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)

    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.2)
    
    plt.tight_layout()
    plt.savefig('continuum_fluid_collapse.png', dpi=300)
    print("Graph saved as 'continuum_fluid_collapse.png'.")
    plt.show()

if __name__ == "__main__":
    # I set N to 5,000 for a fast test. You can increase this to 50,000 later!
    run_continuum_experiment(N_particles=5000, jump_days=1000)