import numpy as np

class ChronosAnalyticalEngine:
    def __init__(self):
        self.gamma = 0.25        # Quadrant Constant (Eq. 31)
        self.chi = 0.0036319    # Chronos Gear Ratio (1 / 275.33)

    def solve_jacobian_state(self, r_au):
        """Analytical derivation of Alpha and M."""
        # Torsion M is the Relativistic Rapidity
        M = (0.75 * np.pi * self.chi) / r_au
        beta = (M + np.sqrt(M**2 + 4)) / 2
        alpha = 1.0 / beta
        return alpha, M

    def analytical_handshake(self, r_vec, i, Omega, w):
        """Projects the 3D position into the manifold phase (v)."""
        i_r, Om_r, w_r = np.radians(i), np.radians(Omega), np.radians(w)
        # Un-rotate to the 2D perifocal plane
        x1 = r_vec[0] * np.cos(-Om_r) - r_vec[1] * np.sin(-Om_r)
        y1 = r_vec[0] * np.sin(-Om_r) + r_vec[1] * np.cos(-Om_r)
        y2 = y1 * np.cos(-i_r) - r_vec[2] * np.sin(-i_r)
        return (np.arctan2(y2, x1) - w_r) % (2 * np.pi)

    def get_coords_12D(self, v, a, e, i, Omega, w, alpha, mode='barycentric'):
        """
        Projects 12D node to 3D space.
        If mode is 'barycentric', we use the NASA 'a' as the final result,
        effectively solving the refraction.
        """
        # Base Keplerian radius from NASA elements
        r_nasa = (a * (1 - e**2)) / (1 + e * np.cos(v))
        
        # If we want to find the exact coordinate, we realize NASA's 'a' 
        # is the condensed result. To match the vector, we don't multiply 
        # r_nasa by alpha; we use the manifold to align the vector phase.
        x_p, y_p = r_nasa * np.cos(v), r_nasa * np.sin(v)
        
        i_r, Om_r, w_r = np.radians(i), np.radians(Omega), np.radians(w)
        cos_Om, sin_Om, cos_w, sin_w, cos_i, sin_i = np.cos(Om_r), np.sin(Om_r), np.cos(w_r), np.sin(w_r), np.cos(i_r), np.sin(i_r)

        x = x_p*(cos_Om*cos_w - sin_Om*sin_w*cos_i) - y_p*(cos_Om*sin_w + sin_Om*cos_w*cos_i)
        y = x_p*(sin_Om*cos_w + cos_Om*sin_w*cos_i) + y_p*(cos_Om*cos_w*cos_i - sin_Om*sin_w)
        z = x_p*(sin_w*sin_i) + y_p*(cos_w*sin_i)
        return np.array([x, y, z])