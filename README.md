# CLI Audio Visualizer

Real‑time, flashy, terminal audio visualization powered by PulseAudio / PipeWire monitor capture and a bunch of lovingly over‑tuned DSP & effects.

## ✨ Highlights

- **7 Modes**: `bars`, `spectrum`, `waveform`, `mirror_circular`, `circular_wave` (now with sparks, rays & halo), `levels` (vertical reactive meters), `radial_burst` (starfield).
- **Adaptive DSP**: Log‑spaced bands (20 Hz–20 kHz), tilt compensation, noise floor suppression, gamma + optional adaptive EQ (3 strengths) & flatten toggle.
- **Smooth + Responsive**: Temporal + spatial smoothing that keeps punchy attacks while taming HF jitter.
- **Particles & Fun**: Orbiting sparks, pulsing inner ring, radial rays, halo dots, starfield burst particles.
- **ASCII Toggle**: Instantly switch to minimal glyphs for compatibility or taste.
- **Persistent Config**: Last mode, color scheme, EQ mode, ASCII/flatten flags auto‑restored (`config.json`).
- **Snapshots**: Press `S` to dump current raw bars / levels to `./snapshots/*.json` for analysis.
- **Silent Startup**: No console spam unless there’s an error.

## 🎨 Color Schemes
`multicolor`, `blue`, `green`, `red`, `rainbow`, `fire`, `prism`, `heat`, `ocean` (cycled with ENTER).

## ⌨ Controls

| Key | Action |
|-----|--------|
| SPACE | Next visualization mode |
| ENTER | Next color scheme |
| W | Cycle Adaptive EQ: off → medium (EQ~) → strong (EQ+) |
| F | Toggle frequency tilt flatten (removes low→high bias) |
| B | Toggle ASCII/simple glyphs |
| S | Snapshot (bars / levels JSON) + save config |
| P | Persist config immediately |
| Q / ESC | Quit |

Header flags: `FLAT`, `EQ~`, `EQ+`, `ASCII` indicate active toggles.

## 🚀 Install

```bash
git clone https://github.com/yourusername/cli-audio-visualizer.git
cd cli-audio-visualizer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ▶ Run

```bash
source .venv/bin/activate
python visualizer.py
```

## 🧩 Requirements

- Linux with PulseAudio or PipeWire (for monitor capture via `parec`)
- Python 3.9+ (tested newer)  
- Terminal with UTF‑8 + color; ASCII mode available otherwise.

Dependencies: `numpy`, `rich` (for tooling), `colorama`, `sounddevice` (optional / future), standard `curses`.

## 🔊 Audio Capture Notes
The app auto‑detects a monitor source. To inspect manually:

```bash
pactl list sources short | grep monitor
```

If nothing appears, enable monitor profiles in your sound settings or PipeWire config.

## 🧪 Snapshots / Analysis
Snapshots land in `snapshots/` and include:
```json
{
	"mode": "bars",
	"bars": [...],
	"distribution": {"low_mean": ..., "high_mean": ...},
	"flatten": false,
	"color_scheme": "multicolor"
}
```
Great for tuning bar distribution offline.

## 🔧 Internals (Quick Tour)

- `audio_visualizer/dsp/bars.py` – core band computation (windowed rFFT, log bins, compensation, adaptive spatial smoothing).
- Visualizers under `audio_visualizer/visualizers/` each implement a `draw_*` function.
- Adaptive EQ = slow running mean with blend strength (0 / 0.4 / 0.65).
- Radial & circular modes add procedural particles (time‑based + energy modulated).

## 🛠 Troubleshooting

| Issue | Tip |
|-------|-----|
| No movement | Check system audio playing + correct monitor source exists |
| Too jittery | Enable medium adaptive EQ (press W) or ASCII mode for lighter rendering |
| Colors wrong | Try another terminal or disable themes forcing palette |
| High CPU | Reduce terminal size or switch to a simpler mode (bars / waveform) |

## 📜 License

Apache 2.0 – see `LICENSE`.

Have fun melting your terminal. PRs / ideas welcome.

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