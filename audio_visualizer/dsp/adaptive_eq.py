"""Adaptive EQ helper utilities to normalize bar/band energy distribution.

The previous implementation duplicated running mean logic across multiple
visualizers. This module centralizes that behavior so each visualizer
can simply call apply_adaptive_eq(values, state) and receive adjusted
values along with state updates.
"""
from __future__ import annotations
import numpy as np
from typing import Dict

def apply_adaptive_eq(values: np.ndarray, state: Dict, key_prefix: str = "") -> np.ndarray:
    """Apply running-mean based adaptive EQ if enabled in state.

    Parameters:
      values: 1-D numpy array of current magnitudes (0..1 expected)
      state:  dict carrying 'adaptive_eq', 'adaptive_eq_strength', etc.
      key_prefix: optional prefix to allow multiple independent EQ contexts
                  within a single visualizer (e.g., "energy_", "bars_").

    Returns:
      Possibly adjusted array (same object is not modified in-place).
    """
    if not state.get('adaptive_eq') or values.size == 0:
        return values
    strength = float(state.get('adaptive_eq_strength', 0.4))
    run_key = f"{key_prefix}adaptive_eq_mean"
    run_mean = state.get(run_key)
    if run_mean is None or not isinstance(run_mean, np.ndarray) or run_mean.shape != values.shape:
        run_mean = values.copy()
    else:
        # Exponential moving average; small alpha for long residency
        run_mean = 0.995 * run_mean + 0.005 * values
    adj = values / (run_mean + 1e-6)
    m = np.max(adj)
    if m > 0:
        adj = adj / m
    blended = (1 - strength) * values + strength * adj
    state[run_key] = run_mean
    return blended
