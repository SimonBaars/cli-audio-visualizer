"""Bars visualizer - classic frequency bars."""

import numpy as np
import curses
from .base import compute_frequency_bars


def draw_bars(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int, 
              get_color_func, apply_smoothing_func, state: dict):
    """Draw classic frequency bars."""
    if width <= 0:
        return
    flatten = state.get('flatten', False)
    bar_heights = compute_frequency_bars(audio_data, width, sample_rate=44100, flatten=flatten)
    bar_heights = apply_smoothing_func(bar_heights, False)
    current_bars = (bar_heights * height).astype(int)

    # Store for snapshot/debug
    state['last_bar_values'] = bar_heights.copy()
    
    # Always clear and redraw all columns for bars mode to prevent artifacts
    for col in range(min(width, len(current_bars))):
        cur_height = current_bars[col]
        
        # Clear the entire column
        for row in range(height):
            try:
                stdscr.addch(row + y_offset, col, ord(' '))
            except curses.error:
                pass
        
        # Draw new bar from bottom up with vertical gradient color
        height_ratio = bar_heights[col]
        position = col / max(1, width - 1)
        
        for row in range(height):
            if height - row <= cur_height:
                # Relative level within bar (bottom 0 -> top 1)
                rel_level = (height - row) / max(1, cur_height)
                # Combine amplitude & vertical position for richer color dynamics
                color = get_color_func(min(1.0, height_ratio * 0.5 + rel_level * 0.5), position)
                try:
                    stdscr.addch(row + y_offset, col, ord('█'), color)
                except curses.error:
                    pass