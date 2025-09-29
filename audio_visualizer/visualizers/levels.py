"""Levels visualizer - large block VU meters for key frequency ranges."""

import numpy as np
import curses
from .base import clear_area


def draw_levels(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                get_color_func, apply_smoothing_func, state: dict):
    """Draw large block-style VU meters for bass, mid, treble."""
    # Process FFT for specific frequency ranges
    fft_size = 4096
    if len(audio_data) < fft_size:
        audio_data = np.pad(audio_data, (0, fft_size - len(audio_data)), 'constant')
    
    fft = np.fft.rfft(audio_data[:fft_size])
    magnitude = np.abs(fft)
    freqs = np.fft.rfftfreq(fft_size, 1.0 / 44100)
    
    # Define 3 main frequency ranges
    ranges = [
        ("BASS", 20, 250),      # Sub-bass and bass
        ("MID", 250, 2000),     # Mids and presence
        ("TREBLE", 2000, 20000) # Highs
    ]
    
    levels = []
    for name, low, high in ranges:
        mask = (freqs >= low) & (freqs < high)
        if np.any(mask):
            level = np.mean(magnitude[mask])
        else:
            level = 0
        levels.append((name, level))
    
    # Normalize
    max_level = max(l[1] for l in levels) if levels else 1
    if max_level > 0:
        levels = [(name, level / max_level) for name, level in levels]
    
    # Apply smoothing
    if 'prev_levels' not in state:
        state['prev_levels'] = [l[1] for l in levels]
    else:
        smoothed = []
        for i, (name, level) in enumerate(levels):
            smoothed_val = 0.7 * state['prev_levels'][i] + 0.3 * level
            smoothed.append((name, smoothed_val))
        levels = smoothed
        state['prev_levels'] = [l[1] for l in levels]
    
    # Clear entire area
    clear_area(stdscr, y_offset, height, width)
    
    # Calculate layout - 3 large blocks
    block_height = height // 3
    
    for idx, (name, level) in enumerate(levels):
        block_y = idx * block_height + y_offset
        
        # Draw label
        label = f" {name} "
        try:
            stdscr.addstr(block_y, 2, label, curses.color_pair(7) | curses.A_BOLD)
        except curses.error:
            pass
        
        # Draw horizontal bar
        bar_y = block_y + block_height // 2
        bar_width = width - 4
        bar_length = int(level * bar_width)
        
        # Determine color based on level
        position = idx / max(1, len(levels) - 1)
        
        # Draw filled portion with blocks
        for x in range(bar_length):
            x_pos = 2 + x
            # Calculate level for this position
            local_level = (x + 1) / bar_width
            color = get_color_func(local_level, position)
            
            try:
                # Use solid blocks
                stdscr.addch(bar_y, x_pos, ord('█'), color)
                # Draw above and below for thickness
                if block_height > 3:
                    stdscr.addch(bar_y - 1, x_pos, ord('█'), color)
                    stdscr.addch(bar_y + 1, x_pos, ord('█'), color)
            except curses.error:
                pass
        
        # Draw empty portion
        for x in range(bar_length, bar_width):
            x_pos = 2 + x
            try:
                stdscr.addch(bar_y, x_pos, ord('─'), curses.color_pair(7) | curses.A_DIM)
                if block_height > 3:
                    stdscr.addch(bar_y - 1, x_pos, ord('─'), curses.color_pair(7) | curses.A_DIM)
                    stdscr.addch(bar_y + 1, x_pos, ord('─'), curses.color_pair(7) | curses.A_DIM)
            except curses.error:
                pass
        
        # Draw percentage
        percentage = int(level * 100)
        pct_str = f"{percentage}%"
        try:
            stdscr.addstr(bar_y, width - 6, pct_str, curses.color_pair(7))
        except curses.error:
            pass