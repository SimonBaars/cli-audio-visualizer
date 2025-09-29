"""Mirror circular visualizer - vertical bars from center."""

import numpy as np
import curses
from audio_visualizer.dsp.bars import compute_frequency_bars
from audio_visualizer.dsp.adaptive_eq import apply_adaptive_eq


def draw_mirror_circular(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                         get_color_func, apply_smoothing_func, state: dict):
    """Draw mirror circular (vertical bars from center)."""
    num_bars = max(1, width // 2)
    bar_heights = compute_frequency_bars(audio_data, num_bars, sample_rate=44100)
    bar_heights = apply_adaptive_eq(bar_heights, state)
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
            simple = state.get('simple_ascii')
            ch = '|' if simple else '█'
            for offset in range(bar_height):
                try:
                    stdscr.addch(center - offset + y_offset, col, ord(ch), color)
                    stdscr.addch(center + offset + y_offset, col, ord(ch), color)
                except curses.error:
                    pass