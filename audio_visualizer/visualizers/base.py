"""Base utilities for visualizers."""

import numpy as np


def clear_area(stdscr, y_start: int, height: int, width: int):
    """Clear a rectangular area."""
    import curses
    for row in range(height):
        try:
            stdscr.move(y_start + row, 0)
            stdscr.clrtoeol()
        except curses.error:
            pass


def verify_bar_distribution(bar_values: np.ndarray) -> dict:
    """Return simple metrics to assess left/right balance of bar array.

    Metrics:
      left_mean, right_mean: mean of first/last 10% (at least 5 bars)
      ratio: right_mean / left_mean
      zeros_left / zeros_right: count of zero (or near-zero) bars in each segment
    """
    if bar_values is None or len(bar_values) == 0:
        return {}
    n = len(bar_values)
    seg = max(5, n // 10)
    left = bar_values[:seg]
    right = bar_values[-seg:]
    eps = 1e-6
    metrics = {
        'count': n,
        'left_mean': float(np.mean(left)),
        'right_mean': float(np.mean(right)),
        'ratio_right_over_left': float((np.mean(right)+eps)/(np.mean(left)+eps)),
        'zeros_left': int(np.sum(left < eps)),
        'zeros_right': int(np.sum(right < eps)),
    }
    return metrics