# CLI Audio Visualizer

A real-time audio visualizer for your terminal that captures system audio and displays it with multiple visualization modes and color schemes.

## Features

- **6 Visualization Modes**: bars, spectrum, waveform, mirror_circular, circular_wave, levels
- **6 Color Schemes**: multicolor (green→yellow→red), blue, green, red, rainbow, fire
- **System Audio Capture**: Uses parec to capture audio from PulseAudio/PipeWire monitor sources
- **Smooth Rendering**: Selective screen updates with no flickering
- **Full Spectrum**: Logarithmic frequency distribution (20 Hz - 20 kHz)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cli-audio-visualizer.git
cd cli-audio-visualizer

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Requirements

- Python 3.7+
- PulseAudio or PipeWire (Linux)
- parec (PulseAudio recorder - usually pre-installed)

**Dependencies:**
- numpy
- curses (built-in on Linux/macOS)

## Usage

```bash
source venv/bin/activate
python visualizer.py
```

**Controls:**
- **SPACE** - Cycle through visualization modes
- **ENTER** - Cycle through color schemes
- **Q** or **ESC** - Quit

## Visualization Modes

1. **BARS** - Classic frequency bars with full spectrum
2. **SPECTRUM** - Block gradient visualization
3. **WAVEFORM** - Time-domain oscilloscope view
4. **MIRROR_CIRCULAR** - Vertical bars mirrored from center
5. **CIRCULAR_WAVE** - Circle that breathes with music
6. **LEVELS** - VU meter style horizontal bars

## Color Schemes

1. **MULTICOLOR** (default) - Green→Yellow→Red (classic audio levels)
2. **BLUE** - Blue→Cyan→White
3. **GREEN** - Green→Yellow
4. **RED** - Yellow→Red
5. **RAINBOW** - Full spectrum colors
6. **FIRE** - Red→Yellow→White

## Linux Audio Setup

The visualizer automatically detects PulseAudio/PipeWire monitor sources. If it doesn't capture system audio:

```bash
# Check available sources
pactl list sources short | grep monitor

# The visualizer will use: alsa_output.pci-0000_XX_XX.X.analog-stereo.monitor
```

If needed, you can set the default source:
```bash
pactl set-default-source alsa_output.pci-0000_XX_XX.X.analog-stereo.monitor
```

## Troubleshooting

**No audio detected:**
- Ensure audio is playing on your system
- Check that PulseAudio/PipeWire is running
- The visualizer will show which source it's using at startup

**Colors not showing:**
- Make sure your terminal supports colors
- Try a different terminal emulator (kitty, alacritty, gnome-terminal)

**Low visualization levels:**
- Turn up your system volume (parec captures at output level)
- Try bass-heavy music for better visualization

## Technical Details

- **Audio Capture**: Uses `parec` to directly capture from PulseAudio/PipeWire monitor sources
- **FFT**: 4096-point FFT for high frequency resolution
- **Frequency Range**: 20 Hz - 20 kHz with logarithmic binning
- **Rendering**: Curses with selective updates for smooth, flicker-free display
- **Frame Rate**: 60 FPS

## License

Apache License 2.0 - See LICENSE file for details.