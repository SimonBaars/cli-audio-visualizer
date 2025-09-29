"""Circular wave visualizer - circle with waveform modulation."""

import numpy as np
import curses
from .base import clear_area


def draw_circular_wave(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                       get_color_func, apply_smoothing_func, state: dict):
    """Draw actual circle with waveform modulation."""
    # Clear area every frame
    clear_area(stdscr, y_offset, height, width)
    
    # Get waveform
    num_points = 120  # Number of points around the circle
    if len(audio_data) > num_points:
        step = len(audio_data) // num_points
        waveform = audio_data[::step][:num_points]
    else:
        waveform = np.pad(audio_data, (0, num_points - len(audio_data)), 'constant')
    
    waveform = apply_smoothing_func(waveform, True)
    if np.max(np.abs(waveform)) > 0:
        waveform = waveform / np.max(np.abs(waveform))
    
    center_y = height // 2
    center_x = width // 2
    base_radius = min(height // 2 - 2, width // 4)
    
    # Draw full circle (0 to 2π)
    for i in range(num_points):
        angle = (i / num_points) * 2 * np.pi
        
        # Modulate radius by waveform
        wave_offset = waveform[i] * base_radius * 0.4
        radius = base_radius + wave_offset
        
        # Calculate position
        x = int(center_x + radius * np.cos(angle))
        y = int(center_y + radius * np.sin(angle) * 0.5)  # Aspect ratio correction
        
        # Get color
        position = i / max(1, num_points - 1)
        intensity = abs(wave_offset / base_radius) if base_radius > 0 else 0
        color = get_color_func(intensity, position)
        
        # Draw point
        if 0 <= x < width and 0 <= y < height:
            try:
                stdscr.addch(y + y_offset, x, ord('●'), color)
            except curses.error:
                pass