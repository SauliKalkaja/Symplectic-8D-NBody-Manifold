import numpy as np
from scipy.optimize import newton

class Manifold8DEngine:
    def __init__(self, mu, c_sq=10000.0):
        self.mu = mu
        self.c_sq = c_sq
        self.lambda_opt = 10.0 

    def _solve_kepler(self, M, e):
        """Unified Kepler solver: handles ellipses and hyperbolas."""
        if e < 1.0:
            E0 = M if e < 0.8 else np.pi
            func = lambda E: E - e * np.sin(E) - M
            fprime = lambda E: 1 - e * np.cos(E)
        else:
            E0 = np.arcsinh(M/e) if M > 0 else M
            func = lambda H: e * np.sinh(H) - H - M
            fprime = lambda H: e * np.cosh(H) - 1
        try:
            return newton(func, E0, fprime=fprime, tol=1e-12)
        except:
            return M 

    def _get_alpha_and_phase(self, r_mag, m_pert, r_p_vec, r_pair_vec, sign=1.0, e=0.0):
        """Calculates antisymmetric torsion and scaling."""
        k1 = (3.0 * self.mu) / 50.0
        M_base = k1 / max(1e-6, r_mag)**3
        
        r_p_mag = max(1e-6, np.linalg.norm(r_p_vec))
        cos_psi = np.dot(r_pair_vec, r_p_vec) / (max(1e-9, np.linalg.norm(r_pair_vec) * r_p_mag))
        
        # PARABOLIC FIX: Flip interaction sign at the transition boundary (e=1)
        eff_sign = sign * (-1.0 if e >= 1.0 else 1.0)
        M_int = eff_sign * self.lambda_opt * (m_pert / r_p_mag**3) * cos_psi
        M_total = M_base + M_int
        
        # Symplectic Lock: alpha * beta = 1
        M_abs = abs(M_total)
        beta_s = (M_abs + np.sqrt(M_total**2 + 4)) / 2.0
        return 1.0 / beta_s, M_total

    def propagate(self, r0, v0, T, pert_params):
        r_mag0, v_sq0 = np.linalg.norm(r0), np.sum(v0**2)
        h_vec = np.cross(r0, v0); h_mag = np.linalg.norm(h_vec)
        energy = (0.5 * v_sq0) - (self.mu / r_mag0)
        a = -self.mu / (2 * energy)
        e_vec = (np.cross(v0, h_vec) / self.mu) - (r0 / r_mag0)
        e = np.linalg.norm(e_vec)

        # 1. Geometry 
        i_angle = np.arccos(np.clip(h_vec[2] / h_mag, -1, 1))
        n_node = np.array([-h_vec[1], h_vec[0], 0]); n_mag = np.linalg.norm(n_node)
        Omega = np.arccos(np.clip(n_node[0]/n_mag, -1, 1)) if n_mag != 0 else 0
        if n_mag != 0 and n_node[1] < 0: Omega = 2*np.pi - Omega
        
        cos_nu0 = np.clip(np.dot(e_vec, r0) / (max(1e-9, e * r_mag0)), -1, 1)
        nu_0 = np.arccos(cos_nu0)
        if np.dot(r0, v0) < 0: nu_0 = 2*np.pi - nu_0
        
        # 2. Universal Time Evolution
        if e < 1.0:
            E_0 = 2 * np.arctan(np.sqrt((1-e)/(1+e)) * np.tan(nu_0/2))
            M_0 = E_0 - e * np.sin(E_0)
        else:
            H_0 = 2 * np.arctanh(np.sqrt((e-1)/(e+1)) * np.tan(nu_0/2))
            M_0 = e * np.sinh(H_0) - H_0
        
        M_T = M_0 + np.sqrt(self.mu / abs(a**3)) * T
        sol_T = self._solve_kepler(M_T, e)
        
        if e < 1.0:
            nu_T = 2 * np.arctan(np.sqrt((1+e)/(1-e)) * np.tan(sol_T / 2))
            r_inv_mag = abs(a) * (1 - e * np.cos(sol_T))
        else:
            nu_T = 2 * np.arctan(np.sqrt((e+1)/(e-1)) * np.tanh(sol_T / 2))
            r_inv_mag = abs(a) * (e * np.cosh(sol_T) - 1)
            
        # 3. Manifold Metric Transformation
        a_start, _ = self._get_alpha_and_phase(r_mag0, pert_params['m'], pert_params['r_p_vec'], r0, sign=pert_params.get('sign', 1.0), e=e)
        a_end, M_f = self._get_alpha_and_phase(r_inv_mag, pert_params['m'], pert_params['r_p_vec'], r0, sign=pert_params.get('sign', 1.0), e=e)
        
        # 4. Phase Shift (Precession + Torsion)
        precession = ((3 * self.mu) / (abs(a) * (1 - e**2) * self.c_sq)) * T
        torsion_phase = (M_f * (r_inv_mag - r_mag0))
        
        omega = np.arctan2(e_vec[1], e_vec[0]) if n_mag == 0 else np.arccos(np.clip(np.dot(n_node, e_vec) / (n_mag * e), -1, 1))
        if n_mag != 0 and e_vec[2] < 0: omega = 2*np.pi - omega
        
        omega_f = omega + precession + torsion_phase
        
        # 5. Resultant Projection
        r_orb = np.array([r_inv_mag * np.cos(nu_T), r_inv_mag * np.sin(nu_T), 0])
        R3_W = np.array([[np.cos(Omega), -np.sin(Omega), 0], [np.sin(Omega), np.cos(Omega), 0], [0, 0, 1]])
        R1_i = np.array([[1, 0, 0], [0, np.cos(i_angle), -np.sin(i_angle)], [0, np.sin(i_angle), np.cos(i_angle)]])
        R3_w = np.array([[np.cos(omega_f), -np.sin(omega_f), 0], [np.sin(omega_f), np.cos(omega_f), 0], [0, 0, 1]])
        
        return (R3_W @ R1_i @ R3_w) @ r_orb * (a_end / a_start)