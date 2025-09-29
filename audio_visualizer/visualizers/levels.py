"""Levels visualizer - dynamic multi-band VU with animated fall, trails & glow.

Upgrades:
 - Faster attack / slower decay smoothing for lively movement
 - Peak hold + falling peak bar
 - Vertical stacked meter per band (instead of single horizontal)
 - Trail / fade effect using dim characters
 - Pulsing color glow influenced by recent energy
 - Soft dynamic EQ normalizing bands over time for fairness
"""

import numpy as np
import curses
from .base import clear_area


def draw_levels(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                get_color_func, apply_smoothing_func, state: dict):
    """Draw flashy multi-band level meters.

    Layout: each band rendered as a vertical column with animated peak fall and
    fading trail. Uses adaptive normalization to keep all bands active.
    """
    # Process FFT for specific frequency ranges
    fft_size = 4096
    if len(audio_data) < fft_size:
        audio_data = np.pad(audio_data, (0, fft_size - len(audio_data)), 'constant')
    
    # Apply window to reduce leakage that exaggerates low bins
    window = np.hanning(fft_size)
    fft = np.fft.rfft(audio_data[:fft_size] * window)
    power = (np.abs(fft) ** 2)
    freqs = np.fft.rfftfreq(fft_size, 1.0 / 44100)
    
    # Frequency ranges (tuned for musical balance)
    ranges = [
        ("BASS", 20, 180),
        ("LOWMID", 180, 600),
        ("HIGHMID", 600, 3500),
        ("TREBLE", 3500, 16000)
    ]
    
    levels = []
    for name, low, high in ranges:
        mask = (freqs >= low) & (freqs < high)
        if np.any(mask):
            band = power[mask]
            rms = float(np.sqrt(np.mean(band)))
        else:
            rms = 0.0
        levels.append((name, rms))
    
    # Raw RMS array
    raw_vals = np.array([l[1] for l in levels], dtype=np.float32) + 1e-9

    # Running reference (slow) for adaptive per-band normalization
    run_ref = state.get('run_ref')
    if run_ref is None or len(run_ref) != len(raw_vals):
        run_ref = raw_vals.copy()
    else:
        # Very slow update so sudden spikes show vividly
        run_ref = 0.995 * run_ref + 0.005 * raw_vals
    state['run_ref'] = run_ref

    norm_vals = raw_vals / run_ref
    # Global scaling
    norm_vals /= (np.max(norm_vals) + 1e-9)

    # Perceptual compression for smoother motion
    norm_vals = np.power(norm_vals, 0.72)

    levels = [(levels[i][0], float(norm_vals[i])) for i in range(len(levels))]
    
    # Temporal smoothing: fast attack, slower release
    attack = 0.25
    release = 0.85
    prev_levels = state.get('prev_levels')
    disp_levels = []
    if prev_levels is None or len(prev_levels) != len(levels):
        prev_levels = [l[1] for l in levels]
    for i, (name, val) in enumerate(levels):
        pv = prev_levels[i]
        if val > pv:
            pv = pv * (1 - attack) + val * attack
        else:
            pv = pv * release + val * (1 - release)
        disp_levels.append(pv)
    state['prev_levels'] = disp_levels

    # Peak hold + fall speed
    peaks = state.get('peaks')
    if peaks is None or len(peaks) != len(levels):
        peaks = disp_levels.copy()
    fall_speed = state.get('peak_fall_speed', 0.02)
    for i, val in enumerate(disp_levels):
        if val > peaks[i]:
            peaks[i] = val
        else:
            peaks[i] = max(0.0, peaks[i] - fall_speed)
    state['peaks'] = peaks

    # Glow energy (overall recent energy) for pulsing brightness
    energy = float(np.mean(raw_vals))
    glow = state.get('glow', energy)
    glow = 0.97 * glow + 0.03 * energy
    state['glow'] = glow
    glow_norm = min(1.0, glow / (np.max(run_ref) + 1e-9))
    
    # Clear area
    clear_area(stdscr, y_offset, height, width)

    # Store snapshot data
    state['last_levels'] = list(zip([n for n,_ in levels], disp_levels))

    num_bands = len(disp_levels)
    # Compute column width per band
    gap = 2
    usable_w = max(10, width - (num_bands + 1) * gap)
    col_w = max(6, usable_w // num_bands)
    meter_height = max(5, height - 4)
    base_y = y_offset + height - 2

    # Draw each band as vertical bar
    for i, (name, _) in enumerate(levels):
        val = disp_levels[i]
        peak = peaks[i]
        position = i / max(1, num_bands - 1)
        col_x = gap + i * (col_w + gap)

        # Label (centered under column)
        label = name.center(col_w)
        try:
            stdscr.addstr(base_y, col_x, label[:col_w], curses.color_pair(7) | curses.A_BOLD)
        except curses.error:
            pass

        # Height of active segment
        h_active = int(val * meter_height)
        peak_row = int(peak * meter_height)

        # Trail memory buffer (per band) for fade effect
        trails = state.get('trails')
        if trails is None or len(trails) != num_bands:
            trails = [np.zeros(meter_height) for _ in range(num_bands)]
        # Decay trails
        trails[i] *= 0.88
        # Set new active region brightness
        if h_active > 0:
            trails[i][:h_active] = 1.0
        state['trails'] = trails

        band_trail = trails[i]

        # Draw from bottom (row 0) upward
        for level_row in range(meter_height):
            filled = level_row < h_active
            trail_val = band_trail[level_row]
            rel = level_row / max(1, meter_height - 1)
            # Color intensity combines fill, trail and glow
            intensity = (0.5 * trail_val + 0.5 * val) * (0.6 + 0.4 * glow_norm)
            intensity = min(1.0, intensity)
            color = get_color_func(intensity, position)
            screen_y = base_y - 1 - level_row
            if screen_y < y_offset or screen_y >= y_offset + height:
                continue
            # Choose glyph based on whether inside active, trail, or empty
            if filled:
                glyph = '█'
            elif trail_val > 0.05:
                glyph = '▒'
            else:
                glyph = ' '
            # Draw horizontal span for thickness
            for dx in range(col_w):
                try:
                    if glyph != ' ':
                        stdscr.addch(screen_y, col_x + dx, ord(glyph), color)
                except curses.error:
                    pass

        # Peak indicator (falling)
        if peak_row > 0:
            py = base_y - 1 - peak_row
            if y_offset <= py < y_offset + height - 1:
                try:
                    peak_color = get_color_func(1.0, position) | curses.A_BOLD
                    for dx in range(col_w):
                        stdscr.addch(py, col_x + dx, ord('─'), peak_color)
                except curses.error:
                    pass

        # Percentage centered above column top
        pct = int(val * 100)
        pct_str = f"{pct:3d}%"
        try:
            stdscr.addstr(base_y - meter_height - 1, col_x, pct_str[:col_w], curses.color_pair(7))
        except curses.error:
            pass