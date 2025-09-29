"""Levels visualizer - VU meter style horizontal bars."""

import numpy as np
import curses
from .base import compute_frequency_bars


def draw_levels(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                get_color_func, apply_smoothing_func, state: dict):
    """Draw level meters (VU meter style)."""
    bar_heights = compute_frequency_bars(audio_data, 20)  # 20 frequency bands
    bar_heights = apply_smoothing_func(bar_heights, False)
    
    bands_per_row = 4
    rows = min((len(bar_heights) + bands_per_row - 1) // bands_per_row, height // 2)
    bar_width = width // bands_per_row - 2
    
    for idx, height_val in enumerate(bar_heights):
        row = idx // bands_per_row
        col_start = (idx % bands_per_row) * (bar_width + 2)
        
        if row >= rows:
            break
        
        bar_length = int(height_val * bar_width)
        position = idx / max(1, len(bar_heights) - 1)
        
        # Clear the entire row first
        try:
            for x in range(bar_width):
                stdscr.addch(row * 2 + y_offset, col_start + x, ord(' '))
        except curses.error:
            pass
        
        # Draw filled part of bar
        try:
            for x in range(bar_length):
                color = get_color_func(height_val, position)
                stdscr.addch(row * 2 + y_offset, col_start + x, ord('█'), color)
            
            # Draw empty part
            for x in range(bar_length, bar_width):
                stdscr.addch(row * 2 + y_offset, col_start + x, ord('░'), curses.color_pair(7) | curses.A_DIM)
        except curses.error:
            pass