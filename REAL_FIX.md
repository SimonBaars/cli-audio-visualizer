# The Real Fix - System Audio Detection

## What Was Wrong

The code detected your monitor source (`alsa_output.pci-0000_65_00.6.analog-stereo.monitor`) but **wasn't actually using it**. It was falling back to the default microphone.

## The Solution

The key is the `PULSE_SOURCE` environment variable. PipeWire/PulseAudio respects this variable to determine which source to capture from.

### What Changed:

1. **Set PULSE_SOURCE environment variable:**
   ```python
   os.environ['PULSE_SOURCE'] = monitor_source
   ```
   
2. **Use the PipeWire/Pulse device** from sounddevice (devices with 'pipewire' or 'pulse' in the name respect the `PULSE_SOURCE` variable)

3. **Queue all audio data** (not just when there's signal) to prevent UI flashing

4. **Larger queue** (10 instead of 5) for smoother playback

---

## How to Test

### Step 1: Test Audio Detection

```bash
source venv/bin/activate
python test_audio.py
```

**Expected output:**
```
✓ Found monitor source: alsa_output.pci-0000_65_00.6.analog-stereo.monitor
✓ Set PULSE_SOURCE environment variable
✓ Using audio server: pipewire
✓ Will capture system audio from monitor source
```

**Play some music** and you should see:
```
Audio: ████████████████ 0.012345
```

If the level is too low, turn up your system volume!

---

### Step 2: Run the Visualizer

```bash
python visualizer_stable.py
```

You should see:
- ✓ At startup: "Capturing system audio"
- 🟢 "Audio ●" indicator in the top-right (green when audio detected)
- 📊 Visualization bars moving with your music!

---

## Controls

- **SPACE** - Change visualization mode
- **Q** or **ESC** - Quit

---

## Troubleshooting

### "Audio level is very low"

Turn up your system volume! The monitor captures at whatever level your system is outputting.

### "Still capturing microphone"

Check the startup output. It should say:
```
✓ Capturing system audio
   Source: alsa_output.pci-0000_65_00.6.analog-stereo.monitor
```

If it says "Capturing from microphone", the PULSE_SOURCE didn't work. Try:
```bash
export PULSE_SOURCE=alsa_output.pci-0000_65_00.6.analog-stereo.monitor
python visualizer_stable.py
```

### "Bars are still glitchy"

This should be fixed now because:
1. We queue all data (not just when there's signal)
2. Larger queue buffer
3. No "Waiting for audio" message flashing

---

## Technical Details

### Why sounddevice doesn't list the monitor

PipeWire's monitor sources are "virtual" sources that don't always show up in sounddevice's device list. But PipeWire/PulseAudio **do** respect the `PULSE_SOURCE` environment variable.

### The Fix

```python
# Find the monitor source via pactl
monitor_source = "alsa_output.pci-0000_65_00.6.analog-stereo.monitor"

# Tell PulseAudio/PipeWire to use it
os.environ['PULSE_SOURCE'] = monitor_source

# Use the pipewire/pulse device (which respects PULSE_SOURCE)
device = find_device_with_name_containing("pipewire")  # or "pulse"
stream = sounddevice.InputStream(device=device)
```

This is the standard way to capture system audio on Linux with PipeWire/PulseAudio!

---

## Verification

Run the test and look for these lines:

```
✓ Found monitor source: alsa_output.pci-0000_65_00.6.analog-stereo.monitor
✓ Set PULSE_SOURCE environment variable
✓ Using audio server: pipewire
✓ Will capture system audio from monitor source
```

If you see all four ✓ marks, it's configured correctly!

Then when audio starts:
```
✓ Audio capture started!
  ✓ Capturing system audio
     Source: alsa_output.pci-0000_65_00.6.analog-stereo.monitor
  🎵 Play some music and you should see visualization!
```

---

## Try It Now!

```bash
cd /home/simon/git/cli-audio-visualizer
source venv/bin/activate

# Test it
python test_audio.py  # Play music during this!

# Run the visualizer
python visualizer_stable.py
```

**Press SPACE to cycle through visualization modes!**

---

## Summary

| Issue | Status |
|-------|--------|
| Capturing microphone instead of system audio | ✅ Fixed - uses PULSE_SOURCE |
| UI says "Waiting for audio" constantly | ✅ Fixed - queues all data |
| Bars are glitchy and not smooth | ✅ Fixed - larger buffer |
| Terminal hangs on startup | ✅ Fixed - proper initialization |

**Everything should work smoothly now!** 🎵📊