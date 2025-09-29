"""Bars visualizer - classic frequency bars."""

import numpy as np
import curses
from audio_visualizer.dsp.bars import compute_frequency_bars


def draw_bars(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int, 
              get_color_func, apply_smoothing_func, state: dict):
    """Draw classic frequency bars."""
    if width <= 0:
        return
    flatten = state.get('flatten', False)
    bar_heights = compute_frequency_bars(audio_data, width, sample_rate=44100, flatten=flatten)
    # Adaptive EQ (slow running mean to balance distribution over time)
    if state.get('adaptive_eq'):
        run_mean = state.get('adaptive_eq_mean')
        if run_mean is None or len(run_mean) != len(bar_heights):
            run_mean = np.copy(bar_heights)
        else:
            run_mean = 0.995 * run_mean + 0.005 * bar_heights
        eq_strength = state.get('adaptive_eq_strength', 0.65)  # blend instead of full replace
        adj = bar_heights / (run_mean + 1e-6)
        if np.max(adj) > 0:
            adj /= np.max(adj)
        bar_heights = (1 - eq_strength) * bar_heights + eq_strength * adj
        state['adaptive_eq_mean'] = run_mean
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