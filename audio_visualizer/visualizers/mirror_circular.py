"""Mirror circular visualizer - symmetric vertical bars expanding from center."""

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


def draw_mirror_circular(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                         get_color_func, apply_smoothing_func, state: dict):
    """Draw symmetric vertical bars expanding from center with gradient coloring."""
    num_bars = max(1, width // 2)
    
    bar_heights = compute_frequency_bars(audio_data, num_bars, sample_rate=44100)
    bar_heights = _apply_adaptive_eq(bar_heights, state)
    bar_heights = apply_smoothing_func(bar_heights, False)
    state['last_bar_values'] = bar_heights.copy()
    
    center = height // 2
    simple = state.get('simple_ascii')
    bar_char = ord('|') if simple else ord('█')
    cap_char = ord('-') if simple else ord('─')
    
    # Precompute bar pixel heights
    bar_pixel_heights = (bar_heights * center).astype(int)
    
    for i in range(num_bars):
        bar_h = bar_pixel_heights[i]
        h_ratio = bar_heights[i]
        position = i / max(1, num_bars - 1)
        
        # Mirror columns: left and right of center
        col_left = num_bars - i - 1
        col_right = num_bars + i
        
        for col in (col_left, col_right):
            if col >= width:
                continue
            
            # Clear and draw in one pass
            for row in range(height):
                y = row + y_offset
                dist_from_center = abs(row - center)
                
                if dist_from_center < bar_h:
                    # Inside bar: gradient color based on distance from center
                    rel_level = 1.0 - (dist_from_center / max(1, bar_h))
                    intensity = min(1.0, h_ratio * 0.6 + rel_level * 0.4)
                    color = get_color_func(intensity, position)
                    try:
                        stdscr.addch(y, col, bar_char, color)
                    except curses.error:
                        pass
                elif dist_from_center == bar_h and bar_h > 0:
                    # Bar cap at the edge
                    color = get_color_func(h_ratio, position)
                    try:
                        stdscr.addch(y, col, cap_char, color)
                    except curses.error:
                        pass
                else:
                    try:
                        stdscr.addch(y, col, ord(' '))
                    except curses.error:
                        pass