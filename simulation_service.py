def simulate_mode(τ, x_i, M):
    # Adaptive gain variables
    k_base = 4.0
    η = 0.5
    β = 0.1
    k_min = 4.0
    k_max = 20.0
    k = k_base
    k_trajectory = []  # To track k trajectory over time

    # Mass-conserving governor correction
    φ_i = max(0, τ - x_i)
    φ̄ = φ_i / 3

    # Simulation step
    for step in range(num_steps):  # Assuming num_steps is defined
        # Update k
        k = k + η * max(0, τ - M) - β * (k - k_base)
        k = max(k_min, min(k, k_max))  # Clipping k to [k_min, k_max]
        k_trajectory.append(k)
        
        # Compute governor correction
        G_i = k * (φ_i - φ̄)
        
    return {'k_trajectory': k_trajectory, 'G_i': G_i}