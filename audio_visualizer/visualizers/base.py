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

    # Log-spaced bin edges
    log_bins = np.logspace(np.log10(f_low), np.log10(f_high), num_bars + 1)

    bar_vals = np.zeros(num_bars, dtype=np.float32)
    for i in range(num_bars):
        lo = log_bins[i]
        hi = log_bins[i + 1]
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            bar_vals[i] = 0.0
            continue

        band_power = power[mask]
        # RMS of power -> sqrt(mean(power)) approximates energy while taming large bands
        rms = np.sqrt(np.mean(band_power))
        bar_vals[i] = rms

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