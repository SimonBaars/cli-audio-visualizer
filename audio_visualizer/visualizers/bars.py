"""Bars visualizer - classic frequency bars."""

import numpy as np
import curses
from audio_visualizer.dsp.bars import compute_frequency_bars
from audio_visualizer.dsp.adaptive_eq import apply_adaptive_eq


def draw_bars(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int, 
              get_color_func, apply_smoothing_func, state: dict):
    """Draw classic frequency bars."""
    if width <= 0:
        return
    bar_heights = compute_frequency_bars(audio_data, width, sample_rate=44100)
    bar_heights = apply_adaptive_eq(bar_heights, state)
    bar_heights = apply_smoothing_func(bar_heights, False)
    # Light spatial neighbor smoothing: stronger on higher-frequency indices
    if len(bar_heights) > 4:
        original = bar_heights.copy()
        for i in range(1, len(bar_heights)-1):
            frac = i / max(1, len(bar_heights)-1)
            w = 0.15 + 0.35 * (frac ** 1.1)  # up to ~0.5 at high end
            local_avg = (original[i-1] + original[i] + original[i+1]) / 3.0
            bar_heights[i] = (1 - w) * original[i] + w * local_avg
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
        
        simple = state.get('simple_ascii')
        for row in range(height):
            if height - row <= cur_height:
                rel_level = (height - row) / max(1, cur_height)
                color = get_color_func(min(1.0, height_ratio * 0.5 + rel_level * 0.5), position)
                ch = '|' if simple else '█'
                try:
                    stdscr.addch(row + y_offset, col, ord(ch), color)
                except curses.error:
                    pass