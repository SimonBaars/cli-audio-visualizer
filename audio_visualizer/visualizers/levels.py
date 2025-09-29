"""Levels visualizer - large block VU meters for key frequency ranges."""

import numpy as np
import curses
from .base import clear_area


def draw_levels(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                get_color_func, apply_smoothing_func, state: dict):
    """Draw large block-style VU meters for bass, mid, treble."""
    # Process FFT for specific frequency ranges
    fft_size = 4096
    if len(audio_data) < fft_size:
        audio_data = np.pad(audio_data, (0, fft_size - len(audio_data)), 'constant')
    
    # Apply window to reduce leakage that exaggerates low bins
    window = np.hanning(fft_size)
    fft = np.fft.rfft(audio_data[:fft_size] * window)
    power = (np.abs(fft) ** 2)
    freqs = np.fft.rfftfreq(fft_size, 1.0 / 44100)
    
    # Define 3 main frequency ranges
    # Slightly adjusted bands to give highs more energy and split mids
    ranges = [
        ("BASS", 20, 220),
        ("LOWMID", 220, 800),
        ("HIGHMID", 800, 4000),
        ("TREBLE", 4000, 16000)
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
    
    # Adaptive normalization: subtract median (noise floor), then scale
    raw_vals = np.array([l[1] for l in levels], dtype=np.float32)
    if np.any(raw_vals > 0):
        median_floor = np.median(raw_vals)
        raw_vals = np.clip(raw_vals - median_floor * 0.5, 0, None)
        max_val = np.max(raw_vals)
        if max_val > 0:
            norm_vals = raw_vals / max_val
        else:
            norm_vals = raw_vals
    else:
        norm_vals = raw_vals

    # Dynamic range compression (soft knee) to keep movement visible
    if np.any(norm_vals > 0):
        norm_vals = np.power(norm_vals, 0.85)

    levels = [(levels[i][0], float(norm_vals[i])) for i in range(len(levels))]
    
    # Apply smoothing
    if 'prev_levels' not in state or len(state['prev_levels']) != len(levels):
        state['prev_levels'] = [l[1] for l in levels]
        state['peaks'] = [l[1] for l in levels]
    else:
        new_levels = []
        peaks = state.get('peaks', [0]*len(levels))
        for i, (name, level) in enumerate(levels):
            prev = state['prev_levels'][i]
            smoothed_val = 0.6 * prev + 0.4 * level
            new_levels.append((name, smoothed_val))
            # Peak decay
            if level > peaks[i]:
                peaks[i] = level
            else:
                peaks[i] = max(0.0, peaks[i] - 0.01)
        levels = new_levels
        state['prev_levels'] = [l[1] for l in levels]
        state['peaks'] = peaks
    
    # Clear entire area
    clear_area(stdscr, y_offset, height, width)
    
    # Store for snapshots
    state['last_levels'] = [l for l in levels]

    # Calculate layout - 3 large blocks
    block_height = max(3, height // len(levels))
    
    for idx, (name, level) in enumerate(levels):
        block_y = idx * block_height + y_offset
        
        # Draw label
        label = f" {name} "
        try:
            stdscr.addstr(block_y, 2, label, curses.color_pair(7) | curses.A_BOLD)
        except curses.error:
            pass
        
        # Draw horizontal bar
    bar_y = block_y + block_height // 2
        bar_width = width - 4
        # Log-like perceptual scaling for more movement (compress extremes)
    level_disp = np.power(level, 0.7)
        bar_length = int(level_disp * bar_width)
        
        # Determine color based on level
        position = idx / max(1, len(levels) - 1)
        
        # Draw filled portion with blocks
        for x in range(bar_length):
            x_pos = 2 + x
            # Calculate level for this position
            local_level = (x + 1) / bar_width
            color = get_color_func(local_level, position)
            
            try:
                # Use solid blocks
                stdscr.addch(bar_y, x_pos, ord('█'), color)
                # Draw above and below for thickness
                if block_height > 3:
                    stdscr.addch(bar_y - 1, x_pos, ord('█'), color)
                    stdscr.addch(bar_y + 1, x_pos, ord('█'), color)
            except curses.error:
                pass
        
        # Draw empty portion
        for x in range(bar_length, bar_width):
            x_pos = 2 + x
            try:
                stdscr.addch(bar_y, x_pos, ord('─'), curses.color_pair(7) | curses.A_DIM)
                if block_height > 3:
                    stdscr.addch(bar_y - 1, x_pos, ord('─'), curses.color_pair(7) | curses.A_DIM)
                    stdscr.addch(bar_y + 1, x_pos, ord('─'), curses.color_pair(7) | curses.A_DIM)
            except curses.error:
                pass
        
        # Draw percentage
        percentage = int(level * 100)
        pct_str = f"{percentage}%"
        try:
            stdscr.addstr(bar_y, width - 6, pct_str, curses.color_pair(7))
        except curses.error:
            pass

        # Draw peak marker (triangle) above bar center line if space
        peak_level = state['peaks'][idx]
        peak_len = int(np.power(peak_level, 0.7) * bar_width)
        if peak_len > 0 and peak_len < bar_width:
            try:
                stdscr.addch(bar_y - 1 if block_height > 3 else bar_y, 2 + peak_len, ord('▲'), curses.color_pair(6))
            except curses.error:
                pass