# Audio Setup Guide

## Quick Start

The stable visualizer will automatically try to detect your system audio. Just run:

```bash
source venv/bin/activate
python visualizer_stable.py
```

If you see audio bars moving, you're all set! If not, follow the platform-specific instructions below.

---

## Linux Setup

### PipeWire (Modern Distros - Ubuntu 22.04+, Fedora 34+, Arch)

PipeWire usually works out of the box! The visualizer will automatically detect monitor sources.

**Troubleshooting:**
```bash
# Check if PipeWire is running
pw-top

# List available sources
pw-cli list-objects | grep -i monitor
```

### PulseAudio (Older Distros)

The visualizer will try to automatically detect monitor devices. If it doesn't work:

**Method 1: Using pavucontrol (Easiest)**
```bash
# Install GUI tool
sudo apt install pavucontrol

# Run visualizer
python visualizer_stable.py

# In another terminal, run:
pavucontrol

# In pavucontrol:
# 1. Go to "Recording" tab
# 2. Find "visualizer_stable.py" or "python"
# 3. Change input to "Monitor of [Your Output Device]"
```

**Method 2: Command Line**
```bash
# List available monitor sources
pactl list sources short | grep monitor

# The visualizer should auto-detect these, but you can also set default:
pactl set-default-source <monitor-source-name>
```

**Method 3: Create Loopback**
```bash
# This creates a virtual loopback
pactl load-module module-loopback latency_msec=1

# To remove it later:
pactl unload-module module-loopback
```

**Helper Script:**
```bash
./setup_audio_linux.sh
```

---

## Windows Setup

Windows requires enabling "Stereo Mix" to capture system audio.

### Steps:

1. **Right-click the speaker icon** in the system tray
2. Click **"Sounds"** or **"Open Sound settings"**
3. Go to the **"Recording"** tab
4. **Right-click** in the empty space and enable:
   - ☑ Show Disabled Devices
   - ☑ Show Disconnected Devices
5. You should see **"Stereo Mix"** or **"Wave Out Mix"**
6. **Right-click "Stereo Mix"** → **Enable**
7. **Right-click "Stereo Mix"** → **Set as Default Device**
8. Click **OK**

Now run the visualizer:
```bash
venv\Scripts\activate
python visualizer_stable.py
```

**Note:** Not all audio drivers support Stereo Mix. If you don't see it:
- Update your audio drivers
- Or install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)

---

## macOS Setup

macOS doesn't have built-in system audio capture. You need a virtual audio device.

### Option 1: BlackHole (Free, Recommended)

1. **Install BlackHole:**
   ```bash
   brew install blackhole-2ch
   ```
   Or download from: https://github.com/ExistentialAudio/BlackHole

2. **Configure Multi-Output Device:**
   - Open **Audio MIDI Setup** (in `/Applications/Utilities/`)
   - Click **"+"** → Create **"Multi-Output Device"**
   - Check both:
     - ☑ Your speakers/headphones
     - ☑ BlackHole 2ch
   - Right-click → Use as **"Default Output"**

3. **Set BlackHole as Input:**
   - In System Preferences → Sound → Input
   - Select **BlackHole 2ch**

4. **Run the visualizer:**
   ```bash
   source venv/bin/activate
   python visualizer_stable.py
   ```

### Option 2: Loopback (Paid, Easiest)

Install [Loopback by Rogue Amoeba](https://rogueamoeba.com/loopback/) - it provides a GUI for routing audio.

---

## Troubleshooting

### No Visualization Bars Moving

1. **Check if audio is playing** - play some music/video
2. **Check volume** - make sure system volume is up
3. **Run the visualizer** - it will show available devices and what it's using
4. **Look for "Audio ●"** in the top-right - if it shows "Audio ○", no audio is detected

### Audio Working But Visualization Weak

- The visualizer auto-scales, but try increasing your system volume
- Bass-heavy music shows better than podcasts/speech
- Try different visualization modes with **SPACE**

### Terminal Issues

If the terminal glitches or doesn't render properly:
- Make sure your terminal supports Unicode and colors
- Try a different terminal emulator (kitty, alacritty, iTerm2)
- Resize the terminal to trigger a redraw

### Audio Device Not Found

Run this to see all devices:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Look for devices with names containing:
- "monitor"
- "loopback"  
- "stereo mix"
- "what u hear"

---

## Controls

- **SPACE** - Cycle through visualization modes
- **Q** or **ESC** - Quit

## Visualization Modes

1. **bars** - Classic frequency bars
2. **spectrum** - Spectrum analyzer with frequency colors
3. **waveform** - Time-domain waveform
4. **blocks** - Gradient block visualization

---

## Technical Details

**Why the new `visualizer_stable.py`?**

The original visualizer used Rich Live which can be glitchy with:
- High refresh rates causing flicker
- Terminal scrolling breaking the display
- Alternate screen buffer issues

The stable version uses **curses** which is:
- ✓ Built into Python (no extra dependencies)
- ✓ Rock-solid terminal rendering
- ✓ No flickering or glitching
- ✓ Proper keyboard handling
- ✓ Works on all platforms

**Audio Detection:**

The improved audio capture:
- Auto-detects system audio monitor sources
- Lists all available devices with hints
- Provides platform-specific setup instructions
- Has better error handling and debugging output