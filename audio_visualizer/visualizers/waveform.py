"""Waveform visualizer - smooth continuous oscilloscope with optional stereo-style dual lines."""

import numpy as np
import curses
from .base import clear_area


def _resample_waveform(audio_data: np.ndarray, target_width: int) -> np.ndarray:
    """Resample audio to target width using linear interpolation for smoother result."""
    n = len(audio_data)
    if n == 0:
        return np.zeros(target_width)
    if n == target_width:
        return audio_data.copy()
    
    # Use linear interpolation instead of simple decimation
    x_old = np.linspace(0, 1, n)
    x_new = np.linspace(0, 1, target_width)
    return np.interp(x_new, x_old, audio_data)


def _bresenham_line(y0: int, y1: int) -> list:
    """Generate all y-coordinates for a vertical line segment."""
    if y0 == y1:
        return [y0]
    step = 1 if y1 > y0 else -1
    return list(range(y0, y1 + step, step))


def draw_waveform(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                  get_color_func, apply_smoothing_func, state: dict):
    """Draw smooth continuous waveform with connected line segments."""
    if width <= 0 or height <= 0:
        return
    
    # Resample using interpolation for smoother result
    waveform = _resample_waveform(audio_data, width)
    
    # Strong temporal smoothing for less jitter
    prev_waveform = state.get('prev_waveform')
    if prev_waveform is None or len(prev_waveform) != len(waveform):
        prev_waveform = waveform.copy()
    smoothing = 0.82
    waveform = smoothing * prev_waveform + (1 - smoothing) * waveform
    state['prev_waveform'] = waveform.copy()
    
    # Normalize to -1..1
    max_val = np.max(np.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val
    
    middle = height // 2
    max_amplitude = middle - 1
    
    # Compute all y-positions first (vectorized)
    y_positions = (middle - (waveform * max_amplitude)).astype(int)
    y_positions = np.clip(y_positions, 0, height - 1)
    
    # Compute intensity based on amplitude
    intensities = np.abs(waveform)
    
    # Clear area
    clear_area(stdscr, y_offset, height, width)
    
    simple = state.get('simple_ascii')
    line_char = ord('|') if simple else ord('│')
    point_char = ord('*') if simple else ord('●')
    
    # Draw waveform with proper line connection
    for col in range(width):
        curr_y = y_positions[col]
        intensity = intensities[col]
        color = get_color_func(min(1.0, intensity * 1.2), col / max(1, width - 1))
        
        if col > 0:
            prev_y = y_positions[col - 1]
            # Draw line from previous point to current
            for y in _bresenham_line(prev_y, curr_y):
                try:
                    stdscr.addch(y + y_offset, col, line_char, color)
                except curses.error:
                    pass
        else:
            # First point
            try:
                stdscr.addch(curr_y + y_offset, col, point_char, color)
            except curses.error:
                pass
    
    # Draw dim center line where waveform isn't present
    center_color = curses.color_pair(7) | curses.A_DIM
    center_char = ord('-') if simple else ord('─')
    for col in range(width):
        try:
            ch = stdscr.inch(middle + y_offset, col) & 0xFF
            if ch == ord(' '):
                stdscr.addch(middle + y_offset, col, center_char, center_color)
        except curses.error:
            pass