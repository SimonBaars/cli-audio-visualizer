"""Snapshot utility to capture bar distributions for each visualizer mode.

Usage:
  python -m tools.snapshot <wav_or_raw_optionally>

If no file is provided, generates synthetic mixes (white + pink + random tonal peaks)
then computes frequency bars like each visualizer would.

Outputs JSON with per-mode metrics and first/last segment averages.
"""
import json
import sys
import numpy as np
from audio_visualizer.visualizers.base import compute_frequency_bars, verify_bar_distribution

SAMPLE_RATE = 44100
FFT_SIZE = 4096


def synthetic_audio(n=FFT_SIZE):
    white = np.random.randn(n)
    # Pink approximation
    fft = np.fft.rfft(np.random.randn(n))
    freqs = np.fft.rfftfreq(n, 1/SAMPLE_RATE)
    scale = np.ones_like(freqs)
    scale[1:] /= np.sqrt(freqs[1:])
    pink = np.fft.irfft(fft*scale, n=n)
    # Add a couple of tonal peaks
    t = np.arange(n) / SAMPLE_RATE
    tone = 0.6*np.sin(2*np.pi*440*t) + 0.3*np.sin(2*np.pi*3000*t)
    mix = 0.5*white + 0.7*pink + tone
    mix /= np.max(np.abs(mix)) + 1e-9
    return mix.astype(np.float32)


def compute_all(audio, width=160, height=60):
    modes = {
        'bars': width,
        'spectrum': width//2,
        'mirror_circular': width//2,
    }
    results = {}
    for mode, bars in modes.items():
        vals = compute_frequency_bars(audio, bars, fft_size=FFT_SIZE, sample_rate=SAMPLE_RATE)
        metrics = verify_bar_distribution(vals)
        results[mode] = {
            'bars': bars,
            'metrics': metrics,
            'values_first20': [float(x) for x in vals[:20]],
            'values_last20': [float(x) for x in vals[-20:]],
        }
    return results


def main():
    audio = synthetic_audio()
    data = compute_all(audio)
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    main()
