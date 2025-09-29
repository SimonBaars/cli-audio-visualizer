"""Base utilities for visualizers."""

import numpy as np


def compute_frequency_bars(audio_data: np.ndarray, num_bars: int, fft_size: int = 4096):
    """Compute frequency bars with logarithmic spacing."""
    if len(audio_data) < fft_size:
        audio_data = np.pad(audio_data, (0, fft_size - len(audio_data)), 'constant')
    
    fft = np.fft.rfft(audio_data[:fft_size])
    magnitude = np.abs(fft)
    freqs = np.fft.rfftfreq(fft_size, 1.0 / 44100)
    
    # Logarithmic bins
    log_bins = np.logspace(np.log10(20), np.log10(20000), num_bars + 1)
    
    bar_heights = []
    for i in range(num_bars):
        freq_mask = (freqs >= log_bins[i]) & (freqs < log_bins[i + 1])
        if np.any(freq_mask):
            bar_heights.append(np.max(magnitude[freq_mask]))
        else:
            bar_heights.append(0)
    
    bar_heights = np.array(bar_heights)
    if np.max(bar_heights) > 0:
        bar_heights = bar_heights / np.max(bar_heights)
        bar_heights = np.power(bar_heights, 0.7)
    
    return bar_heights


def clear_area(stdscr, y_start: int, height: int, width: int):
    """Clear a rectangular area."""
    import curses
    for row in range(height):
        try:
            stdscr.move(y_start + row, 0)
            stdscr.clrtoeol()
        except curses.error:
            pass