"""Base utilities for visualizers."""

import numpy as np


def compute_frequency_bars(audio_data: np.ndarray, num_bars: int, fft_size: int = 4096, sample_rate: int = 44100):
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

    # Interpolate in log-frequency domain to avoid empty early bins.
    if num_bars <= 0:
        return np.array([])
    log_centers = np.logspace(np.log10(f_low), np.log10(f_high), num_bars)

    # Work with magnitude for smoother interpolation, then square back to pseudo-power
    mag = np.sqrt(power)
    log_freqs = np.log10(np.clip(freqs, f_low, f_high))
    log_centers_log = np.log10(log_centers)

    # Ensure strictly increasing for interp (guard against any pathological duplicates)
    unique_mask = np.concatenate([[True], np.diff(log_freqs) > 0])
    log_freqs_u = log_freqs[unique_mask]
    mag_u = mag[unique_mask]

    interp_mag = np.interp(log_centers_log, log_freqs_u, mag_u)

    # Mild smoothing to emulate bandwidth around each center (triangular kernel)
    if num_bars > 4:
        kernel = np.array([0.25, 0.5, 0.25], dtype=np.float32)
        padded = np.pad(interp_mag, (1,1), mode='edge')
        smoothed = kernel[0]*padded[:-2] + kernel[1]*padded[1:-1] + kernel[2]*padded[2:]
    else:
        smoothed = interp_mag

    bar_vals = (smoothed.astype(np.float32)) ** 2

    # Remove noise floor (median-based) to prevent constant low plateau on right side
    if np.any(bar_vals > 0):
        median_floor = np.median(bar_vals)
        bar_vals = np.clip(bar_vals - median_floor * 0.6, 0, None)

    # Min-max normalize
    max_val = np.max(bar_vals)
    if max_val > 0:
        bar_vals = bar_vals / max_val

    # Gentle gamma to elevate lower bars without crushing peaks
    bar_vals = np.power(bar_vals, 0.6, where=bar_vals>0, out=bar_vals)

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