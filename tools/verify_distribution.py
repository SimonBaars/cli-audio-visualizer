"""Utility to verify frequency bar distribution uniformity.

Run this to print average normalized energy per bar index across random pink-noise
and white-noise samples, highlighting skew where early bars are systematically lower.
"""
import numpy as np
from audio_visualizer.visualizers.base import compute_frequency_bars


def generate_noise(kind: str, n: int, sample_rate: int = 44100):
    if kind == 'white':
        return np.random.randn(n).astype(np.float32) * 0.2
    if kind == 'pink':
        # Simple 1/f pink noise approximation via frequency weighting
        # Generate white, FFT, scale by 1/sqrt(f), iFFT
        N = n
        white = np.random.randn(N)
        fft = np.fft.rfft(white)
        freqs = np.fft.rfftfreq(N, 1/sample_rate)
        scale = np.ones_like(freqs)
        scale[1:] /= np.sqrt(freqs[1:])
        pink_fft = fft * scale
        pink = np.fft.irfft(pink_fft, n=N)
        pink /= np.max(np.abs(pink)) + 1e-9
        return pink.astype(np.float32) * 0.3
    raise ValueError(kind)


def accumulate(kind: str, iterations: int = 100, fft_size: int = 4096, bars: int = 120):
    sums = np.zeros(bars, dtype=np.float64)
    for _ in range(iterations):
        noise = generate_noise(kind, fft_size)
        vals = compute_frequency_bars(noise, bars, fft_size=fft_size)
        sums += vals
    return sums / iterations


def main():
    for kind in ('white', 'pink'):
        avg = accumulate(kind)
        left_mean = float(np.mean(avg[:10]))
        right_mean = float(np.mean(avg[-10:]))
        ratio = (right_mean + 1e-9) / (left_mean + 1e-9)
        print(f"{kind.upper()} NOISE  bars={len(avg)}  left_mean={left_mean:.3f} right_mean={right_mean:.3f} ratio(right/left)={ratio:.2f}")
        print("First 20 bars:", ' '.join(f"{v:.2f}" for v in avg[:20]))
        print("Last 20 bars: ", ' '.join(f"{v:.2f}" for v in avg[-20:]))
        print()

if __name__ == '__main__':
    main()
