import numpy as np
from scipy.optimize import newton

class Manifold8DEngine:
    def __init__(self, mu, c_light=299792.458):
        self.mu = mu 
        self.c_sq = c_light**2
        self.Gamma_16D = 3.0 / 16.0  # Volumetric coupling from 16D trace [cite: 121, 123]
        self.phi = (1 + np.sqrt(5)) / 2.0 

    def _solve_kepler(self, M, e):
        """Unified solver for the baseline temporal flow."""
        if e < 1.0:
            E0 = M if e < 0.8 else np.pi
            func = lambda E: E - e * np.sin(E) - M
            fprime = lambda E: 1 - e * np.cos(E)
        else:
            E0 = np.arcsinh(M/e) if M > 0 else M
            func = lambda H: e * np.sinh(H) - H - M
            fprime = lambda H: e * np.cosh(H) - 1
        try: return newton(func, E0, fprime=fprime, tol=1e-12)
        except: return M 

    def propagate(self, planet_idx, bodies, r_input, v_input, T, pert_params, mc_mode=False):
        # 1. Coordinate & Element Extraction [cite: 74, 106]
        if mc_mode:
            r0, v0 = r_input, v_input
            mu_eff = self.mu
        else:
            r0, v0 = r_input[planet_idx], v_input[planet_idx]
            mu_eff = self.mu + bodies[planet_idx]['gm']

        r_mag0, v_sq0 = np.linalg.norm(r0), np.sum(v0**2)
        h_vec = np.cross(r0, v0); h_mag = np.linalg.norm(h_vec)
        energy = (0.5 * v_sq0) - (mu_eff / r_mag0)
        a = -mu_eff / (2 * energy)
        e_vec = (np.cross(v0, h_vec) / mu_eff) - (r0 / r_mag0)
        e = np.linalg.norm(e_vec)

        # 3D Frame Extraction for NASA alignment
        i_angle = np.arccos(np.clip(h_vec[2] / h_mag, -1, 1))
        n_node = np.array([-h_vec[1], h_vec[0], 0]); n_mag = np.linalg.norm(n_node)
        Omega = np.arccos(np.clip(n_node[0]/n_mag, -1, 1)) if n_mag != 0 else 0
        if n_mag != 0 and n_node[1] < 0: Omega = 2*np.pi - Omega
        
        # 2. Keplerian Baseline (The 'Time' component) [cite: 106, 162]
        cos_nu0 = np.clip(np.dot(e_vec, r0) / (max(1e-9, e * r_mag0)), -1, 1)
        nu_0 = np.arccos(cos_nu0)
        if np.dot(r0, v0) < 0: nu_0 = 2*np.pi - nu_0
        
        if e < 1.0:
            M_0 = (2*np.arctan(np.sqrt((1-e)/(1+e))*np.tan(nu_0/2))) - e*np.sin(2*np.arctan(np.sqrt((1-e)/(1+e))*np.tan(nu_0/2)))
        else:
            H_0 = 2 * np.arctanh(np.sqrt((e-1)/(e+1)) * np.tan(nu_0/2))
            M_0 = e * np.sinh(H_0) - H_0
        
        M_T = M_0 + np.sqrt(mu_eff / abs(a**3)) * T
        sol_T = self._solve_kepler(M_T, e)
        
        if e < 1.0:
            nu_T = 2 * np.arctan(np.sqrt((1+e)/(1-e)) * np.tan(sol_T / 2))
            r_inv_mag = abs(a) * (1 - e * np.cos(sol_T))
        else:
            nu_T = 2 * np.arctan(np.sqrt((e+1)/(e-1)) * np.tanh(sol_T / 2))
            r_inv_mag = abs(a) * (e * np.cosh(sol_T) - 1)

        # 3. 8D Metric Supervision (Scaling ratio) [cite: 19, 43, 179]
        M_0_manifold = (3.0 * mu_eff / (50.0 * r_mag0**3)) + pert_params.get('M_int', 0)
        M_f_manifold = (3.0 * mu_eff / (50.0 * r_inv_mag**3)) + pert_params.get('M_int', 0)
        
        alpha_start = 1.0 / ((abs(M_0_manifold) + np.sqrt(M_0_manifold**2 + 4)) / 2.0)
        alpha_end = 1.0 / ((abs(M_f_manifold) + np.sqrt(M_f_manifold**2 + 4)) / 2.0)

        # 4. Phase Precession [cite: 108, 164]
        if n_mag == 0:
            omega_start = np.arctan2(e_vec[1], e_vec[0])
        else:
            omega_start = np.arccos(np.clip(np.dot(n_node, e_vec) / (n_mag * e), -1, 1))
            if e_vec[2] < 0: omega_start = 2*np.pi - omega_start

        precession = (M_f_manifold * (r_inv_mag - r_mag0)) * self.Gamma_16D
        omega_f = omega_start + precession

        # 5. Final Position Reconstruction
        r_plane = np.array([r_inv_mag * np.cos(nu_T), r_inv_mag * np.sin(nu_T), 0])
        
        # Rotation Matrices [cite: 159, 288]
        R3_W = np.array([[np.cos(Omega), -np.sin(Omega), 0], [np.sin(Omega), np.cos(Omega), 0], [0, 0, 1]])
        R1_i = np.array([[1, 0, 0], [0, np.cos(i_angle), -np.sin(i_angle)], [0, np.sin(i_angle), np.cos(i_angle)]])
        R3_w = np.array([[np.cos(omega_f), -np.sin(omega_f), 0], [np.sin(omega_f), np.cos(omega_f), 0], [0, 0, 1]])
        
        # Apply Frame Rotation + Metric Scaling ratio
        return (R3_W @ R1_i @ R3_w) @ r_plane * (alpha_end / alpha_start)