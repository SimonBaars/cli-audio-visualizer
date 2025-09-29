#!/usr/bin/env python3
"""Manual test of each visualizer without curses - shows what they produce."""

import sys
import time
import numpy as np
from audio_visualizer.parec_audio import ParecAudioCapture
from audio_visualizer.visualizers import base


def get_test_audio():
    """Get real audio data."""
    audio = ParecAudioCapture(chunk_size=1024)
    audio.start()
    time.sleep(1)
    
    try:
        audio_data = audio.audio_queue.get(timeout=1)
    except:
        audio_data = None
    
    audio.stop()
    return audio_data


def test_bars_manual(audio_data, width=80, height=20):
    """Test BARS visualization."""
    print("\n" + "="*80)
    print("MODE 1: BARS")
    print("="*80)
    
    bar_heights = base.compute_frequency_bars(audio_data, width, fft_size=4096)
    current_bars = (bar_heights * height).astype(int)
    
    # Build visual
    for row in range(height):
        line = ""
        for col in range(width):
            cur_height = current_bars[col]
            height_ratio = bar_heights[col]
            
            if height - row <= cur_height:
                # Determine color
                if height_ratio < 0.4:
                    color = "\033[32m"  # Green
                elif height_ratio < 0.7:
                    color = "\033[33m"  # Yellow
                else:
                    color = "\033[31m"  # Red
                line += color + "█" + "\033[0m"
            else:
                line += " "
        print(line)
    
    print(f"\nStats: max={np.max(bar_heights):.3f}, mean={np.mean(bar_heights):.3f}")
    print(f"Active bars: {np.sum(bar_heights > 0.01)}/{width}")


def test_spectrum_manual(audio_data, width=80, height=20):
    """Test SPECTRUM visualization."""
    print("\n" + "="*80)
    print("MODE 2: SPECTRUM")
    print("="*80)
    
    bar_heights = base.compute_frequency_bars(audio_data, width, fft_size=4096)
    
    # Simulate peak tracking
    peak_values = bar_heights.copy()
    
    # Build visual
    for row in range(height):
        line = ""
        for col in range(width):
            height_ratio = bar_heights[col]
            bar_height = int(height_ratio * height)
            peak_height = int(peak_values[col] * height)
            
            if height - row <= bar_height:
                if height_ratio < 0.4:
                    color = "\033[32m"
                elif height_ratio < 0.7:
                    color = "\033[33m"
                else:
                    color = "\033[31m"
                line += color + "▆" + "\033[0m"
            elif height - row == peak_height and peak_height > bar_height:
                line += "\033[37m▬\033[0m"  # Peak indicator
            else:
                line += " "
        print(line)
    
    print(f"\nPeaks shown above bars with ▬ character")


def test_waveform_manual(audio_data, width=80, height=20):
    """Test WAVEFORM visualization."""
    print("\n" + "="*80)
    print("MODE 3: WAVEFORM")
    print("="*80)
    
    # Get waveform data
    if len(audio_data) > width:
        step = len(audio_data) // width
        waveform = audio_data[::step][:width]
    else:
        waveform = np.pad(audio_data, (0, width - len(audio_data)), 'constant')
    
    # Normalize
    if np.max(np.abs(waveform)) > 0:
        waveform = waveform / np.max(np.abs(waveform))
    
    middle = height // 2
    
    # Build visual
    for row in range(height):
        line = ""
        for col in range(width):
            wave_value = waveform[col]
            wave_height = int(wave_value * (middle - 1))
            target_row = middle - wave_height
            
            if row == target_row:
                line += "\033[32m█\033[0m"
            elif row == middle:
                line += "\033[90m─\033[0m"  # Center line
            else:
                line += " "
        print(line)
    
    print(f"\nOscilloscope display with center reference line")


