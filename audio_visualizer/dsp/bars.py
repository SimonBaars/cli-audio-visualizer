"""DSP utilities for computing frequency bar data."""
import numpy as np

DEFAULT_FFT_SIZE = 4096
DEFAULT_SAMPLE_RATE = 44100


def _log_edges(num_bars: int, f_low: float, f_high: float):
    centers = np.logspace(np.log10(f_low), np.log10(f_high), num_bars)
    edges = np.zeros(num_bars + 1)
    edges[1:-1] = np.sqrt(centers[:-1] * centers[1:])
    edges[0] = centers[0] * (centers[0] / edges[1]) if edges[1] > 0 else f_low
    edges[-1] = centers[-1] * (centers[-1] / edges[-2]) if edges[-2] > 0 else f_high
    return centers, np.clip(edges, f_low, f_high)


def compute_frequency_bars(audio_data: np.ndarray, num_bars: int, fft_size: int = DEFAULT_FFT_SIZE,
                           sample_rate: int = DEFAULT_SAMPLE_RATE, flatten: bool = False) -> np.ndarray:
    if num_bars <= 0:
        return np.array([])
    if fft_size <= 0:
        fft_size = DEFAULT_FFT_SIZE

    if len(audio_data) < fft_size:
        audio = np.pad(audio_data, (0, fft_size - len(audio_data)), 'constant')
    else:
        audio = audio_data[:fft_size]

    window = np.hanning(len(audio))
    windowed = audio * window
    fft = np.fft.rfft(windowed)
    power = np.abs(fft) ** 2
    freqs = np.fft.rfftfreq(len(windowed), 1.0 / sample_rate)

    nyquist = sample_rate / 2.0
    f_low, f_high = 20.0, min(20000.0, nyquist * 0.999)
    if f_high <= f_low:
        f_high = nyquist * 0.999

    centers, edges = _log_edges(num_bars, f_low, f_high)
    bar_vals = np.zeros(num_bars, dtype=np.float32)

    for i in range(num_bars):
        lo, hi = edges[i], edges[i+1]
        mask = (freqs >= lo) & (freqs < hi)
        if np.any(mask):
            band_power = power[mask]
            bar_vals[i] = float(np.sqrt(np.mean(band_power)))
        else:
            c = centers[i]
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
        floor = np.percentile(bar_vals, 20)
        bar_vals = np.clip(bar_vals - floor * 0.15, 0, None)
        if not flatten:
            idx = np.linspace(0, 1, num_bars)
            tilt_gain = 1.0 + 0.78 * (idx ** 1.15)
            bar_vals *= tilt_gain
        baseline = np.mean(bar_vals) * 0.01
        if baseline > 0:
            bar_vals += baseline

    max_val = np.max(bar_vals)
    if max_val > 0:
        bar_vals = bar_vals / max_val
    bar_vals = np.power(bar_vals, 0.7, where=bar_vals>0, out=bar_vals)
    return bar_vals
