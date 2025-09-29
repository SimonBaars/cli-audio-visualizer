"""Spectrum visualizer - thin bars with gaps like pro audio equipment."""

import numpy as np
import curses
from .base import compute_frequency_bars


def draw_spectrum(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                  get_color_func, apply_smoothing_func, state: dict):
    """Draw spectrum analyzer with thin bars and gaps."""
    # Use fewer bars (half width) with gaps between
    num_bars = max(1, width // 2)
    bar_heights = compute_frequency_bars(audio_data, num_bars, sample_rate=44100)
    bar_heights = apply_smoothing_func(bar_heights, False)
    state['last_bar_values'] = bar_heights.copy()
    
    # Track peak values for spectrum analyzer effect
    if 'peak_values' not in state:
        state['peak_values'] = np.zeros(num_bars)
        state['peak_decay'] = np.zeros(num_bars)
    
    peak_values = state['peak_values']
    peak_decay = state['peak_decay']
    
    # Update peaks
    for i in range(len(bar_heights)):
        if bar_heights[i] > peak_values[i]:
            peak_values[i] = bar_heights[i]
            peak_decay[i] = 0
        else:
            # Peak decays slowly
            peak_decay[i] += 0.008
            peak_values[i] = max(0, peak_values[i] - peak_decay[i])
    
    # Clear entire area + draw faint horizontal grid every 4 rows for readability
    for row in range(height):
        is_grid = (row % 4 == 0 and row not in (0, height-1))
        for col in range(width):
            try:
                if is_grid:
                    stdscr.addch(row + y_offset, col, ord('·'), curses.color_pair(7) | curses.A_DIM)
                else:
                    stdscr.addch(row + y_offset, col, ord(' '))
            except curses.error:
                pass
    
    # Draw bars with gaps (every other column)
    for bar_idx in range(num_bars):
        col = bar_idx * 2  # Leave gap
        
        if col >= width:
            break
        
        height_ratio = bar_heights[bar_idx]
        bar_height = int(height_ratio * height)
        peak_height = int(peak_values[bar_idx] * height)
        position = bar_idx / max(1, num_bars - 1)
        
        # Draw gradient bar using two glyph regions: solid lower, light upper
        for row in range(height):
            if height - row <= bar_height:
                rel = (height - row) / max(1, bar_height)
                glyph = '█' if rel < 0.55 else ('▓' if rel < 0.8 else '░')
                row_level = min(1.0, (height_ratio * 0.6) + rel * 0.4)
                color = get_color_func(row_level, position)
                try:
                    stdscr.addch(row + y_offset, col, ord(glyph), color)
                except curses.error:
                    pass
        
        # Draw peak indicator
        peak_row = height - peak_height
        if 0 <= peak_row < height:
            try:
                peak_color = get_color_func(peak_values[bar_idx], position)
                marker_char = '▲' if peak_height > bar_height else '·'
                stdscr.addch(peak_row + y_offset, col, ord(marker_char), peak_color)
            except curses.error:
                pass