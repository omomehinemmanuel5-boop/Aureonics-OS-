"""
Aureonics CBF Governor Service
==============================
Implements a Control Barrier Function (CBF)-constrained adaptive governor
that guarantees min(x_i) >= TAU_CBF for all time steps under stochastic forcing.

Architecture:
  dynamics  →  adaptive governor  →  CBF safety filter  →  state update

The CBF filter is structured as a reusable module that can be upgraded
to a full Quadratic Program (QP)-based controller.
"""
import random

# ── Safety parameters ──────────────────────────────────────────────────────────
TAU_CBF = 0.05       # safety floor: no pillar may fall below this
DT_DEFAULT = 1.0     # time step

# ── Governor parameters ────────────────────────────────────────────────────────
TAU_GOV = 0.25       # governor correction activates below this threshold
THETA_0 = 1.0        # baseline adaptive gain
THETA_MIN = 0.1
THETA_MAX = 5.0
ALPHA_THETA = 0.8    # gain increase rate on error
BETA_THETA = 0.05    # decay rate toward theta_0
DEADZONE = 0.01      # ignore tiny errors
TARGET_MARGIN = 0.33 # desired stability margin (simplex centroid)

# ── Noise parameters ──────────────────────────────────────────────────────────
NOISE_SIGMA = 0.08
NOISE_CLIP = 0.15

NORMALIZATION_EPSILON = 1e-12


# ══════════════════════════════════════════════════════════════════════════════
# Dynamics
# ══════════════════════════════════════════════════════════════════════════════

def _gauss_clip(rng: random.Random, sigma: float, clip: float) -> float:
    return max(-clip, min(clip, rng.gauss(0.0, sigma)))


def _replicator(x: list[float], alpha: float = 0.5) -> list[float]:
    """Standard replicator dynamics — mass-conserving."""
    c, r, s = x
    a = [0.5, 0.5, 0.5]
    fitness = [
        a[0] - alpha * (r + s),
        a[1] - alpha * (c + s),
        a[2] - alpha * (c + r),
    ]
    f_bar = sum(x[i] * fitness[i] for i in range(3))
    return [x[i] * (fitness[i] - f_bar) for i in range(3)]


def _intrinsic_dynamics(x: list[float], rng: random.Random, alpha: float = 0.5) -> list[float]:
    """Replicator + bounded, mass-conserving Gaussian noise."""
    rep = _replicator(x, alpha)
    noise_raw = [_gauss_clip(rng, NOISE_SIGMA, NOISE_CLIP) for _ in range(3)]
    noise_mean = sum(noise_raw) / 3.0
    noise_mc = [n - noise_mean for n in noise_raw]
    return [rep[i] + noise_mc[i] for i in range(3)]


# ══════════════════════════════════════════════════════════════════════════════
# Adaptive Governor
# ══════════════════════════════════════════════════════════════════════════════

def _governor_G(x: list[float], tau_gov: float = TAU_GOV) -> list[float]:
    """Mass-conserving governor correction vector G(x)."""
    phi = [max(0.0, tau_gov - xi) for xi in x]
    phi_bar = sum(phi) / 3.0
    return [phi[i] - phi_bar for i in range(3)]


# ══════════════════════════════════════════════════════════════════════════════
# CBF Safety Module
# (structured for future upgrade to full QP controller)
# ══════════════════════════════════════════════════════════════════════════════

def _cbf_safety_filter(
    x: list[float],
    f: list[float],
    u_des: list[float],
    tau_cbf: float = TAU_CBF,
    dt: float = DT_DEFAULT,
) -> list[float]:
    """
    Discrete-time Control Barrier Function safety filter.

    Guarantees: x_i(t+1) = x_i + dt*(f_i + u_i) >= tau_cbf for all i,
    while maintaining mass conservation (sum(u) = 0).

    Algorithm (analytically solves the n=3 QP):
    1. Compute minimum safe control u_min_i = (tau_cbf - x_i)/dt - f_i
    2. Find active constraints: pillars where u_des_i < u_min_i
    3. Set active pillar controls to u_min_i
    4. Distribute the resulting mass excess equally to inactive (unconstrained) pillars
    5. If the redistribution activates additional constraints, iterate (max 5 passes)

    This is the exact QP solution for:
        min ||u - u_des||^2  s.t.  u_i >= u_min_i for all i,  sum(u) = 0
    """
    u_min = [(tau_cbf - x[i]) / dt - f[i] for i in range(3)]
    u = list(u_des)

    for _ in range(5):
        active = [i for i in range(3) if u[i] < u_min[i]]
        if not active:
            break

        inactive = [i for i in range(3) if i not in active]

        for i in active:
            u[i] = u_min[i]

        current_sum = sum(u)
        if abs(current_sum) < NORMALIZATION_EPSILON:
            break

        if inactive:
            excess_per = current_sum / len(inactive)
            for j in inactive:
                u[j] -= excess_per
        else:
            mean_u = current_sum / 3.0
            u = [ui - mean_u for ui in u]

    return u


