"""Waveform visualizer - smooth continuous line oscilloscope."""

import numpy as np
import curses
from .base import clear_area


def draw_waveform(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                  get_color_func, apply_smoothing_func, state: dict):
    """Draw smooth continuous waveform line."""
    # Get waveform data
    if len(audio_data) > width:
        step = len(audio_data) // width
        waveform = audio_data[::step][:width]
    else:
        waveform = np.pad(audio_data, (0, width - len(audio_data)), 'constant')
    
    # Heavy smoothing for less jitter (increased smoothing factor)
    if 'prev_waveform' not in state or len(state['prev_waveform']) != len(waveform):
        state['prev_waveform'] = waveform
    else:
        # Much higher smoothing (0.85 instead of using apply_smoothing_func)
        waveform = 0.85 * state['prev_waveform'] + 0.15 * waveform
        state['prev_waveform'] = waveform
    
    # Normalize
    if np.max(np.abs(waveform)) > 0:
        waveform = waveform / np.max(np.abs(waveform))
    
    middle = height // 2
    
    # Clear entire area first
    clear_area(stdscr, y_offset, height, width)
    
    # Draw continuous waveform by connecting adjacent points
    prev_row = None
    for col in range(min(width, len(waveform))):
        wave_value = waveform[col]
        wave_height = int(wave_value * (middle - 1))
        current_row = middle - wave_height
        
        # Keep in bounds
        current_row = max(0, min(height - 1, current_row))
        
        color = get_color_func(abs(wave_value), 0)
        
        # Draw vertical line from previous point to current point
        if prev_row is not None:
            start_row = min(prev_row, current_row)
            end_row = max(prev_row, current_row)
            
            for row in range(start_row, end_row + 1):
                try:
                    stdscr.addch(row + y_offset, col, ord('│'), color)
                except curses.error:
                    pass
        else:
            # First point
            try:
                stdscr.addch(current_row + y_offset, col, ord('│'), color)
            except curses.error:
                pass
        
        prev_row = current_row
    
    # Draw dim center line
    for col in range(width):
        try:
            ch = stdscr.inch(middle + y_offset, col)
            # Only draw if no waveform there
            if ch == ord(' '):
                stdscr.addch(middle + y_offset, col, ord('─'), curses.color_pair(7) | curses.A_DIM)
        except curses.error:
            pass