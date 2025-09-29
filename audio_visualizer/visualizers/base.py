"""Base utilities for visualizers."""

import numpy as np


def compute_frequency_bars(audio_data: np.ndarray, num_bars: int, fft_size: int = 4096, sample_rate: int = 44100, flatten: bool = False):
    """Compute frequency bars with perceptually-better distribution.

    Improvements over previous implementation:
    - Apply Hann window to reduce spectral leakage (which biased highs)
    - Use RMS power per logarithmic band (sqrt(mean(power))) instead of mean magnitude
    - Perform min-max normalization (remove noise floor) before gamma adjustment
    - Slight gamma (0.6) to lift quieter bands without flattening dynamics
    """
    if fft_size <= 0:
        fft_size = 4096

    # Pad / truncate
    if len(audio_data) < fft_size:
        audio = np.pad(audio_data, (0, fft_size - len(audio_data)), 'constant')
    else:
        audio = audio_data[:fft_size]

    # Hann window reduces leakage that inflated high-frequency noise floor
    window = np.hanning(len(audio))
    windowed = audio * window

    # FFT & power spectrum
    fft = np.fft.rfft(windowed)
    power = (np.abs(fft) ** 2)
    freqs = np.fft.rfftfreq(len(windowed), 1.0 / sample_rate)

    # Avoid log(0) issues by constraining lower bound and upper bound to Nyquist
    nyquist = sample_rate / 2.0
    f_low, f_high = 20.0, min(20000.0, nyquist * 0.999)
    if f_high <= f_low:
        f_high = nyquist * 0.999

    # Construct logarithmic band edges using geometric midpoints
    if num_bars <= 0:
        return np.array([])
    centers = np.logspace(np.log10(f_low), np.log10(f_high), num_bars)
    # Derive edges: geometric mean between adjacent centers; extend ends
    edges = np.zeros(num_bars + 1)
    edges[1:-1] = np.sqrt(centers[:-1] * centers[1:])
    # Extrapolate first/last edges
    edges[0] = centers[0] * (centers[0] / edges[1]) if edges[1] > 0 else f_low
    edges[-1] = centers[-1] * (centers[-1] / edges[-2]) if edges[-2] > 0 else f_high
    # Clamp edges
    edges = np.clip(edges, f_low, f_high)

    bar_vals = np.zeros(num_bars, dtype=np.float32)
    for i in range(num_bars):
        lo, hi = edges[i], edges[i+1]
        mask = (freqs >= lo) & (freqs < hi)
        if np.any(mask):
            # Integrate power in band (mean to normalize for varying bin counts)
            band_power = power[mask]
            bar_vals[i] = float(np.sqrt(np.mean(band_power)))
        else:
            # Fallback: interpolate magnitude at center
            c = centers[i]
            # Find closest bin indices
            idx = np.searchsorted(freqs, c)
            if idx <= 0:
                val = power[0]
            elif idx >= len(freqs):
                val = power[-1]
            else:
                f1, f2 = freqs[idx-1], freqs[idx]
                w = (c - f1) / max(1e-9, (f2 - f1))
                val = (1-w)*power[idx-1] + w*power[idx]
            bar_vals[i] = float(np.sqrt(val))

    if np.any(bar_vals > 0):
        # Light noise floor removal based on lower percentile (less aggressive than median)
        floor = np.percentile(bar_vals, 20)
        bar_vals = np.clip(bar_vals - floor * 0.15, 0, None)

        # Spectral tilt compensation (moderate) unless flatten requested
        if not flatten:
            idx = np.linspace(0, 1, num_bars)
            # Up to +5 dB (~1.78x) at extreme right
            tilt_gain = 1.0 + 0.78 * (idx ** 1.15)
            bar_vals *= tilt_gain

        # Minimal baseline proportional to global mean to avoid empty tail
        baseline = np.mean(bar_vals) * 0.01
        if baseline > 0:
            bar_vals += baseline

    # Min-max normalize & gamma
    max_val = np.max(bar_vals)
    if max_val > 0:
        bar_vals = bar_vals / max_val
    # Slightly less aggressive gamma to preserve dynamic highs
    bar_vals = np.power(bar_vals, 0.7, where=bar_vals>0, out=bar_vals)

    return bar_vals


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