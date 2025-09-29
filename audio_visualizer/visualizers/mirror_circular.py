"""Mirror circular visualizer - vertical bars from center."""

import numpy as np
import curses
from .base import compute_frequency_bars


def draw_mirror_circular(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                         get_color_func, apply_smoothing_func, state: dict):
    """Draw mirror circular (vertical bars from center)."""
    num_bars = max(1, width // 2)
    flatten = state.get('flatten', False)
    bar_heights = compute_frequency_bars(audio_data, num_bars, sample_rate=44100, flatten=flatten)
    bar_heights = apply_smoothing_func(bar_heights, False)
    state['last_bar_values'] = bar_heights.copy()
    center = height // 2
    
    for i in range(num_bars):
        bar_height = int(bar_heights[i] * center)
        position = i / max(1, num_bars - 1)
        color = get_color_func(bar_heights[i], position)
        
        # Left half
        col_left = num_bars - i - 1
        # Right half
        col_right = num_bars + i
        
        for col in [col_left, col_right]:
            if col >= width:
                continue
            
            # Clear column
            for row in range(height):
                try:
                    stdscr.addch(row + y_offset, col, ord(' '))
                except curses.error:
                    pass
            
            # Draw from center outward
            for offset in range(bar_height):
                try:
                    stdscr.addch(center - offset + y_offset, col, ord('█'), color)
                    stdscr.addch(center + offset + y_offset, col, ord('█'), color)
                except curses.error:
                    pass