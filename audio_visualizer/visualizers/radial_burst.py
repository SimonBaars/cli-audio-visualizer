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

    # Render trail buffer
    for y in range(height):
        for x in range(width):
            b = trail[y, x]
            if b <= 0.02:
                continue
            # Color intensity linked to brightness
            color = get_color_func(b, x / max(1, width - 1))
            # Choose glyph by brightness tiers
            if b > 0.75:
                ch = '✶'
            elif b > 0.5:
                ch = '✳'
            elif b > 0.3:
                ch = '•'
            else:
                ch = '·'
            try:
                stdscr.addch(y + y_offset, x, ord(ch), color)
            except curses.error:
                pass

    state['trail'] = trail
