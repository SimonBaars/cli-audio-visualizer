"""Bars visualizer - classic frequency bars."""

import numpy as np
import curses
from .base import compute_frequency_bars


def draw_bars(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int, 
              get_color_func, apply_smoothing_func, state: dict):
    """Draw classic frequency bars."""
    bar_heights = compute_frequency_bars(audio_data, width)
    bar_heights = apply_smoothing_func(bar_heights, False)
    current_bars = (bar_heights * height).astype(int)
    
    # Debug: Store max level for verification
    if 'debug_counter' not in state:
        state['debug_counter'] = 0
    state['debug_counter'] += 1
    
    # Log color distribution every 60 frames for debugging
    if state['debug_counter'] % 60 == 0 and np.max(bar_heights) > 0:
        import sys
        print(f"DEBUG: max bar_height={np.max(bar_heights):.3f}, " + 
              f"min={np.min(bar_heights):.3f}, " +
              f"mean={np.mean(bar_heights):.3f}", file=sys.stderr)
    
    # Always clear and redraw all columns for bars mode to prevent artifacts
    for col in range(min(width, len(current_bars))):
        cur_height = current_bars[col]
        
        # Clear the entire column
        for row in range(height):
            try:
                stdscr.addch(row + y_offset, col, ord(' '))
            except curses.error:
                pass
        
        # Draw new bar from bottom up
        height_ratio = bar_heights[col]
        position = col / max(1, width - 1)
        color = get_color_func(height_ratio, position)
        
        for row in range(height):
            if height - row <= cur_height:
                try:
                    stdscr.addch(row + y_offset, col, ord('█'), color)
                except curses.error:
                    pass