"""Radial Burst visualizer - pulsating radial energy spokes with fading trails.

Transforms frequency bands into expanding/contracting radial spokes around center.
Each frame, spoke lengths are smoothed; prior frame fades for a particle-like afterglow.
"""
import numpy as np
import curses
from audio_visualizer.dsp.bars import compute_frequency_bars


def draw_radial_burst(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                       get_color_func, apply_smoothing_func, state: dict):
    if width < 10 or height < 6:
        return

    # Number of spokes limited by perimeter density
    num_spokes = max(24, min(120, int((width + height) * 0.8)))
    flatten = state.get('flatten', False)
    # Use bar computation but request num_spokes bands
    bands = compute_frequency_bars(audio_data, num_spokes, sample_rate=44100, flatten=flatten)
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

    # Fading trail buffer (2D) - store brightness per cell (float 0..1)
    trail = state.get('trail')
    if trail is None or trail.shape != (height, width):
        trail = np.zeros((height, width), dtype=np.float32)

    # Fade previous frame
    trail *= 0.85

    cx, cy = width // 2, height // 2
    max_r = min(width, height) // 2 - 1
    if max_r <= 0:
        return

    # Draw spokes
    for i in range(num_spokes):
        val = bands[i]
        # Non-linear exaggeration for burstiness
        val_disp = val ** 0.6
        r = int(val_disp * max_r)
        angle = (i / num_spokes) * 2 * np.pi
        dx = np.cos(angle)
        dy = np.sin(angle) * 0.6  # vertical squish
        position = i / max(1, num_spokes - 1)

        for step in range(r):
            x = int(cx + dx * step)
            y = int(cy + dy * step)
            if 0 <= x < width and 0 <= y < height:
                # Increase trail brightness
                trail[y, x] = max(trail[y, x], 0.4 + 0.6 * (step / max(1, r - 1)))

    # ---------------- Sparkly star particles ----------------
    # Particles emitted from center with outward velocity and short lifetimes.
    particles = state.get('particles')
    if particles is None:
        particles = []

    energy = float(np.mean(bands)) if len(bands) else 0.0
    # Spawn rate scales with energy (capped for performance)
    spawn_count = min(60, int(2 + energy * 25))
    rng = np.random.random
    for _ in range(spawn_count):
        ang = rng() * 2 * np.pi
        base_speed = 0.4 + rng() * 1.2 * (0.5 + energy * 1.2)
        vx = np.cos(ang) * base_speed
        vy = np.sin(ang) * base_speed * 0.6  # keep vertical squish
        max_life = 12 + int(rng() * 18)
        particles.append([cx + 0.0, cy + 0.0, vx, vy, 0, max_life])  # x,y,vx,vy,life,max_life

    # Update particles
    new_particles = []
    for p in particles:
        p[0] += p[2]
        p[1] += p[3]
        p[4] += 1  # life
        if p[4] < p[5] and 0 <= p[0] < width and 0 <= p[1] < height:
            new_particles.append(p)
    particles = new_particles

    # Render trail buffer first (background glow)
    simple = state.get('simple_ascii')
    for y in range(height):
        row_trail = trail[y]
        for x in range(width):
            b = row_trail[x]
            if b <= 0.02:
                continue
            color = get_color_func(b, x / max(1, width - 1))
            if simple:
                if b > 0.75: ch = '*'
                elif b > 0.5: ch = '+'
                elif b > 0.3: ch = '.'
                else: ch = '·'
            else:
                if b > 0.75: ch = '✶'
                elif b > 0.5: ch = '✳'
                elif b > 0.3: ch = '•'
                else: ch = '·'
            try:
                stdscr.addch(y + y_offset, x, ord(ch), color)
            except curses.error:
                pass

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

    state['trail'] = trail
    state['particles'] = particles
