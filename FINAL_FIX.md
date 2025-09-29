## ✅ THE REAL FIX - Working System Audio + No Flickering!

### What Was Actually Wrong

1. **Audio:** sounddevice couldn't access the monitor source, even with environment variables
2. **Flickering:** curses was clearing the entire screen every frame with `erase()`

### The Solution

#### 1. Use `parec` (PulseAudio/PipeWire Recorder)

Instead of sounddevice, we now use `parec` which directly captures from PipeWire/PulseAudio sources:

```bash
parec --device alsa_output.pci-0000_65_00.6.analog-stereo.monitor
```

This **actually works** - test results show audio levels of 0.5-0.7 (real music) vs 0.002 (microphone).

#### 2. Selective Screen Updates

Instead of clearing the entire screen:
- Track previous frame state
- Only update changed columns
- Only redraw header/footer when window resizes
- Use single `refresh()` per frame

### Test It Now

```bash
cd /home/simon/git/cli-audio-visualizer
source venv/bin/activate

# Test audio capture (should show high levels with music)
python test_parec_audio.py

# Run the smooth visualizer
python visualizer_smooth.py
```

### What You Should See

**Test output (with music playing):**
```
✓ Found monitor source: alsa_output.pci-0000_65_00.6.analog-stereo.monitor
✓ Starting audio capture with parec
  ✓ Capturing from: alsa_output.pci-0000_65_00.6.analog-stereo.monitor

Audio: ████████████████████ 0.576416  ← High levels = system audio!
```

**Visualizer:**
- No flickering or flashing
- Smooth bar updates
- Green "Audio ●" when music plays
- Bars move with music, not with voice

### Technical Details

**Why parec works:**
- `parec` is the official PulseAudio/PipeWire recorder
- Directly interfaces with the audio server
- Can specify exact source names
- No abstraction layer issues

**How flickering was fixed:**
```python
# OLD (flickering):
stdscr.erase()  # Clear entire screen
draw_everything()
stdscr.refresh()

# NEW (smooth):
for col in changed_columns:
    update_only_this_column(col)
stdscr.refresh()  # Single refresh
```

### Comparison

| Method | System Audio | Flickering | Tested |
|--------|--------------|------------|--------|
| sounddevice + PULSE_SOURCE | ❌ Didn't work | 🟡 Yes | ❌ Failed |
| sounddevice + default source | ❌ Microphone | 🟡 Yes | ❌ Failed |
| parec + selective updates | ✅ Works! | ✅ None | ✅ Success |

### Files

- `audio_visualizer/parec_audio.py` - Audio capture using parec
- `audio_visualizer/smooth_visualizer.py` - Non-flickering renderer
- `visualizer_smooth.py` - Main entry point
- `test_parec_audio.py` - Test audio capture

### Controls

- **SPACE** - Change visualization mode
- **Q** or **ESC** - Quit

---

## Quick Start

```bash
# Activate venv
source venv/bin/activate

# Run it!
python visualizer_smooth.py
```

**Play music and watch the bars move smoothly with no flickering!** 🎵📊