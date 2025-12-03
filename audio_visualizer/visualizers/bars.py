"""Bars visualizer - classic frequency bars with smooth gradient coloring."""

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


def _spatial_smooth(values: np.ndarray) -> np.ndarray:
    """Vectorized spatial smoothing - heavier on high-frequency end."""
    n = len(values)
    if n < 5:
        return values
    # Build weight array: low at bass, higher toward treble
    frac = np.linspace(0, 1, n)
    weights = 0.15 + 0.35 * (frac ** 1.1)
    # Neighbor average using shifted arrays (no loop)
    padded = np.pad(values, 1, mode='edge')
    neighbor_avg = (padded[:-2] + padded[1:-1] + padded[2:]) / 3.0
    return (1 - weights) * values + weights * neighbor_avg


def draw_bars(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int, 
              get_color_func, apply_smoothing_func, state: dict):
    """Draw classic frequency bars with per-row gradient coloring."""
    if width <= 0 or height <= 0:
        return
    
    bar_heights = compute_frequency_bars(audio_data, width, sample_rate=44100)
    bar_heights = _apply_adaptive_eq(bar_heights, state)
    bar_heights = apply_smoothing_func(bar_heights, False)
    bar_heights = _spatial_smooth(bar_heights)
    
    current_bars = (bar_heights * height).astype(int)
    state['last_bar_values'] = bar_heights.copy()
    
    # Precompute position array for color lookups
    positions = np.linspace(0, 1, width) if width > 1 else np.array([0.5])
    simple = state.get('simple_ascii')
    bar_char = ord('|') if simple else ord('█')
    
    # Draw all bars
    n_bars = min(width, len(current_bars))
    for col in range(n_bars):
        cur_h = current_bars[col]
        h_ratio = bar_heights[col]
        pos = positions[col]
        
        # Clear column and draw bar in one pass
        for row in range(height):
            y = row + y_offset
            if height - row <= cur_h:
                # Inside bar: compute gradient color based on vertical position
                rel_level = (height - row) / max(1, cur_h)
                color = get_color_func(min(1.0, h_ratio * 0.5 + rel_level * 0.5), pos)
                try:
                    stdscr.addch(y, col, bar_char, color)
                except curses.error:
                    pass
            else:
                try:
                    stdscr.addch(y, col, ord(' '))
                except curses.error:
                    pass