def test_mirror_circular_manual(audio_data, width=80, height=20):
    """Test MIRROR_CIRCULAR visualization."""
    print("\n" + "="*80)
    print("MODE 4: MIRROR_CIRCULAR")
    print("="*80)
    
    num_bars = width // 2
    bar_heights = base.compute_frequency_bars(audio_data, num_bars, fft_size=4096)
    center = height // 2
    
    # Build visual
    for row in range(height):
        line = ""
        for col in range(width):
            # Determine which bar this column corresponds to
            if col < num_bars:
                bar_idx = num_bars - col - 1  # Left half (reversed)
            else:
                bar_idx = col - num_bars  # Right half
            
            if bar_idx < len(bar_heights):
                bar_height = int(bar_heights[bar_idx] * center)
                distance_from_center = abs(row - center)
                
                if distance_from_center <= bar_height:
                    height_ratio = bar_heights[bar_idx]
                    if height_ratio < 0.4:
                        color = "\033[32m"
                    elif height_ratio < 0.7:
                        color = "\033[33m"
                    else:
                        color = "\033[31m"
                    line += color + "█" + "\033[0m"
                else:
                    line += " "
            else:
                line += " "
        print(line)
    
    print(f"\nVertical bars from center, mirrored left/right and top/bottom")


def test_circular_wave_manual(audio_data, width=80, height=20):
    """Test CIRCULAR_WAVE visualization."""
    print("\n" + "="*80)
    print("MODE 5: CIRCULAR_WAVE")
    print("="*80)
    
    # Get waveform
    num_points = 120
    if len(audio_data) > num_points:
        step = len(audio_data) // num_points
        waveform = audio_data[::step][:num_points]
    else:
        waveform = np.pad(audio_data, (0, num_points - len(audio_data)), 'constant')
    
    if np.max(np.abs(waveform)) > 0:
        waveform = waveform / np.max(np.abs(waveform))
    
    center_y = height // 2
    center_x = width // 2
    base_radius = min(height // 2 - 2, width // 4)
    
    # Create canvas
    canvas = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Draw circle
    for i in range(num_points):
        angle = (i / num_points) * 2 * np.pi
        wave_offset = waveform[i] * base_radius * 0.4
        radius = base_radius + wave_offset
        
        x = int(center_x + radius * np.cos(angle))
        y = int(center_y + radius * np.sin(angle) * 0.5)  # Aspect correction
        
        if 0 <= x < width and 0 <= y < height:
            intensity = abs(wave_offset / base_radius) if base_radius > 0 else 0
            if intensity < 0.4:
                color = "\033[32m"
            elif intensity < 0.7:
                color = "\033[33m"
            else:
                color = "\033[31m"
            canvas[y][x] = color + "█" + "\033[0m"
    
    # Print canvas
    for row in canvas:
        print(''.join(row))
    
    print(f"\nCircle with waveform modulating radius (120 points)")


def test_levels_manual(audio_data, width=80, height=20):
    """Test LEVELS visualization."""
    print("\n" + "="*80)
    print("MODE 6: LEVELS")
    print("="*80)
    
    bar_heights = base.compute_frequency_bars(audio_data, 20, fft_size=4096)
    
    bands_per_row = 4
    bar_width = width // bands_per_row - 2
    
    for idx, height_val in enumerate(bar_heights[:12]):  # Show first 12
        if idx % bands_per_row == 0 and idx > 0:
            print()  # New line every 4 bands
        
        bar_length = int(height_val * bar_width)
        
        # Determine color
        if height_val < 0.4:
            color = "\033[32m"
        elif height_val < 0.7:
            color = "\033[33m"
        else:
            color = "\033[31m"
        
        line = "  "
        line += color + "█" * bar_length + "\033[0m"
        line += "\033[90m░\033[0m" * (bar_width - bar_length)
        print(line, end="")
    
    print("\n\nHorizontal VU meter bars (20 frequency bands)")


def main():
    print("MANUAL VISUALIZATION TEST")
    print("Testing with live audio...")
    print()
    
    audio_data = get_test_audio()
    
    if audio_data is None or len(audio_data) == 0:
        print("ERROR: No audio data captured!")
        sys.exit(1)
    
    print(f"✓ Captured audio: {len(audio_data)} samples, max={np.max(np.abs(audio_data)):.3f}")
    
    # Test each mode
    test_bars_manual(audio_data)
    test_spectrum_manual(audio_data)
    test_waveform_manual(audio_data)
    test_mirror_circular_manual(audio_data)
    test_circular_wave_manual(audio_data)
    test_levels_manual(audio_data)
    
    print("\n" + "="*80)
    print("ALL MODES TESTED")
    print("="*80)


if __name__ == "__main__":
    main()