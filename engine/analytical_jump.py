"""
analytical_jump.py — Universal analytical-jump engine for rigid-body systems.

Anchor module.  Every project that needs the symplectic jump operator imports
`AnalyticalJump` from here.  No project-specific assumptions; rigid bodies
only in this first cut (point masses with mass, position, velocity, and
optional spin for later).

PHYSICS (condensed)
===================

The core identity (Eq 23 in 6D_Symplectic_Unification.pdf; Eq 26 in the 8D
counterpart is the same operator in higher dimensionality):

    Δφ_total = ∮_Anchors [ M(r) dr + Σ_{j≠i} (∂χ_ij/∂θ) dθ ]           (eq 23)

The integral is bounded by the orbital anchors (perihelion ↔ aphelion),
and time has been eliminated via the chain rule dr = (p_r/μ) dt.  The
summation operator therefore plays the same role as log(·) for products:
it converts an integral over time into an algebraic initial-value problem.

KEY STRUCTURE
-------------
  • Pair-wise torsion M:
      M_ij(r_ij) = κ(r_ij) · (α_s,ij − β_s,ij) / 2    (Kepler two-body
      torsion between bodies i and j; N×N antisymmetric matrix;
      N(N−1)/2 unique entries)
  • Pair-wise theta χ_ij same structure.
  • Analytical closure:  {r, φ, θ} ↔ {M, α_s, β_s}, symmetric IVP basis.
  • Flip gate:  sign(M) flips only when a body crosses its perihelion.
                The gate fires PER BODY, not per step.
  • Sparse update:  body k flips → M_kj for j≠k change sign; all other
                     pairs untouched.

USAGE SKETCH
------------
    aj = AnalyticalJump(masses, positions, velocities, G=...)
    aj.build_pairwise_state()           # seed M_ij, α_ij, β_ij, e_ij
    state_T = aj.propagate_to(T)        # O(1) analytical jump per body
    aj.check_and_apply_flips(state_T)   # sparse update at perihelion events

All pair matrices are kept as numpy arrays so downstream projects can index
them directly.  The class never hides the underlying numbers behind
`__private` getters — everything the architect might want is a public
attribute.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Iterable, Optional

import numpy as np

from solar_system import kepler_anchor


# ---------------------------------------------------------------------------
# Constants — defaults for the solar-system problem.  Override via __init__.
# ---------------------------------------------------------------------------

#: Gravitational constant in SI units (m^3 kg^-1 s^-2).  Use au/day/M_sun for
#: JPL Horizons inputs; see `from_horizons_units`.
G_SI = 6.67430e-11

#: Γ_12D from Eq 16/17: symplectic projection scalar 3/12 for the 6D manifold.
#: For the 8D extension it becomes 4/16 = 0.25 — the paper shows both reduce
#: to 0.25, i.e. the same projection operator.
GAMMA_PROJECTION = 0.25

#: Speed of light in au/day — Gauss system:  c · 1 day = 173.144... au
C_AU_PER_DAY = 173.1446326742403


# ---------------------------------------------------------------------------
# Body record — rigid body in the first-cut API.  Spin/inertia fields are
# present but unused in the point-mass path; they give extension room.
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class RigidBody:
    """Minimal rigid-body descriptor.  Sun is just a heavy RigidBody; it is
    not special and does not sit at the origin — everything rotates around
    the system barycenter."""

    name:     str
    mass:     float                    # kg (or Horizons units, be consistent)
    position: np.ndarray               # shape (3,)
    velocity: np.ndarray               # shape (3,)
    # Rigid-body extension (optional, unused by point-mass jump):
    inertia:  Optional[np.ndarray] = None       # shape (3,3)
    spin:     Optional[np.ndarray] = None       # shape (3,)  angular velocity
    radius:   float = 0.0                        # physical radius (m)


# ---------------------------------------------------------------------------
# AnalyticalJump — the universal engine
# ---------------------------------------------------------------------------

class AnalyticalJump:
    """Analytical-jump operator for an N-body rigid-body system.

    The class holds:
      • bodies           : list[RigidBody]
      • M                : (N,N) antisymmetric torsion matrix       — pair-wise
      • alpha, beta      : (N,N) symplectic anchors per pair        — pair-wise
      • e                : (N,N) eccentricity per pair               — pair-wise
      • perihelion_sign  : (N,) current elliptic/hyperbolic sign per body
                             (+1 bound / −1 unbound)

    The only mutation primitives are:
      • build_pairwise_state():  seed all pair matrices from current posns/vels
      • propagate_to(T):         O(1) algebraic jump of each body to time T
      • check_and_apply_flips(): event-gated sparse update (only pairs
                                   involving bodies currently crossing
                                   their perihelion)

    Everything else is a read-only *derived* quantity that can be computed
    from (positions, velocities, masses, G) without hidden side effects.
    This keeps the analytical closure of the physics visible in the code.
    """

    # ----- construction ----------------------------------------------------

    def __init__(self,
                 bodies: Iterable[RigidBody],
                 G: float = G_SI,
                 gamma_projection: float = GAMMA_PROJECTION):
        """Build a jump engine over `bodies`.

        Parameters
        ----------
        bodies : iterable of RigidBody
            All bodies in the system.  Order is fixed; indices i,j in the
            pair matrices refer to this ordering.  The Sun (if present) is
            just one of the entries.
        G : float
            Gravitational constant, in the unit system the caller is using.
            Horizons au/day/M_sun: use G = 2.959122e-4 (G * M_sun).
        gamma_projection : float
            Symplectic projection scalar Γ used in the eccentricity
            identity (default 0.25; see Eq 17 in 6D paper).
        """
        self.bodies = list(bodies)
        self.N      = len(self.bodies)
        self.G      = float(G)
        self.gamma  = float(gamma_projection)

        # pair matrices — filled by build_pairwise_state()
        self.M     = np.zeros((self.N, self.N), dtype=float)
        self.alpha = np.zeros((self.N, self.N), dtype=float)
        self.beta  = np.zeros((self.N, self.N), dtype=float)
        self.e     = np.zeros((self.N, self.N), dtype=float)

        # per-body perihelion sign: +1 = elliptic (bound), −1 = hyperbolic.
        # Flips are gated by perihelion crossings; see check_and_apply_flips.
        self.perihelion_sign = np.ones(self.N, dtype=int)

        # per-body last known perihelion / aphelion radii, updated lazily
        # when we detect anchor events.  NaN = unknown yet.
        self.r_per = np.full(self.N, np.nan, dtype=float)
        self.r_aph = np.full(self.N, np.nan, dtype=float)

        # per-body Keplerian elements relative to the system barycenter.
        # Populated by seed_barycentric_elements().  Used by propagate_to.
        self.elements: list[Optional[kepler_anchor.OrbitElements]] = [None] * self.N
        self.t0: Optional[float] = None    # epoch of the seeded state

    # ----- geometry: pair-wise basics --------------------------------------

    def pair_vector(self, i: int, j: int) -> np.ndarray:
        """Relative position r_ij = r_j − r_i.  (Convention: vector from i
        to j, so ||r_ij|| is the inter-body distance.)"""
        return self.bodies[j].position - self.bodies[i].position

    def pair_distance(self, i: int, j: int) -> float:
        """Scalar r_ij = ||r_j − r_i||.  O(1)."""
        return float(np.linalg.norm(self.pair_vector(i, j)))

    def reduced_mass(self, i: int, j: int) -> float:
        """μ_ij = m_i m_j / (m_i + m_j).  Used in the Kepler two-body
        reduction that underlies M_ij."""
        m_i, m_j = self.bodies[i].mass, self.bodies[j].mass
        return m_i * m_j / (m_i + m_j)

    # ----- alpha / beta (symplectic anchors) -------------------------------

    def schwarzschild_radius(self, m_attractor: float) -> float:
        """r_s = 2 G M / c²  in au.  For solar-mass primary in our units
        this is ~1.97e-8 au ≈ 2.95 km, matching the Sun's Schwarzschild
        radius to 3 sig figs."""
        return 2.0 * self.G * m_attractor / (C_AU_PER_DAY ** 2)

    def alpha_from_r(self, r: float, r_s: float) -> float:
        """Spatial condensation α_s as a function of radius (weak-field
        Schwarzschild-like).

            α_s(r) = 1 − r_s / r

        • At r → ∞  (far from attractor):  α_s → 1, β_s = 1/α_s → 1, M → 0.
        • At r = r_s (singularity):       α_s → 0, β_s → ∞, M → ∞.

        This is the leading-order weak-field solution of the hyperbolic
        invariant (α_s + β_s)² − M² = 4 with α_s · β_s = 1 and the metric
        coupling r ∝ (1 − α_s)⁻¹.  Evaluated at perihelion it yields
        α_s,min; at aphelion α_s,max.
        """
        if r <= 0.0 or r <= r_s:
            return 0.0
        return 1.0 - r_s / r

    def beta_from_alpha(self, alpha: float) -> float:
        """Symplectic lock: α · β = 1 (Eq 1 / 2 in the 6D paper)."""
        if alpha == 0.0:
            return math.inf
        return 1.0 / alpha

    def torsion_from_alpha(self, alpha: float) -> float:
        """M = sqrt((α + β)² − 4), from the hyperbolic invariant."""
        if alpha <= 0.0: return math.inf
        beta = 1.0 / alpha
        return math.sqrt(max((alpha + beta) ** 2 - 4.0, 0.0))

    def evaluate_at_anchors(self, k: int) -> dict:
        """Evaluate α_s, β_s, M at body k's perihelion AND aphelion,
        using the body's current Keplerian orbit around its primary.

        Returns a dict with:
          r_per, r_aph
          alpha_min, alpha_max       (at perihelion, aphelion)
          beta_min,  beta_max        (= 1/alpha)
          M_max,     M_min           (at perihelion, aphelion; reversed)
          e_alpha    via Eq 16
          e_M        via Eq 17
        """
        el = self.elements[k]
        if el is None:
            raise RuntimeError(f"body {k} has no fitted orbital elements")

        # Anchors in the relative-orbit frame
        if el.e < 1.0 and el.a > 0.0:
            r_per = el.a * (1.0 - el.e)
            r_aph = el.a * (1.0 + el.e)
        else:
            # hyperbolic / parabolic — r_aph is infinite; skip
            return {"r_per": math.nan, "r_aph": math.nan,
                     "alpha_min": math.nan, "alpha_max": math.nan,
                     "beta_min":  math.nan, "beta_max":  math.nan,
                     "M_max": math.nan, "M_min": math.nan,
                     "e_alpha": math.nan, "e_M": math.nan}

        # Schwarzschild radius of the body's primary (the attractor)
        primary_idx = self._primary[k] if hasattr(self, "_primary") \
                       else int(np.argmax([b.mass if j != k else -1
                                             for j, b in enumerate(self.bodies)]))
        r_s = self.schwarzschild_radius(self.bodies[primary_idx].mass)

        # α, β, M at both anchors
        alpha_min = self.alpha_from_r(r_per, r_s)           # smaller α at perihelion
        alpha_max = self.alpha_from_r(r_aph, r_s)           # larger α at aphelion
        beta_min  = self.beta_from_alpha(alpha_max)          # β is inverse
        beta_max  = self.beta_from_alpha(alpha_min)
        M_max     = self.torsion_from_alpha(alpha_min)       # max torsion at perihelion
        M_min     = self.torsion_from_alpha(alpha_max)       # min torsion at aphelion

        e_alpha = self.eccentricity_from_alpha(a_min=alpha_min, a_max=alpha_max)
        e_M     = self.eccentricity_from_M(M_min=M_min, M_max=M_max)
        return {"r_per": r_per, "r_aph": r_aph,
                 "alpha_min": alpha_min, "alpha_max": alpha_max,
                 "beta_min":  beta_min,  "beta_max":  beta_max,
                 "M_max": M_max, "M_min": M_min,
                 "e_alpha": e_alpha, "e_M": e_M, "r_s": r_s}

    # ----- torsion M_ij (pair-wise) ----------------------------------------

    def torsion_pair(self, i: int, j: int) -> float:
        """Scalar torsion M_ij between bodies i and j.

        Derivation (paper, §2.5–2.7): M = ((α + β)^2 − 4)^(1/2), the scalar
        magnitude of the antisymmetric torsion tensor.  The sign is carried
        by self.perihelion_sign[i] · self.perihelion_sign[j]: either body
        having flipped to hyperbolic inverts the pair's torsion sign.
        """
        r = self.pair_distance(i, j)
        a = self.alpha[i, j] if self.alpha[i, j] != 0.0 else 1.0
        b = self.beta [i, j] if self.beta [i, j] != 0.0 else 1.0
        disc = (a + b) ** 2 - 4.0
        mag = math.sqrt(max(disc, 0.0))
        sign = self.perihelion_sign[i] * self.perihelion_sign[j]
        return sign * mag

    # ----- eccentricity from the two anchor identities ---------------------

    def eccentricity_from_alpha(self, a_min: float, a_max: float) -> float:
        """Eq 16:  e = Γ · (α_max − α_min) / (2 − α_min − α_max)."""
        denom = 2.0 - a_min - a_max
        if denom == 0.0:
            return 0.0
        return self.gamma * (a_max - a_min) / denom

    def eccentricity_from_M(self, M_min: float, M_max: float) -> float:
        """Eq 17:  e = Γ · (M_max − M_min) / (M_max + M_min).

        Mathematically identical to eccentricity_from_alpha when the
        hyperbolic invariant holds; useful as a cross-check.
        """
        if M_max + M_min == 0.0:
            return 0.0
        return self.gamma * (M_max - M_min) / (M_max + M_min)

    # ----- seeding the full pair state -------------------------------------

    def build_pairwise_state(self) -> None:
        """Populate self.M, self.alpha, self.beta, self.e from current
        positions/velocities of all bodies.

        This is the costly step — O(N²).  After this runs, propagate_to()
        and check_and_apply_flips() are cheap O(N) and O(N−1)-per-flip
        respectively.
        """
        N = self.N
        # Reset matrices (leave diagonal 0).
        self.M[:]     = 0.0
        self.alpha[:] = 0.0
        self.beta[:]  = 0.0
        self.e[:]     = 0.0

        # First pass: for each pair, estimate r_per, r_aph via two-body
        # Kepler from current (r, v).  This uses the vis-viva shortcut
        # rather than the full symplectic residual.  It gives the correct
        # anchors for the seed state; subsequent updates refine them.
        for i in range(N):
            for j in range(i + 1, N):
                rvec = self.pair_vector(i, j)
                vvec = self.bodies[j].velocity - self.bodies[i].velocity
                r = float(np.linalg.norm(rvec))
                v2 = float(np.dot(vvec, vvec))
                mu = self.G * (self.bodies[i].mass + self.bodies[j].mass)

                # specific orbital energy; if ≥0 the pair is unbound.
                eps = 0.5 * v2 - mu / r
                if eps >= 0.0:
                    # hyperbolic/parabolic — sign will flip pair-wise
                    self.perihelion_sign[i] = -1
                    self.perihelion_sign[j] = -1
                    e_ij = 1.0 + 2.0 * eps * np.linalg.norm(np.cross(rvec,
                                 vvec))**2 / (mu**2)
                    e_ij = math.sqrt(max(e_ij, 1.0))
                    a_ij = -mu / (2.0 * eps)    # negative semi-major axis
                else:
                    a_ij = -mu / (2.0 * eps)    # positive
                    hvec = np.cross(rvec, vvec)
                    h2 = float(np.dot(hvec, hvec))
                    e_ij = math.sqrt(max(1.0 + 2.0 * eps * h2 / (mu**2), 0.0))

                r_per_ij = a_ij * (1.0 - e_ij) if a_ij > 0 else r
                r_aph_ij = a_ij * (1.0 + e_ij) if a_ij > 0 else r * 10.0

                # write into pair matrices (symmetric where appropriate)
                self.e[i, j] = self.e[j, i] = e_ij

                # α_s at current r, using the heavier partner's r_s
                heavier = i if self.bodies[i].mass >= self.bodies[j].mass else j
                r_s_ij = self.schwarzschild_radius(self.bodies[heavier].mass)
                a_val = self.alpha_from_r(r, r_s_ij)
                b_val = self.beta_from_alpha(a_val)
                self.alpha[i, j] = self.alpha[j, i] = a_val
                self.beta [i, j] = self.beta [j, i] = b_val

                # antisymmetric M: off-diagonal with sign from perihelion
                mag = math.sqrt(max((a_val + b_val)**2 - 4.0, 0.0))
                sgn = self.perihelion_sign[i] * self.perihelion_sign[j]
                self.M[i, j] =  sgn * mag
                self.M[j, i] = -sgn * mag

    # ----- perihelion gating ------------------------------------------------

    def is_at_perihelion(self, k: int,
                           tol: float = 1e-6) -> bool:
        """Return True if body k is at or is crossing its perihelion.

        Definition of "body k's perihelion" in a multi-body setting: the
        minimum of ||r_k − r_bary||, where r_bary is the system
        barycentre.  This is the physically meaningful anchor because
        the symplectic lock condenses each body's own α_s when IT dips
        closest to the aggregated mass, not pair-wise.

        For the first-cut gate we return True when the current body-to-
        barycentre distance is within `tol` of the known per-body minimum
        (self.r_per[k]).  The caller is responsible for updating
        self.r_per[k] when a new minimum is observed.
        """
        if not math.isfinite(self.r_per[k]):
            return False
        r_bary = self.body_to_barycentre_distance(k)
        return abs(r_bary - self.r_per[k]) < tol

    def barycentre(self) -> np.ndarray:
        """System mass-weighted centre.  Nothing is fixed here — the Sun
        orbits it like any other body."""
        total_m = sum(b.mass for b in self.bodies)
        return sum(b.mass * b.position for b in self.bodies) / total_m

    def body_to_barycentre_distance(self, k: int) -> float:
        return float(np.linalg.norm(self.bodies[k].position - self.barycentre()))

    # ----- sparse flip update ---------------------------------------------

    def apply_flip(self, k: int) -> None:
        """Body k has crossed its perihelion and changed regime: flip the
        sign of every M_ij whose pair involves k, leaving all other
        pairs untouched.  This is the O(N−1) update the architect flagged;
        do NOT rewrite all N(N−1)/2 entries here.
        """
        self.perihelion_sign[k] *= -1
        for j in range(self.N):
            if j == k: continue
            self.M[k, j] = -self.M[k, j]
            self.M[j, k] = -self.M[j, k]

    def check_and_apply_flips(self, tol: float = 1e-6) -> list[int]:
        """Walk once over the N bodies, fire apply_flip() on each that is
        currently at perihelion.  Returns the list of body indices that
        flipped this call (empty list = no update needed)."""
        flipped = []
        for k in range(self.N):
            if self.is_at_perihelion(k, tol=tol):
                self.apply_flip(k)
                flipped.append(k)
        return flipped

    # ----- analytical propagation -----------------------------------------

    def total_mass(self) -> float:
        return sum(b.mass for b in self.bodies)

    def primary_index(self, k: int) -> int:
        """Return the index of body k's dominant gravitational attractor.

        Universal rule: the *heaviest* other body.  In a planetary system
        this recovers the physically correct two-body reduction without
        special-casing the Sun:

          • Every planet k     →  heaviest other = Sun
          • Sun                →  heaviest other = Jupiter
          • (If we ever model a binary star, each star would pair to the
             other; still universal.)

        A more aggressive rule would be argmax(m_j / r_jk²), the "strongest
        current pull".  For the solar system they coincide.
        """
        return max((j for j in range(self.N) if j != k),
                     key=lambda j: self.bodies[j].mass)

    def seed_barycentric_elements(self, t0: float) -> None:
        """Fit each body k's Keplerian elements as a two-body orbit around
        its dominant attractor (primary_index(k)).  Each body carries the
        gravitational parameter

            μ_k = G · (m_primary + m_k)

        which is the correct heliocentric μ for planets (m_primary = M_sun)
        and the correct binary-reduction μ for the Sun (m_primary = M_jup).

        Must be called after build_pairwise_state() and before
        propagate_to().
        """
        self._primary = [self.primary_index(k) for k in range(self.N)]
        for k, body in enumerate(self.bodies):
            p = self._primary[k]
            primary = self.bodies[p]
            r_rel = body.position - primary.position
            v_rel = body.velocity - primary.velocity
            mu_k  = self.G * (primary.mass + body.mass)
            self.elements[k] = kepler_anchor.state_to_elements(
                r_rel, v_rel, mu=mu_k, t0=t0)
        self.t0 = t0
        # Remember each primary's SEED state — we'll linear-extrapolate
        # its motion over the propagation interval.  For sub-orbital-period
        # dt this is adequate; for long jumps we'd need to propagate the
        # primary first (Sun's own elements around Jupiter, etc.).
        self._primary_seed_pos = [self.bodies[self._primary[k]].position.copy()
                                    for k in range(self.N)]
        self._primary_seed_vel = [self.bodies[self._primary[k]].velocity.copy()
                                    for k in range(self.N)]
        # System barycentre (seed) and mass — required to enforce
        # momentum conservation after propagation.  In a closed system
        # the total CoM moves uniformly; we re-anchor predictions to it
        # after the Kepler jump.
        self._seed_com_pos = self.barycentre().copy()
        self._seed_com_vel = self._barycentre_velocity().copy()

    def _barycentre_velocity(self) -> np.ndarray:
        """Mass-weighted velocity of the system.  Should be ~0 in a
        barycentric frame, but we subtract it explicitly for numerical
        cleanliness (Horizons can carry a tiny non-zero CoM drift)."""
        total_m = self.total_mass()
        return sum(b.mass * b.velocity for b in self.bodies) / total_m

    def _find_pairs(self) -> list[tuple[int, int]]:
        """Return all index pairs (i, j) where each is the other's primary.

        These require a single relative-orbit fit with mass-weighted
        distribution, rather than two independent Kepler fits.
        """
        pairs = []
        seen = set()
        for i in range(self.N):
            j = self._primary[i]
            if self._primary[j] == i and i < j and (i, j) not in seen:
                pairs.append((i, j))
                seen.add((i, j))
        return pairs

    def propagate_to(self, T: float,
                       use_alpha_scaling: bool = False) -> None:
        """Advance every body to absolute Julian date T.

        Two-stage reduction:
          • **Pairs** (i, j each other's primary, e.g. Sun–Jupiter): one
            relative-orbit Kepler fit; distribute into body positions via
            mass ratios around the PAIR barycentre, which drifts linearly
            over dt (since pair-internal forces don't move pair BC).
          • **Tree bodies**: planets orbit the Sun.  Their Kepler orbit
            was seeded around the primary's SEED position.  At time T we
            attach them to the primary's NEW position.
        """
        if self.t0 is None or any(e is None for e in self.elements):
            raise RuntimeError(
                "propagate_to: seed_barycentric_elements(t0) must be called first.")

        dt = T - self.t0
        pairs = self._find_pairs()
        paired = set()
        for i, j in pairs:
            paired.update((i, j))

        new_pos: list[Optional[np.ndarray]] = [None] * self.N
        new_vel: list[Optional[np.ndarray]] = [None] * self.N

        # --- Stage 1: symmetric pairs --------------------------------------
        for (i, j) in pairs:
            # Use body i's element — its r_rel is r_i - r_j.  Body j's
            # relative vector is the mirror; no independent fit needed.
            el = self.elements[i]
            r_rel_T, v_rel_T = kepler_anchor.elements_to_state(el, t=T)
            # r_rel_T is body i relative to body j, per state_to_elements(r_i - r_j, ...)
            m_i, m_j = self.bodies[i].mass, self.bodies[j].mass
            M_pair = m_i + m_j
            # seed pair barycentre position + velocity
            r_bc_seed = (m_i * self.bodies[i].position
                          + m_j * self.bodies[j].position) / M_pair
            v_bc_seed = (m_i * self.bodies[i].velocity
                          + m_j * self.bodies[j].velocity) / M_pair
            # Linear drift over dt — exact for an isolated pair; good
            # approximation while external perturbers are much lighter.
            r_bc_T = r_bc_seed + dt * v_bc_seed
            v_bc_T = v_bc_seed
            # Distribute: body i = BC + (m_j/M_pair)·r_rel,  body j = BC − (m_i/M_pair)·r_rel
            new_pos[i] = r_bc_T + (m_j / M_pair) * r_rel_T
            new_pos[j] = r_bc_T - (m_i / M_pair) * r_rel_T
            new_vel[i] = v_bc_T + (m_j / M_pair) * v_rel_T
            new_vel[j] = v_bc_T - (m_i / M_pair) * v_rel_T

        # --- Stage 2: tree bodies — hang off primary's new position -------
        for k in range(self.N):
            if k in paired: continue
            el = self.elements[k]
            r_rel_T, v_rel_T = kepler_anchor.elements_to_state(el, t=T)
            if use_alpha_scaling:
                r_now = float(np.linalg.norm(r_rel_T))
                r_s = self.schwarzschild_radius(self.bodies[self._primary[k]].mass)
                alpha = self.alpha_from_r(r_now, r_s)
                r_rel_T = alpha * r_rel_T
            p = self._primary[k]
            # primary's new position must already be resolved (paired or tree)
            # — tree primaries also resolve here (recursively)
            if new_pos[p] is None:
                # Non-paired primary (unusual for solar system; defensive).
                # Fallback: linear extrapolation of primary seed state.
                new_pos[p] = (self.bodies[p].position
                                + dt * self.bodies[p].velocity)
                new_vel[p] = self.bodies[p].velocity.copy()
            new_pos[k] = new_pos[p] + r_rel_T
            new_vel[k] = new_vel[p] + v_rel_T

        # Apply atomically
        for k, body in enumerate(self.bodies):
            body.position = new_pos[k]
            body.velocity = new_vel[k]
        self.t0 = T


# ---------------------------------------------------------------------------
# Small utilities for unit systems the architect will actually feed in
# ---------------------------------------------------------------------------

def horizons_units() -> float:
    """Return G for JPL Horizons default units (au, day, M_sun).

    G * M_sun  =  k_Gauss²  ≈  2.959122082855911e-4  au³ / (day² · M_sun)
    So with masses expressed in solar masses:  G = 2.959122082855911e-4.
    """
    return 2.959122082855911e-4


if __name__ == "__main__":
    # Sanity smoke test: 2-body Sun–Earth (very approximate).
    sun = RigidBody(name="Sun",
                     mass=1.0,
                     position=np.zeros(3),
                     velocity=np.zeros(3))
    earth = RigidBody(name="Earth",
                       mass=3.0027e-6,            # solar masses
                       position=np.array([1.0, 0.0, 0.0]),   # au
                       velocity=np.array([0.0, 0.01720209, 0.0]))  # au/day

    aj = AnalyticalJump([sun, earth], G=horizons_units())
    aj.build_pairwise_state()
    print("Bodies       :", [b.name for b in aj.bodies])
    print("M matrix     :\n", aj.M)
    print("α matrix     :\n", aj.alpha)
    print("β matrix     :\n", aj.beta)
    print("e matrix     :\n", aj.e)
    print("barycentre   :", aj.barycentre())
    print("Earth→bary r :", aj.body_to_barycentre_distance(1))
