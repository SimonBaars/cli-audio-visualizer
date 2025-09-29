"""Simple ASCII bars visualizer.

Provides an alternative to the full block glyph bars for terminals/fonts
where color doesn't appear correctly on the heavy block character. Uses a
stack of simple ASCII characters to represent intensity with per-cell color.
"""

from typing import Dict
import numpy as np
import curses
from audio_visualizer.dsp.bars import compute_frequency_bars


# A coarse vertical fill using only safe ASCII characters.
# Index 0 = lowest (at top of bar), last = strongest (near bottom)
ASCII_GRADIENT = ['|']  # Single glyph for now; easy to extend later if desired


def draw_bars_simple(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                     get_color_func, apply_smoothing_func, state: Dict):
    if width <= 0 or height <= 0:
        return

    flatten = state.get('flatten', False)
    bar_values = compute_frequency_bars(audio_data, width, sample_rate=44100, flatten=flatten)

    # Optional adaptive EQ (same logic as other bar modes)
    if state.get('adaptive_eq'):
        run_mean = state.get('adaptive_eq_mean')
        if run_mean is None or len(run_mean) != len(bar_values):
            run_mean = np.copy(bar_values)
        else:
            run_mean = 0.995 * run_mean + 0.005 * bar_values
        eq_strength = state.get('adaptive_eq_strength', 0.65)
        adj = bar_values / (run_mean + 1e-6)
        if np.max(adj) > 0:
            adj /= np.max(adj)
        bar_values = (1 - eq_strength) * bar_values + eq_strength * adj
        state['adaptive_eq_mean'] = run_mean

    bar_values = apply_smoothing_func(bar_values, False)
    state['last_bar_values'] = bar_values.copy()

    int_heights = (bar_values * height).astype(int)

    # Clear area (only columns we use for perf)
    for col in range(min(width, len(int_heights))):
        for row in range(height):
            try:
                stdscr.addch(row + y_offset, col, ord(' '))
            except curses.error:
                pass

    # Draw bars using a simple ASCII glyph; each cell colored independently
    for col in range(min(width, len(int_heights))):
        bar_h = int_heights[col]
        if bar_h <= 0:
            continue
        level_base = bar_values[col]
        pos = col / max(1, width - 1)

        for step in range(bar_h):
            # Bottom is step 0
            rel = (step + 1) / max(1, bar_h)  # 0..1 upward
            # Mix base level and relative position inside bar for color variance
            color_level = min(1.0, level_base * 0.5 + rel * 0.5)
            color = get_color_func(color_level, pos)
            # If global ascii flag off, allow fallback to block (user toggled away)
            if not state.get('simple_ascii'):
                glyph = '█'
            else:
                glyph = ASCII_GRADIENT[-1]
            row = height - 1 - step
            try:
                stdscr.addch(row + y_offset, col, ord(glyph), color)
            except curses.error:
                pass
