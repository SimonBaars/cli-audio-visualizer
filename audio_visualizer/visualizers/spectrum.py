"""Spectrum visualizer - thin bars with gaps like pro audio equipment."""

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
    """Vectorized spatial smoothing for high-frequency stability."""
    n = len(values)
    if n < 5:
        return values
    frac = np.linspace(0, 1, n)
    weights = 0.12 + 0.3 * (frac ** 1.1)
    padded = np.pad(values, 1, mode='edge')
    neighbor_avg = (padded[:-2] + padded[1:-1] + padded[2:]) / 3.0
    return (1 - weights) * values + weights * neighbor_avg


def draw_spectrum(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                  get_color_func, apply_smoothing_func, state: dict):
    """Draw spectrum analyzer with thin bars, gaps, and peak indicators."""
    num_bars = max(1, width // 2)
    
    bar_heights = compute_frequency_bars(audio_data, num_bars, sample_rate=44100)
    bar_heights = _apply_adaptive_eq(bar_heights, state)
    bar_heights = apply_smoothing_func(bar_heights, False)
    bar_heights = _spatial_smooth(bar_heights)
    state['last_bar_values'] = bar_heights.copy()
    
    # Vectorized peak tracking
    peak_values = state.get('peak_values')
    peak_decay = state.get('peak_decay')
    if peak_values is None or len(peak_values) != num_bars:
        peak_values = np.zeros(num_bars)
        peak_decay = np.zeros(num_bars)
    
    # Update peaks vectorized: where new > old, reset; else decay
    new_peak_mask = bar_heights > peak_values
    peak_values = np.where(new_peak_mask, bar_heights, 
                           np.maximum(0, peak_values - peak_decay))
    peak_decay = np.where(new_peak_mask, 0.0, peak_decay + 0.008)
    state['peak_values'] = peak_values
    state['peak_decay'] = peak_decay
    
    # Clear with grid pattern (vectorized row check)
    grid_rows = set(r for r in range(height) if r % 4 == 0 and r not in (0, height-1))
    for row in range(height):
        is_grid = row in grid_rows
        y = row + y_offset
        for col in range(width):
            try:
                if is_grid:
                    stdscr.addch(y, col, ord('·'), curses.color_pair(7) | curses.A_DIM)
                else:
                    stdscr.addch(y, col, ord(' '))
            except curses.error:
                pass
    
    # Draw bars with gaps
    simple = state.get('simple_ascii')
    positions = np.linspace(0, 1, num_bars) if num_bars > 1 else np.array([0.5])
    
    for bar_idx in range(num_bars):
        col = bar_idx * 2
        if col >= width:
            break
        
        h_ratio = bar_heights[bar_idx]
        bar_h = int(h_ratio * height)
        peak_h = int(peak_values[bar_idx] * height)
        pos = positions[bar_idx]
        
        # Draw gradient bar
        for row in range(height):
            if height - row <= bar_h:
                rel = (height - row) / max(1, bar_h)
                if simple:
                    glyph = ord('|') if rel < 0.7 else ord(':')
                else:
                    glyph = ord('█') if rel < 0.55 else (ord('▓') if rel < 0.8 else ord('░'))
                intensity = min(1.0, h_ratio * 0.6 + rel * 0.4)
                color = get_color_func(intensity, pos)
                try:
                    stdscr.addch(row + y_offset, col, glyph, color)
                except curses.error:
                    pass
        
        # Draw peak indicator
        peak_row = height - peak_h
        if 0 <= peak_row < height:
            peak_color = get_color_func(peak_values[bar_idx], pos)
            marker = ord('▲') if peak_h > bar_h else ord('·')
            try:
                stdscr.addch(peak_row + y_offset, col, marker, peak_color)
            except curses.error:
                pass