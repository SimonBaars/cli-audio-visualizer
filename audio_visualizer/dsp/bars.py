"""DSP utilities for computing frequency bar data from audio samples."""
import numpy as np

DEFAULT_FFT_SIZE = 4096
DEFAULT_SAMPLE_RATE = 44100


def _log_edges(num_bars: int, f_low: float, f_high: float) -> tuple:
    """Compute logarithmically-spaced frequency bin edges.
    
    Returns:
        Tuple of (center frequencies, bin edges)
    """
    centers = np.logspace(np.log10(f_low), np.log10(f_high), num_bars)
    edges = np.zeros(num_bars + 1)
    edges[1:-1] = np.sqrt(centers[:-1] * centers[1:])
    edges[0] = centers[0] * (centers[0] / edges[1]) if edges[1] > 0 else f_low
    edges[-1] = centers[-1] * (centers[-1] / edges[-2]) if edges[-2] > 0 else f_high
    return centers, np.clip(edges, f_low, f_high)


def _adaptive_spatial_smooth(bar_vals: np.ndarray) -> np.ndarray:
    """Apply progressive spatial smoothing - stronger for higher frequencies.
    
    Higher-frequency bars tend to be noisier due to lower absolute energy
    and tilt compensation. This applies a variable-width local mean filter
    that increases toward the treble end.
    """
    n = len(bar_vals)
    if n <= 8:
        return bar_vals
    
    original = bar_vals.copy()
    smoothed = np.copy(bar_vals)
    frac = np.linspace(0, 1, n)
    
    # Precompute blend factors (increases toward high end, up to 65%)
    blend = 0.15 + 0.5 * (frac ** 1.2)
    
    # Apply variable-width smoothing
    for i in range(n):
        half_win = int(1 + frac[i] * 4)  # Window grows from 1 to 5
        if half_win <= 1:
            continue
        lo = max(0, i - half_win)
        hi = min(n, i + half_win + 1)
        local_mean = np.mean(original[lo:hi])
        smoothed[i] = (1 - blend[i]) * original[i] + blend[i] * local_mean
    
    # Re-normalize to maintain 0..1 range
    mx = np.max(smoothed)
    if mx > 0:
        smoothed /= mx
    
    return smoothed


def compute_frequency_bars(audio_data: np.ndarray, num_bars: int, 
                           fft_size: int = DEFAULT_FFT_SIZE,
                           sample_rate: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """Compute normalized frequency bar values from audio samples.
    
    Args:
        audio_data: Raw audio samples (mono)
        num_bars: Number of frequency bars to compute
        fft_size: FFT window size (default 4096)
        sample_rate: Audio sample rate in Hz (default 44100)
    
    Returns:
        Array of bar values normalized to 0..1 range
    """
    if num_bars <= 0:
        return np.array([], dtype=np.float32)
    if fft_size <= 0:
        fft_size = DEFAULT_FFT_SIZE

    # Prepare audio buffer
    if len(audio_data) < fft_size:
        audio = np.pad(audio_data, (0, fft_size - len(audio_data)), 'constant')
    else:
        audio = audio_data[:fft_size]

    # Windowed FFT
    window = np.hanning(len(audio))
    fft = np.fft.rfft(audio * window)
    power = np.abs(fft) ** 2
    freqs = np.fft.rfftfreq(len(audio), 1.0 / sample_rate)

    # Frequency range
    nyquist = sample_rate / 2.0
    f_low, f_high = 20.0, min(20000.0, nyquist * 0.999)
    if f_high <= f_low:
        f_high = nyquist * 0.999

    centers, edges = _log_edges(num_bars, f_low, f_high)
    bar_vals = np.zeros(num_bars, dtype=np.float32)

    # Compute RMS for each frequency band
    for i in range(num_bars):
        lo, hi = edges[i], edges[i + 1]
        mask = (freqs >= lo) & (freqs < hi)
        if np.any(mask):
            bar_vals[i] = np.sqrt(np.mean(power[mask]))
        else:
            # Interpolate for empty bands
            c = centers[i]
            idx = np.searchsorted(freqs, c)
            if idx <= 0:
                val = power[0]
            elif idx >= len(freqs):
                val = power[-1]
            else:
                f1, f2 = freqs[idx - 1], freqs[idx]
                w = (c - f1) / max(1e-9, f2 - f1)
                val = (1 - w) * power[idx - 1] + w * power[idx]
            bar_vals[i] = np.sqrt(val)

    # Post-processing
    if np.any(bar_vals > 0):
        # Noise floor reduction
        floor = np.percentile(bar_vals, 20)
        bar_vals = np.maximum(bar_vals - floor * 0.15, 0)
        
        # High-frequency tilt compensation for perceptual balance
        idx_norm = np.linspace(0, 1, num_bars)
        tilt_gain = 1.0 + 0.78 * (idx_norm ** 1.15)
        bar_vals *= tilt_gain
        
        # Baseline lift
        baseline = np.mean(bar_vals) * 0.01
        if baseline > 0:
            bar_vals += baseline

    # Normalize and apply gamma compression
    max_val = np.max(bar_vals)
    if max_val > 0:
        bar_vals /= max_val
    bar_vals = np.power(bar_vals, 0.7, where=bar_vals > 0, out=bar_vals)

    # Adaptive spatial smoothing for high-frequency stability
    bar_vals = _adaptive_spatial_smooth(bar_vals)
    
    return bar_vals
