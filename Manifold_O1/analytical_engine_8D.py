import numpy as np
from scipy.optimize import newton

class Manifold8DEngine:
    def __init__(self, mu, c_sq=10000.0):
        self.mu = mu
        self.c_sq = c_sq
        self.lambda_opt = 10.0  # Optimized Tidal Coupling

    def _solve_kepler(self, M, e):
        """Standard Kepler solver for the invariant orbital radius."""
        E0 = M if e < 0.8 else np.pi
        return newton(lambda E: E - e * np.sin(E) - M, E0, 
                      fprime=lambda E: 1 - e * np.cos(E), tol=1e-12)

    def _get_refined_scaling(self, r_mag, m_pert, r_p_vec, r_pair_vec):
        """Calculates alpha scaling based on optimized torsion formula."""
        # 2-Body Torsion
        M_base = (3.0 * self.mu) / (r_mag**3 * 50.0) 
        # N-Body Refinement
        r_p_mag = np.linalg.norm(r_p_vec)
        cos_psi = np.dot(r_pair_vec, r_p_vec) / (max(1e-9, np.linalg.norm(r_pair_vec) * r_p_mag))
        M_refined = M_base + self.lambda_opt * (m_pert / r_p_mag**3) * abs(cos_psi)
        
        # Symplectic Lock alpha * beta = 1
        beta_s = (M_refined + np.sqrt(M_refined**2 + 4)) / 2.0
        return 1.0 / beta_s, M_refined

    def propagate(self, r0, v0, T, pert_params):
        """Analytical Jump to time T."""
        # 1. State extraction
        r_mag0, v_sq0 = np.linalg.norm(r0), np.sum(v0**2)
        h_vec = np.cross(r0, v0); h_mag = np.linalg.norm(h_vec)
        energy = (0.5 * v_sq0) - (self.mu / r_mag0)
        a = -self.mu / (2 * energy)
        e_vec = (np.cross(v0, h_vec) / self.mu) - (r0 / r_mag0)
        e = np.linalg.norm(e_vec)
        
        # 2. Orbital Orientation
        i_angle = np.arccos(h_vec[2] / h_mag)
        n_node = np.array([-h_vec[1], h_vec[0], 0]); n_mag = np.linalg.norm(n_node)
        Omega = np.arccos(n_node[0]/n_mag) if n_mag != 0 else 0
        if n_mag != 0 and n_node[1] < 0: Omega = 2*np.pi - Omega
        
        # 3. Evolution of Mean Anomaly
        nu_0 = np.arccos(np.clip(np.dot(e_vec, r0)/(e * r_mag0), -1, 1))
        if np.dot(r0, v0) < 0: nu_0 = 2*np.pi - nu_0
        E_0 = 2 * np.arctan(np.sqrt((1-e)/(1+e)) * np.tan(nu_0/2))
        M_T = (E_0 - e * np.sin(E_0)) + np.sqrt(self.mu / a**3) * T
        
        # 4. Final Position Geometry
        E_T = self._solve_kepler(M_T, e)
        nu_T = 2 * np.arctan(np.sqrt((1+e)/(1-e)) * np.tan(E_T/2))
        r_inv_mag = a * (1 - e * np.cos(E_T))
        
        # 5. Apply Torsion Scaling
        alpha_s, M_val = self._get_refined_scaling(r_inv_mag, pert_params['m'], pert_params['r_p_vec'], r0)
        
        # 6. Apply Mirror Precession (Relativistic Shift)
        omega_base = np.arctan2(e_vec[1], e_vec[0]) if n_mag == 0 else \
                     np.arccos(np.clip(np.dot(n_node, e_vec)/(n_mag * e), -1, 1))
        if n_mag != 0 and e_vec[2] < 0: omega_base = 2*np.pi - omega_base

        # THE FIX: Calculate mean motion (n) and multiply it into the shift!
        n_motion = np.sqrt(self.mu / a**3)
        omega_f = omega_base + ((3 * self.mu * n_motion) / (a * (1 - e**2) * self.c_sq)) * T
        
        # 7. Coordinate Projection
        r_orb = np.array([r_inv_mag * np.cos(nu_T), r_inv_mag * np.sin(nu_T), 0])
        R3_W = np.array([[np.cos(Omega), -np.sin(Omega), 0], [np.sin(Omega), np.cos(Omega), 0], [0, 0, 1]])
        R1_i = np.array([[1, 0, 0], [0, np.cos(i_angle), -np.sin(i_angle)], [0, np.sin(i_angle), np.cos(i_angle)]])
        R3_w = np.array([[np.cos(omega_f), -np.sin(omega_f), 0], [np.sin(omega_f), np.cos(omega_f), 0], [0, 0, 1]])
        
        pos_final = (R3_W @ R1_i @ R3_w) @ r_orb * alpha_s
        return pos_final, {"alpha": alpha_s, "M": M_val}