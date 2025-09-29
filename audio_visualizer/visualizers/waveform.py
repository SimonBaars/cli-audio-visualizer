"""Waveform visualizer - time-domain oscilloscope."""

import numpy as np
import curses
from .base import clear_area


def draw_waveform(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                  get_color_func, apply_smoothing_func, state: dict):
    """Draw actual time-domain waveform."""
    # Get waveform data
    if len(audio_data) > width:
        step = len(audio_data) // width
        waveform = audio_data[::step][:width]
    else:
        waveform = np.pad(audio_data, (0, width - len(audio_data)), 'constant')
    
    waveform = apply_smoothing_func(waveform, True)
    
    # Normalize
    if np.max(np.abs(waveform)) > 0:
        waveform = waveform / np.max(np.abs(waveform))
    
    middle = height // 2
    
    # Clear entire area first
    clear_area(stdscr, y_offset, height, width)
    
    # Draw waveform as connected dots
    for col in range(min(width, len(waveform))):
        wave_value = waveform[col]
        wave_height = int(wave_value * (middle - 1))
        target_row = middle - wave_height
        
        # Keep in bounds
        target_row = max(0, min(height - 1, target_row))
        
        color = get_color_func(abs(wave_value), 0)
        
        # Draw the waveform point
        try:
            stdscr.addch(target_row + y_offset, col, ord('█'), color)
        except curses.error:
            pass
    
    # Draw center line
    for col in range(width):
        try:
            # Only draw if no waveform point there
            ch = stdscr.inch(middle + y_offset, col)
            if ch == ord(' '):
                stdscr.addch(middle + y_offset, col, ord('─'), curses.color_pair(7) | curses.A_DIM)
        except curses.error:
            pass