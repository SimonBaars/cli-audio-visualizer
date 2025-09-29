"""Radial Burst visualizer - pure starfield burst.

Simplified per request: removed lingering radial glow/trails. Now only
sparkly star particles emit from the center and fly outward all the way
until they exit the screen. Frequency bands modulate spawn rate and
initial velocity. The previous spoke backdrop is removed for a cleaner,
minimal cosmic look.
"""
import numpy as np
import curses
from audio_visualizer.dsp.bars import compute_frequency_bars


def draw_radial_burst(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                       get_color_func, apply_smoothing_func, state: dict):
    if width < 10 or height < 6:
        return

    # Full clear (no trails) for a pristine starfield each frame
    for row in range(height):
        try:
            stdscr.move(y_offset + row, 0)
            stdscr.clrtoeol()
        except curses.error:
            pass

    # Use some bands only to derive energy; we don't draw them directly anymore.
    num_energy_bands = 96
    flatten = state.get('flatten', False)
    bands = compute_frequency_bars(audio_data, num_energy_bands, sample_rate=44100, flatten=flatten)
    if state.get('adaptive_eq'):
        run_mean = state.get('adaptive_eq_mean')
        if run_mean is None or len(run_mean) != len(bands):
            run_mean = np.copy(bands)
        else:
            run_mean = 0.995 * run_mean + 0.005 * bands
        eq_strength = state.get('adaptive_eq_strength', 0.65)
        adj = bands / (run_mean + 1e-6)
        if np.max(adj) > 0:
            adj /= np.max(adj)
        bands = (1 - eq_strength) * bands + eq_strength * adj
        state['adaptive_eq_mean'] = run_mean
    bands = apply_smoothing_func(bands, False)
    state['last_bar_values'] = bands.copy()

    cx, cy = width // 2, height // 2

    # ---------------- Sparkly star particles ----------------
    # Particles emitted from center with outward velocity and short lifetimes.
    particles = state.get('particles')
    if particles is None:
        particles = []

    # Weighted energy: emphasize lows & mids gently, suppress constant hiss
    if len(bands):
        idx = np.linspace(0, 1, len(bands))
        w = 0.9 - 0.4 * (idx ** 1.3)  # slightly more weight to lower half
        w /= w.sum()
        energy = float(np.dot(bands, w))
    else:
        energy = 0.0

    # Smoothed macro energy envelope for calmer behavior
    macro_e = state.get('macro_energy', energy)
    macro_e = 0.97 * macro_e + 0.03 * energy
    state['macro_energy'] = macro_e

    # Spawn count lowered for chill vibe; slight exponential response to peaks
    spawn_count = int(1 + (macro_e ** 0.8) * 18)
    spawn_count = min(spawn_count, 40)
    rng = np.random.random
    # Small global drift (slowly rotating field)
    drift_angle = state.get('drift_angle', 0.0) + 0.002
    state['drift_angle'] = drift_angle
    drift_dx = 0.12 * np.cos(drift_angle)
    drift_dy = 0.12 * np.sin(drift_angle) * 0.6

    # Derive per-band speed bias (higher bands add shimmer)
    high_energy = float(np.mean(bands[int(len(bands)*0.65):])) if len(bands) else 0.0
    shimmer = (high_energy ** 0.8)

    for _ in range(spawn_count):
        ang = rng() * 2 * np.pi
        # Base speed tempered for chill; add subtle shimmer modulation
        base_speed = 0.25 + rng() * 0.55 + macro_e * 0.6 + shimmer * 0.3
        vx = np.cos(ang) * base_speed + drift_dx
        vy = (np.sin(ang) * base_speed * 0.6) + drift_dy
        # Lifetime longer for slower calm motion
        max_life = int((width + height) / (base_speed * 1.4) * (0.55 + rng() * 0.4))
        max_life = max(40, min(260, max_life))
        particles.append([cx + 0.0, cy + 0.0, vx, vy, 0, max_life])

    # Update particles
    new_particles = []
    for p in particles:
        # Gentle velocity damping for glide effect
        p[2] *= 0.995
        p[3] *= 0.995
        p[0] += p[2]
        p[1] += p[3]
        p[4] += 1
        if p[4] < p[5] and -2 <= p[0] < width + 2 and -2 <= p[1] < height + 2:
            new_particles.append(p)
    # Lower cap (calmer density)
    particles = new_particles[-450:]

    simple = state.get('simple_ascii')

    # Render particles on top (sharper stars)
    for p in particles:
        life_ratio = p[4] / p[5]
        b = max(0.0, 1.0 - life_ratio)
        # Softer twinkle; modulated by shimmer (high freq energy)
        twinkle = 0.4 + 0.3 * np.sin(p[4] * (0.25 + 0.4 * shimmer) + p[0] * 0.05)
        intensity = min(1.0, b * (0.6 + twinkle))
        color = get_color_func(intensity * 0.9 + shimmer * 0.1, p[0] / max(1, width - 1))
        x_i = int(p[0])
        y_i = int(p[1])
        if 0 <= x_i < width and 0 <= y_i < height:
            if simple:
                if intensity > 0.7: ch = '*'
                elif intensity > 0.4: ch = '+'
                else: ch = '.'
            else:
                if intensity > 0.75: ch = '✦'
                elif intensity > 0.5: ch = '✧'
                elif intensity > 0.3: ch = '•'
                else: ch = '·'
            try:
                stdscr.addch(y_i + y_offset, x_i, ord(ch), color)
            except curses.error:
                pass

    state['particles'] = particles
