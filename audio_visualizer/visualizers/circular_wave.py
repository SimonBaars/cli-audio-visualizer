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
    num_samples = 60  # Sample points for waveform data
    if len(audio_data) > num_samples:
        step = len(audio_data) // num_samples
        waveform = audio_data[::step][:num_samples]
    else:
        waveform = np.pad(audio_data, (0, num_samples - len(audio_data)), 'constant')
    
    waveform = apply_smoothing_func(waveform, True)
    if np.max(np.abs(waveform)) > 0:
        waveform = waveform / np.max(np.abs(waveform))
    
    center_y = height // 2
    center_x = width // 2
    base_radius = min(height // 2 - 2, width // 4)
    
    # Calculate perimeter to determine how many points we need
    perimeter = int(2 * np.pi * base_radius * 1.5)  # Overestimate for good coverage
    num_draw_points = max(perimeter, 200)  # At least 200 points for smooth circle
    
    # Draw full circle with line segments between points
    prev_x, prev_y = None, None
    
    for i in range(num_draw_points + 1):  # +1 to close the circle
        angle = (i / num_draw_points) * 2 * np.pi
        
        # Sample waveform (interpolate between samples)
        waveform_idx = int((i / num_draw_points) * num_samples) % num_samples
        wave_offset = waveform[waveform_idx] * base_radius * 0.4
        radius = base_radius + wave_offset
        
        # Calculate position
        x = int(center_x + radius * np.cos(angle))
        y = int(center_y + radius * np.sin(angle) * 0.5)  # Aspect ratio correction
        
        # Get color
        position = i / max(1, num_draw_points - 1)
        intensity = abs(wave_offset / base_radius) if base_radius > 0 else 0
        color = get_color_func(intensity, position)
        
        # Draw current point
        if 0 <= x < width and 0 <= y < height:
            try:
                stdscr.addch(y + y_offset, x, ord('█'), color)
            except curses.error:
                pass
        
        # Draw line from previous point to current (fill gaps)
        if prev_x is not None and prev_y is not None:
            # Simple line drawing - interpolate between points
            dx = x - prev_x
            dy = y - prev_y
            steps = max(abs(dx), abs(dy))
            
            if steps > 0:
                for step in range(steps + 1):
                    t = step / steps
                    interp_x = int(prev_x + t * dx)
                    interp_y = int(prev_y + t * dy)
                    
                    if 0 <= interp_x < width and 0 <= interp_y < height:
                        try:
                            stdscr.addch(interp_y + y_offset, interp_x, ord('█'), color)
                        except curses.error:
                            pass
        
        prev_x, prev_y = x, y