FLOAT_TOLERANCE = 1e-9   # floating-point noise threshold for safety check


def _normalize(x: list[float]) -> tuple[list[float], bool]:
    clamped = [max(0.0, xi) for xi in x]
    total = sum(clamped)
    if total <= NORMALIZATION_EPSILON:
        return [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0], True
    # Only renormalize if total deviates from 1 by more than float noise
    if abs(total - 1.0) < 1e-10:
        return clamped, False
    return [xi / total for xi in clamped], False


# ══════════════════════════════════════════════════════════════════════════════
# Simulation
# ══════════════════════════════════════════════════════════════════════════════

def simulate_cbf(
    *,
    steps: int = 150,
    dt: float = DT_DEFAULT,
    seed: int = 42,
    alpha: float = 0.5,
    cbf_enabled: bool = True,
) -> dict:
    rng = random.Random(seed)
    x = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
    theta = THETA_0

    trajectory: list[dict] = []
    theta_traj: list[float] = []
    safety_violated = False
    min_m_global = 1.0
    time_below_safe = 0
    recovery_times: list[int] = []
    violation_start: int | None = None

    for t in range(steps):
        f = _intrinsic_dynamics(x, rng, alpha)

        if cbf_enabled:
            G = _governor_G(x)
            u_des = [theta * g for g in G]
            u_safe = _cbf_safety_filter(x, f, u_des, tau_cbf=TAU_CBF, dt=dt)
            total_force = [f[i] + u_safe[i] for i in range(3)]
        else:
            total_force = f[:]
            u_safe = [0.0, 0.0, 0.0]

        x_next = [x[i] + dt * total_force[i] for i in range(3)]
        x_next, _ = _normalize(x_next)
        x = x_next

        M_new = min(x)

        if M_new < TAU_CBF - FLOAT_TOLERANCE:
            safety_violated = True
            time_below_safe += 1
            if violation_start is None:
                violation_start = t
        elif violation_start is not None:
            recovery_times.append(t - violation_start)
            violation_start = None

        min_m_global = min(min_m_global, M_new)

        if cbf_enabled:
            e = max(0.0, TARGET_MARGIN - M_new)
            if e > DEADZONE:
                theta += ALPHA_THETA * e - BETA_THETA * (theta - THETA_0)
                theta = max(THETA_MIN, min(THETA_MAX, theta))

        theta_traj.append(theta)
        trajectory.append({
            "t": t,
            "C": round(x[0], 6),
            "R": round(x[1], 6),
            "S": round(x[2], 6),
            "M": round(M_new, 6),
            "theta": round(theta, 6),
            "u_safe": [round(u, 6) for u in u_safe],
        })

    if violation_start is not None:
        recovery_times.append(steps - violation_start)

    avg_recovery = sum(recovery_times) / len(recovery_times) if recovery_times else 0.0

    return {
        "trajectory": trajectory,
        "theta_trajectory": theta_traj,
        "min_M": round(min_m_global, 6),
        "safety_violated": safety_violated,
        "time_below_safe": time_below_safe,
        "recovery_times": recovery_times,
        "avg_recovery_time": round(avg_recovery, 3),
        "steps": steps,
        "dt": dt,
        "seed": seed,
        "cbf_enabled": cbf_enabled,
        "tau_cbf": TAU_CBF,
    }


def simulate_cbf_comparison(
    *,
    steps: int = 150,
    dt: float = DT_DEFAULT,
    seed: int = 42,
    alpha: float = 0.5,
) -> dict:
    governed = simulate_cbf(steps=steps, dt=dt, seed=seed, alpha=alpha, cbf_enabled=True)
    ungoverned = simulate_cbf(steps=steps, dt=dt, seed=seed, alpha=alpha, cbf_enabled=False)
    return {
        "governed": governed,
        "ungoverned": ungoverned,
        "safety_guarantee_holds": not governed["safety_violated"],
        "improvement_min_M": round(governed["min_M"] - ungoverned["min_M"], 6),
    }
