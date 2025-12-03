"""Levels visualizer - dynamic multi-band VU meters with animated peaks and trails.

Features:
- Four frequency bands: Bass, Low-Mid, High-Mid, Treble
- Fast attack / slow decay smoothing for responsive yet smooth animation
- Falling peak indicators with hold
- Fade trails for visual persistence
- Adaptive per-band normalization for balanced display
- Glow effect modulated by overall energy
"""

import numpy as np
import curses
from .base import clear_area

# Frequency band definitions (name, low_hz, high_hz)
FREQUENCY_BANDS = [
    ("BASS", 20, 180),
    ("LOWMID", 180, 600),
    ("HIGHMID", 600, 3500),
    ("TREBLE", 3500, 16000),
]


def _compute_band_levels(audio_data: np.ndarray, sample_rate: int = 44100) -> np.ndarray:
    """Compute RMS levels for each frequency band."""
    fft_size = 4096
    if len(audio_data) < fft_size:
        audio_data = np.pad(audio_data, (0, fft_size - len(audio_data)), 'constant')
    
    window = np.hanning(fft_size)
    fft = np.fft.rfft(audio_data[:fft_size] * window)
    power = np.abs(fft) ** 2
    freqs = np.fft.rfftfreq(fft_size, 1.0 / sample_rate)
    
    levels = np.zeros(len(FREQUENCY_BANDS), dtype=np.float32)
    for i, (_, low, high) in enumerate(FREQUENCY_BANDS):
        mask = (freqs >= low) & (freqs < high)
        if np.any(mask):
            levels[i] = np.sqrt(np.mean(power[mask]))
    
    return levels + 1e-9  # Avoid division by zero


def _apply_smoothing(values: np.ndarray, prev_values: np.ndarray, 
                     attack: float = 0.25, release: float = 0.85) -> np.ndarray:
    """Apply fast attack / slow release temporal smoothing."""
    result = np.zeros_like(values)
    for i in range(len(values)):
        if values[i] > prev_values[i]:
            result[i] = prev_values[i] * (1 - attack) + values[i] * attack
        else:
            result[i] = prev_values[i] * release + values[i] * (1 - release)
    return result


def draw_levels(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                get_color_func, apply_smoothing_func, state: dict):
    """Draw multi-band VU meters with peaks and trails."""
    
    # Compute raw band levels
    raw_vals = _compute_band_levels(audio_data)
    num_bands = len(raw_vals)
    
    # Adaptive per-band normalization (slow reference tracking)
    run_ref = state.get('run_ref')
    if run_ref is None or len(run_ref) != num_bands:
        run_ref = raw_vals.copy()
    else:
        run_ref = 0.995 * run_ref + 0.005 * raw_vals
    state['run_ref'] = run_ref
    
    # Normalize and compress
    norm_vals = raw_vals / run_ref
    norm_vals /= (np.max(norm_vals) + 1e-9)
    norm_vals = np.power(norm_vals, 0.72)  # Perceptual compression
    
    # Temporal smoothing
    prev_levels = state.get('prev_levels')
    if prev_levels is None or len(prev_levels) != num_bands:
        prev_levels = norm_vals.copy()
    disp_levels = _apply_smoothing(norm_vals, prev_levels)
    state['prev_levels'] = disp_levels.copy()
    
    # Peak tracking with fall
    peaks = state.get('peaks')
    if peaks is None or len(peaks) != num_bands:
        peaks = disp_levels.copy()
    fall_speed = 0.02
    peaks = np.where(disp_levels > peaks, disp_levels, np.maximum(0, peaks - fall_speed))
    state['peaks'] = peaks.copy()
    
    # Glow energy tracking
    energy = float(np.mean(raw_vals))
    glow = state.get('glow', energy)
    glow = 0.97 * glow + 0.03 * energy
    state['glow'] = glow
    glow_norm = min(1.0, glow / (np.max(run_ref) + 1e-9))
    
    # Clear and prepare layout
    clear_area(stdscr, y_offset, height, width)
    state['last_levels'] = [(FREQUENCY_BANDS[i][0], disp_levels[i]) for i in range(num_bands)]
    
    # Layout calculations
    gap = 2
    usable_w = max(10, width - (num_bands + 1) * gap)
    col_w = max(6, usable_w // num_bands)
    meter_height = max(5, height - 4)
    base_y = y_offset + height - 2
    
    simple = state.get('simple_ascii')
    fill_char = ord('#') if simple else ord('█')
    trail_char = ord('+') if simple else ord('▒')
    peak_char = ord('-') if simple else ord('─')
    
    # Trail buffers
    trails = state.get('trails')
    if trails is None or len(trails) != num_bands:
        trails = [np.zeros(meter_height) for _ in range(num_bands)]
    
    # Draw each band
    for i in range(num_bands):
        name = FREQUENCY_BANDS[i][0]
        val = disp_levels[i]
        peak = peaks[i]
        position = i / max(1, num_bands - 1)
        col_x = gap + i * (col_w + gap)
        
        # Update trail
        trails[i] *= 0.88
        h_active = int(val * meter_height)
        if h_active > 0:
            trails[i][:h_active] = 1.0
        
        # Draw meter rows
        for row in range(meter_height):
            screen_y = base_y - 1 - row
            if screen_y < y_offset or screen_y >= y_offset + height:
                continue
            
            is_filled = row < h_active
            trail_val = trails[i][row]
            
            # Compute color intensity
            intensity = min(1.0, (0.5 * trail_val + 0.5 * val) * (0.6 + 0.4 * glow_norm))
            color = get_color_func(intensity, position)
            
            # Select glyph
            if is_filled:
                glyph = fill_char
            elif trail_val > 0.05:
                glyph = trail_char
            else:
                continue  # Skip empty cells
            
            # Draw horizontal span
            for dx in range(col_w):
                try:
                    stdscr.addch(screen_y, col_x + dx, glyph, color)
                except curses.error:
                    pass
        
        # Peak indicator
        peak_row = int(peak * meter_height)
        if peak_row > 0:
            peak_y = base_y - 1 - peak_row
            if y_offset <= peak_y < y_offset + height - 1:
                peak_color = get_color_func(1.0, position) | curses.A_BOLD
                for dx in range(col_w):
                    try:
                        stdscr.addch(peak_y, col_x + dx, peak_char, peak_color)
                    except curses.error:
                        pass
        
        # Label
        label = name.center(col_w)[:col_w]
        try:
            stdscr.addstr(base_y, col_x, label, curses.color_pair(7) | curses.A_BOLD)
        except curses.error:
            pass
        
        # Percentage
        pct_str = f"{int(val * 100):3d}%"
        try:
            stdscr.addstr(base_y - meter_height - 1, col_x, pct_str[:col_w], curses.color_pair(7))
        except curses.error:
            pass
    
    state['trails'] = trails