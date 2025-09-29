"""Spectrum visualizer - spectrum analyzer with peak indicators."""

import numpy as np
import curses
from .base import compute_frequency_bars


def draw_spectrum(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                  get_color_func, apply_smoothing_func, state: dict):
    """Draw spectrum analyzer with peaks and decay."""
    bar_heights = compute_frequency_bars(audio_data, width)
    bar_heights = apply_smoothing_func(bar_heights, False)
    
    # Track peak values for spectrum analyzer effect
    if 'peak_values' not in state:
        state['peak_values'] = np.zeros(width)
        state['peak_decay'] = np.zeros(width)
    
    peak_values = state['peak_values']
    peak_decay = state['peak_decay']
    
    # Update peaks
    for i in range(len(bar_heights)):
        if bar_heights[i] > peak_values[i]:
            peak_values[i] = bar_heights[i]
            peak_decay[i] = 0
        else:
            # Peak decays slowly
            peak_decay[i] += 0.01
            peak_values[i] = max(0, peak_values[i] - peak_decay[i])
    
    # Draw bars with peak indicators
    for col in range(width):
        height_ratio = bar_heights[col]
        bar_height = int(height_ratio * height)
        peak_height = int(peak_values[col] * height)
        position = col / max(1, width - 1)
        
        # Clear column
        for row in range(height):
            try:
                stdscr.addch(row + y_offset, col, ord(' '))
            except curses.error:
                pass
        
        # Draw bar
        color = get_color_func(height_ratio, position)
        for row in range(height):
            if height - row <= bar_height:
                try:
                    stdscr.addch(row + y_offset, col, ord('▆'), color)
                except curses.error:
                    pass
        
        # Draw peak indicator
        peak_row = height - peak_height
        if 0 <= peak_row < height and peak_height > bar_height:
            try:
                peak_color = get_color_func(peak_values[col], position)
                stdscr.addch(peak_row + y_offset, col, ord('▬'), peak_color)
            except curses.error:
                pass