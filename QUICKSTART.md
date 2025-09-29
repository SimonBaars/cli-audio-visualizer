# Quick Start Guide

## Step 1: Test Audio Detection

First, let's make sure audio capture works:

```bash
source venv/bin/activate
python test_audio.py
```

**Play some music/audio** and you should see bars moving showing the audio level.

### If You See Audio Bars Moving:
✅ Great! Audio capture is working. Skip to Step 3.

### If You DON'T See Audio:
The test will show what device it's using. You need to configure system audio capture.

---

## Step 2: Configure System Audio (Linux)

Based on the test output, you detected: `alsa_output.pci-0000_65_00.6.analog-stereo.monitor`

This is your monitor source! But we need to make sure the visualizer can use it.

### Option A: Use pavucontrol (Easiest)

1. Install if you don't have it:
   ```bash
   sudo pacman -S pavucontrol  # Arch
   # or
   sudo apt install pavucontrol  # Ubuntu/Debian
   ```

2. Run the visualizer:
   ```bash
   python visualizer_stable.py
   ```

3. In another terminal, run:
   ```bash
   pavucontrol
   ```

4. In pavucontrol:
   - Go to **"Recording"** tab
   - Find the Python/visualizer entry
   - In the dropdown, select: **"Monitor of Analog Stereo"** or similar

5. Audio should start showing immediately!

### Option B: Set Default Source

```bash
# Set the monitor as default
pactl set-default-source alsa_output.pci-0000_65_00.6.analog-stereo.monitor

# Now run visualizer
python visualizer_stable.py
```

### Option C: Use Environment Variable

```bash
# Set for this session
export PULSE_SOURCE=alsa_output.pci-0000_65_00.6.analog-stereo.monitor

# Run visualizer
python visualizer_stable.py
```

---

## Step 3: Run the Visualizer

```bash
source venv/bin/activate
python visualizer_stable.py
```

Or use the launcher:
```bash
./run_visualizer.sh
```

### Controls:
- **SPACE** - Cycle visualization modes
- **Q** or **ESC** - Quit

### Visualization Modes:
1. **bars** - Classic frequency bars
2. **spectrum** - Spectrum analyzer with colors
3. **waveform** - Time-domain waveform
4. **blocks** - Gradient blocks

---

## Troubleshooting

### "Press any key to continue..." hangs
This was a bug in the old version. Make sure you're running the latest code:
```bash
git pull  # if in git repo
python visualizer_stable.py
```

### Terminal crashes or glitches
- Make sure your terminal supports Unicode
- Try a different terminal (kitty, alacritty, gnome-terminal)
- Resize the terminal to trigger redraw

### No audio detected in pavucontrol
Make sure the visualizer is actually running when you check pavucontrol's Recording tab.

### Ctrl+C doesn't work
This should be fixed now. If it still happens:
1. Press Ctrl+Z to suspend
2. Run: `killall python` or `pkill -9 python`

---

## What Your System Shows

From your `pw-top` output, I can see:
- ✅ PipeWire is running
- ✅ Audio is playing (mpv at 44100 Hz)
- ✅ Monitor source exists: `alsa_output.pci-0000_65_00.6.analog-stereo`
- ✅ The visualizer is trying to capture (alsa_capture.python3.13)

The issue was that the code wasn't properly detecting and using the monitor source. This is now fixed!

---

## One-Command Setup (After First Run)

Create an alias in your `~/.bashrc`:

```bash
alias visualizer='cd /home/simon/git/cli-audio-visualizer && source venv/bin/activate && python visualizer_stable.py'
```

Then just run:
```bash
visualizer
```

---

## Still Not Working?

1. **Test audio first:**
   ```bash
   python test_audio.py
   ```

2. **Check what sources are available:**
   ```bash
   pactl list sources short
   ```

3. **Try manual device selection:**
   The improved code now tries multiple methods to find your monitor source!

4. **Check the output** - it now prints exactly what device it's using

5. **Join the debug info:**
   ```bash
   python visualizer_stable.py 2>&1 | tee debug.log
   ```
   Then share the debug.log if you need help.

---

**Pro Tip:** Keep `pavucontrol` open in the Recording tab while testing. You can change the input source on-the-fly without restarting the visualizer!