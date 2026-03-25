import numpy as np
from scipy.optimize import minimize_scalar

class FineStructure8D_Solver:
    def __init__(self):
        self.Gamma_16D = 3.0 / 16.0 
        self.alpha_em = 1.0 / 137.035999  # The Fine Structure Constant
        
        # Proper relativistic spin-orbit coupling constant in Atomic Units
        # H_so scales by (alpha_em^2 / 2)
        self.k_spin = (self.alpha_em**2) / 2.0 

    def effective_potential(self, r, ls_coupling):
        """
        ls_coupling evaluates L dot S:
        For p_1/2 state: L*S = -1
        For p_3/2 state: L*S = +0.5
        """
        M_Z = 1.0 / (r**2)
        
        # Proper dimensionally-scaled spin torsion
        M_spin = self.k_spin * (ls_coupling / r**3)
        M_total = M_Z + M_spin
        
        beta = (M_total + np.sqrt(M_total**2 + 4.0)) / 2.0
        E_eff = -(1.0 / r) + self.Gamma_16D * beta
        return E_eff

    def find_state(self, ls_coupling):
        res = minimize_scalar(self.effective_potential, args=(ls_coupling,), bounds=(0.1, 2.0), method='bounded')
        return res.x, res.fun

# Execute with strictly physical L.S couplings
solver = FineStructure8D_Solver()

r_base, E_base = solver.find_state(0)      # No spin (Baseline)
r_p12, E_p12 = solver.find_state(-1)       # p_1/2 state (Antiparallel)
r_p32, E_p32 = solver.find_state(0.5)      # p_3/2 state (Parallel)

print(f"Base State:   E = {E_base:.8f} Ha")
print(f"p_1/2 State:  E = {E_p12:.8f} Ha")
print(f"p_3/2 State:  E = {E_p32:.8f} Ha")
print(f"Dirac Split:  {abs(E_p32 - E_p12):.8e} Ha")