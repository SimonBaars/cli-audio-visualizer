"""Base utilities shared across visualizers."""

import curses
import numpy as np
from typing import Dict, Optional


def clear_area(stdscr, y_start: int, height: int, width: int) -> None:
    """Clear a rectangular area of the screen.
    
    Uses clrtoeol() for efficiency - clears from cursor to end of line.
    
    Args:
        stdscr: Curses window object
        y_start: Starting row (0-indexed from top of visualization area)
        height: Number of rows to clear
        width: Not used (clrtoeol clears to end of line)
    """
    for row in range(height):
        try:
            stdscr.move(y_start + row, 0)
            stdscr.clrtoeol()
        except curses.error:
            pass


def clear_rect(stdscr, y_start: int, x_start: int, height: int, width: int) -> None:
    """Clear a specific rectangular region with spaces.
    
    Unlike clear_area(), this respects the width parameter and only
    clears the specified rectangle.
    
    Args:
        stdscr: Curses window object
        y_start: Starting row
        x_start: Starting column
        height: Number of rows to clear
        width: Number of columns to clear
    """
    for row in range(height):
        y = y_start + row
        for col in range(width):
            try:
                stdscr.addch(y, x_start + col, ord(' '))
            except curses.error:
                pass


def verify_bar_distribution(bar_values: Optional[np.ndarray]) -> Dict:
    """Compute metrics to assess frequency distribution balance.
    
    Useful for debugging and tuning the DSP pipeline to ensure
    balanced energy across the spectrum.
    
    Args:
        bar_values: Array of bar height values (0..1 normalized)
    
    Returns:
        Dictionary with distribution metrics:
        - count: Total number of bars
        - left_mean: Mean of lowest 10% of frequencies
        - right_mean: Mean of highest 10% of frequencies  
        - ratio_right_over_left: Balance ratio (1.0 = balanced)
        - zeros_left/zeros_right: Count of near-zero bars in each segment
    """
    if bar_values is None or len(bar_values) == 0:
        return {}
    
    n = len(bar_values)
    seg = max(5, n // 10)
    left = bar_values[:seg]
    right = bar_values[-seg:]
    eps = 1e-6
    
    return {
        'count': n,
        'left_mean': float(np.mean(left)),
        'right_mean': float(np.mean(right)),
        'ratio_right_over_left': float((np.mean(right) + eps) / (np.mean(left) + eps)),
        'zeros_left': int(np.sum(left < eps)),
        'zeros_right': int(np.sum(right < eps)),
    }