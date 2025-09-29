# CLI Audio Visualizer

A beautiful, cross-platform audio visualizer for your terminal, written in Python. Features multiple visualization modes, colorful output, and excellent compatibility with PulseAudio (Linux), WASAPI (Windows), and CoreAudio (macOS).

![Demo](https://via.placeholder.com/800x400/1a1a1a/00ff00?text=CLI+Audio+Visualizer+Demo)

## Features

- 🎵 **Real-time audio visualization** from your system's microphone or audio input
- 🌈 **Multiple visualization modes**: bars, waveform, spectrum analyzer, dots, and blocks
- 🎨 **Colorful terminal output** with intensity-based color coding
- ⚡ **Cross-platform compatibility**: Linux (PulseAudio), Windows (WASAPI), macOS (CoreAudio)
- 🔄 **Easy mode switching** with spacebar
- 💾 **Configuration persistence** - remembers your last used visualization
- 🎛️ **Smooth animations** with configurable refresh rate and smoothing

## Installation

### From PyPI (coming soon)
```bash
pip install cli-audio-visualizer
```

### From Source
```bash
git clone https://github.com/SimonBaars/cli-audio-visualizer.git
cd cli-audio-visualizer
pip install -r requirements.txt
pip install .
```

### System Dependencies

#### Linux (Ubuntu/Debian)
```bash
# For PulseAudio support
sudo apt-get update
sudo apt-get install pulseaudio pulseaudio-utils python3-dev portaudio19-dev

# For development headers
sudo apt-get install python3-pyaudio-dev
```

#### Linux (Fedora/RedHat)
```bash
# For PulseAudio support
sudo dnf install pulseaudio pulseaudio-utils python3-devel portaudio-devel
```

#### macOS
```bash
# Using Homebrew
brew install portaudio
```

#### Windows
No additional system dependencies required - uses WASAPI by default.

## Usage

### Command Line
After installation, run:
```bash
audio-visualizer
```

Or if installed from source:
```bash
python -m audio_visualizer.main
```

### Controls
- **SPACE**: Cycle through visualization modes
- **Q** or **ESC**: Quit the application

### Visualization Modes

1. **Bars** - Classic frequency bars visualization
2. **Waveform** - Time-domain waveform display
3. **Spectrum** - Frequency spectrum analyzer with color-coded frequency bands
4. **Dots** - Dot matrix pattern based on frequency and time
5. **Blocks** - Block-style visualization with variable block heights

## Configuration

The visualizer automatically saves your preferences in `~/.cli-audio-visualizer/config.json`:

```json
{
  "last_visualization": "bars",
  "colors": true,
  "sensitivity": 1.0,
  "smoothing": 0.5,
  "fps": 30
}
```

## Audio Input Setup

### Linux with PulseAudio
The visualizer works best with PulseAudio and will automatically detect and use PulseAudio devices. To monitor system audio output:

```bash
# Create a monitor source for your speakers
pactl load-module module-loopback latency_msec=1

# List audio sources
pactl list sources short

# Set default input to monitor your speakers
pactl set-default-source alsa_output.pci-0000_00_1f.3.analog-stereo.monitor
```

### Windows
The visualizer uses WASAPI by default. For system audio capture, you may need to enable "Stereo Mix" or use third-party software to route system audio to a virtual input device.

### macOS
Uses CoreAudio by default. For system audio capture, consider using tools like BlackHole or SoundFlower to route system audio to a virtual input device.

## Troubleshooting

### No Audio Input Detected
1. Check that your system audio is properly configured and accessible
2. Verify audio permissions are granted to terminal applications
3. On Linux, ensure PulseAudio is running: `systemctl --user status pulseaudio`
4. For system audio capture, use loopback devices or monitor sources

### Performance Issues
1. Reduce refresh rate by modifying the config file
2. Close other audio applications that might be using the audio device
3. Try a different visualization mode (some are more computationally intensive)

### Installation Issues
1. Make sure you have Python 3.7+ installed
2. Install system audio dependencies before Python packages
3. On Linux, you may need to install additional development packages

## Development

### Setup Development Environment
```bash
git clone https://github.com/SimonBaars/cli-audio-visualizer.git
cd cli-audio-visualizer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### Project Structure
```
cli-audio-visualizer/
├── audio_visualizer/
│   ├── __init__.py
│   ├── main.py              # Main application entry point
│   ├── audio_capture.py     # Cross-platform audio capture
│   ├── visualizer.py        # Visualization engine
│   └── config.py           # Configuration management
├── setup.py
├── requirements.txt
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Uses [sounddevice](https://github.com/spatialaudio/python-sounddevice) for cross-platform audio capture
- Powered by [NumPy](https://numpy.org/) for efficient audio processing
