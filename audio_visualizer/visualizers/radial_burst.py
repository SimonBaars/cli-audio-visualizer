"""Radial Burst visualizer - transient-driven starfield particle system.

Features:
- Dual energy envelopes (macro/fast) for detecting musical transients
- Particles emit from center with velocity influenced by audio energy
- Shimmer effect from high-frequency content
- Smooth drift animation for ambient feel
"""
import numpy as np
import curses
from audio_visualizer.dsp.bars import compute_frequency_bars


def _apply_adaptive_eq(values: np.ndarray, state: dict) -> np.ndarray:
    """Apply running-mean adaptive EQ if enabled."""
    if not state.get('adaptive_eq') or values.size == 0:
        return values
    strength = float(state.get('adaptive_eq_strength', 0.4))
    run_mean = state.get('adaptive_eq_mean')
    if run_mean is None or run_mean.shape != values.shape:
        run_mean = values.copy()
    else:
        run_mean = 0.995 * run_mean + 0.005 * values
    adj = values / (run_mean + 1e-6)
    mx = np.max(adj)
    if mx > 0:
        adj /= mx
    state['adaptive_eq_mean'] = run_mean
    return (1 - strength) * values + strength * adj


def _compute_energy_metrics(bands: np.ndarray, state: dict) -> dict:
    """Compute weighted energy, transient detection, and shimmer from frequency bands."""
    if len(bands) == 0:
        return {'energy': 0.0, 'transient': 0.0, 'shimmer': 0.0, 'quiet': True}
    
    # Weighted energy emphasizing musical fundamentals (80-800 Hz range)
    idx = np.linspace(0, 1, len(bands))
    shape = 0.75 + 0.55 * np.exp(-((idx - 0.25) ** 2) / 0.08)
    weights = shape / shape.sum()
    energy = float(np.dot(bands, weights))
    
    # Dual envelopes for transient detection
    macro_e = state.get('macro_energy', energy)
    macro_e = 0.94 * macro_e + 0.06 * energy
    state['macro_energy'] = macro_e
    
    fast_e = state.get('fast_energy', energy)
    fast_e = 0.60 * fast_e + 0.40 * energy
    state['fast_energy'] = fast_e
    
    # Transient = fast overshoot of macro
    transient = max(0.0, fast_e - macro_e * 1.03)
    transient_norm = min(1.5, transient / (macro_e * 0.6 + 1e-6))
    
    # High-frequency shimmer
    high_start = int(len(bands) * 0.65)
    shimmer = float(np.mean(bands[high_start:])) ** 0.8
    
    # Quiet gating
    quiet = macro_e < 0.02 and transient_norm < 0.15
    
    return {
        'energy': macro_e,
        'transient': transient_norm,
        'shimmer': shimmer,
        'quiet': quiet
    }


def draw_radial_burst(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                       get_color_func, apply_smoothing_func, state: dict):
    """Draw transient-driven starfield particle system."""
    if width < 10 or height < 6:
        return

    # Clear frame
    for row in range(height):
        try:
            stdscr.move(y_offset + row, 0)
            stdscr.clrtoeol()
        except curses.error:
            pass

    # Process frequency bands
    num_bands = 96
    bands = compute_frequency_bars(audio_data, num_bands, sample_rate=44100)
    bands = _apply_adaptive_eq(bands, state)
    bands = apply_smoothing_func(bands, False)
    state['last_bar_values'] = bands.copy()

    # Compute audio metrics
    metrics = _compute_energy_metrics(bands, state)
    energy = metrics['energy']
    transient = metrics['transient']
    shimmer = metrics['shimmer']
    quiet = metrics['quiet']

    cx, cy = width // 2, height // 2
    rng = np.random.random

    # Global drift animation
    drift_angle = state.get('drift_angle', 0.0) + 0.002
    state['drift_angle'] = drift_angle
    drift_dx = 0.12 * np.cos(drift_angle)
    drift_dy = 0.12 * np.sin(drift_angle) * 0.6

    # Particle spawning based on audio
    particles = state.get('particles', [])
    
    if not quiet:
        base_spawn = int((energy ** 0.85) * 14)
        burst_spawn = int((transient ** 0.9) * 30)
        spawn_count = base_spawn + burst_spawn
        if transient > 0.9:
            spawn_count += 6
        spawn_count = min(spawn_count, 55)
    else:
        spawn_count = 0
    
    # Occasional particle to prevent frozen scene
    frame_counter = state.get('frame_counter', 0) + 1
    state['frame_counter'] = frame_counter
    if spawn_count == 0 and frame_counter % 22 == 0:
        spawn_count = 1

    speed_boost = 0.4 * transient
    
    for _ in range(spawn_count):
        ang = rng() * 2 * np.pi
        base_speed = 0.20 + rng() * 0.45 + energy * 0.55 + shimmer * 0.25 + speed_boost
        vx = np.cos(ang) * base_speed + drift_dx
        vy = np.sin(ang) * base_speed * 0.6 + drift_dy
        max_life = int((width + height) / (base_speed * 1.4) * (0.55 + rng() * 0.4))
        max_life = max(40, min(260, max_life))
        burst_factor = min(1.0, transient * (0.7 + 0.6 * rng()))
        
        # Particle: [x, y, vx, vy, life, max_life, burst_factor]
        particles.append([float(cx), float(cy), vx, vy, 0, max_life, burst_factor])

    # Update particles with velocity damping
    new_particles = []
    damping = 0.995
    for p in particles:
        p[2] *= damping  # vx
        p[3] *= damping  # vy
        p[0] += p[2]     # x
        p[1] += p[3]     # y
        p[4] += 1        # life
        
        # Keep if alive and on screen
        if p[4] < p[5] and -2 <= p[0] < width + 2 and -2 <= p[1] < height + 2:
            new_particles.append(p)
    
    particles = new_particles[-450:]  # Cap particle count
    state['particles'] = particles

    # Render particles
    simple = state.get('simple_ascii')
    
    for p in particles:
        x, y, _, _, life, max_life, burst_factor = p
        life_ratio = life / max_life
        base_brightness = max(0.0, 1.0 - life_ratio)
        
        # Twinkle effect modulated by shimmer
        twinkle = 0.4 + 0.3 * np.sin(life * (0.25 + 0.4 * shimmer) + x * 0.05)
        
        # Early life emphasis for burst particles
        early_boost = 1.0 if life < 6 else np.exp(-(life - 6) * 0.05)
        
        intensity = min(1.0, base_brightness * (0.55 + twinkle) * (1.0 + burst_factor * 0.9 * early_boost))
        color_intensity = intensity * (0.85 + 0.15 * burst_factor) + shimmer * 0.1
        
        x_i, y_i = int(x), int(y)
        if 0 <= x_i < width and 0 <= y_i < height:
            color = get_color_func(color_intensity, x_i / max(1, width - 1))
            
            if simple:
                ch = '*' if intensity > 0.7 else ('+' if intensity > 0.4 else '.')
            else:
                ch = '✦' if intensity > 0.75 else ('✧' if intensity > 0.5 else ('•' if intensity > 0.3 else '·'))
            
            try:
                stdscr.addch(y_i + y_offset, x_i, ord(ch), color)
            except curses.error:
                pass
