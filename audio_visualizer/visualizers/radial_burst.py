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
    num_energy_bands = 64
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

    energy = float(np.mean(bands)) if len(bands) else 0.0
    # Spawn rate scales with energy (higher ceiling now that trails removed)
    spawn_count = min(120, int(4 + energy * 50))
    rng = np.random.random
    for _ in range(spawn_count):
        ang = rng() * 2 * np.pi
        base_speed = 0.6 + rng() * 1.8 * (0.5 + energy * 1.5)
        vx = np.cos(ang) * base_speed
        vy = np.sin(ang) * base_speed * 0.6  # keep vertical squish
        # Increase lifetime so stars can reach edges; scale with speed
        max_life = int((width + height) / (base_speed * 2.2) * (0.4 + rng() * 0.6))
        max_life = max(15, min(180, max_life))
        particles.append([cx + 0.0, cy + 0.0, vx, vy, 0, max_life])  # x,y,vx,vy,life,max_life

    # Update particles
    new_particles = []
    for p in particles:
        p[0] += p[2]
        p[1] += p[3]
        p[4] += 1  # life
        if p[4] < p[5] and 0 <= p[0] < width and 0 <= p[1] < height:
            new_particles.append(p)
    # Cap total particles to avoid flooding when energy stays high
    particles = new_particles[-800:]

    simple = state.get('simple_ascii')

    # Render particles on top (sharper stars)
    for p in particles:
        life_ratio = p[4] / p[5]
        b = max(0.0, 1.0 - life_ratio)
        # Twinkle modulation
        twinkle = 0.6 + 0.4 * np.sin(p[4] * 0.6 + p[0] * 0.2)
        intensity = min(1.0, b * twinkle)
        color = get_color_func(intensity, p[0] / max(1, width - 1))
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
