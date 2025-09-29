# Visualization Modes & Color Schemes

## 🎨 6 Distinct Visualization Modes

### 1. BARS (Classic Frequency Bars)
```
█
█ █
█ █ █
█ █ █ █
█ █ █ █ █
```
- Classic frequency bars from bottom up
- Logarithmic frequency distribution (20 Hz - 20 kHz)
- Bass on left, treble on right

### 2. SPECTRUM (Block Gradient)
```
█
▇ ▇
▆ ▆ ▆
▄ ▄ ▄ ▄
▂ ▂ ▂ ▂ ▂
```
- Uses gradient block characters (▁▂▃▄▅▆▇█)
- Shows frequency intensity with block density
- Smooth visual gradient effect

### 3. WAVEFORM (Time Domain)
```
    █
  █   █
█       █
─────────── (center line)
```
- Actual audio waveform over time
- Shows audio signal amplitude
- Center line represents zero

### 4. MIRROR_CIRCULAR (Vertical Mirror)
```
     ███
   ███████
     ███
   (center)
     ███
   ███████
     ███
```
- Frequency bars grow from center vertically
- Mirrored top/bottom
- Mirrored left/right
- Great for symmetrical effect

### 5. CIRCULAR_WAVE (Actual Circle) ⭐ NEW!
```
    ●●●●●
  ●       ●
 ●         ●
●           ●
 ●         ●
  ●       ●
    ●●●●●
```
- Forms an actual circle
- Waveform modulates the radius
- Top and bottom are mirrored
- Smooth, flowing circular motion
- **This is what you wanted!**

### 6. LEVELS (VU Meters)
```
Band 1: ████████░░░░
Band 2: ██████░░░░░░
Band 3: ███████████░
Band 4: ████░░░░░░░░
```
- VU meter style level meters
- 20 frequency bands in grid layout
- Classic studio equipment look

---

## 🌈 6 Color Schemes

### 1. MULTICOLOR (Default) ⭐
- **Green** (low levels): Quiet/safe
- **Yellow** (medium): Getting loud
- **Red** (high): Peak/loud
- Classic audio visualizer colors!

### 2. BLUE
- Dark blue → Cyan → White
- Cool, calming ocean theme

### 3. GREEN
- Green → Yellow
- Natural, organic feel

### 4. RED
- Yellow → Red
- Hot, energetic theme

### 5. RAINBOW
- Uses position for color (not amplitude)
- Red → Yellow → Green → Cyan → Blue
- Full spectrum across width

### 6. FIRE
- Red → Yellow → White
- Fire/heat theme

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| **SPACE** | Cycle through visualization modes |
| **ENTER** | Cycle through color schemes |
| **Q** or **ESC** | Quit |

---

## 💡 Tips for Each Mode

### BARS
- Best for seeing full frequency spectrum
- Good for all types of music
- Clear separation of bass/mids/treble

### SPECTRUM
- More "analog" looking
- Block gradient shows intensity smoothly
- Great for electronic music

### WAVEFORM
- Shows actual audio signal
- Best with simple sounds or voice
- Good for seeing dynamics

### MIRROR_CIRCULAR
- Very symmetrical and pleasing
- Great for bass-heavy music
- Looks like speaker visualization

### CIRCULAR_WAVE ⭐
- Most unique and eye-catching
- Circle "breathes" with the music
- Perfect for showing rhythm
- Try with electronic or orchestral music!

### LEVELS
- Professional studio feel
- Good for mixing/mastering perspective
- Shows frequency balance clearly

---

## 🎵 Recommended Combinations

**Electronic/EDM:**
- Mode: CIRCULAR_WAVE or MIRROR_CIRCULAR
- Color: MULTICOLOR or FIRE

**Rock/Metal:**
- Mode: BARS or SPECTRUM  
- Color: MULTICOLOR or RED

**Classical/Orchestra:**
- Mode: CIRCULAR_WAVE or WAVEFORM
- Color: RAINBOW or BLUE

**Hip-Hop/Bass:**
- Mode: MIRROR_CIRCULAR or BARS
- Color: MULTICOLOR or FIRE

**Ambient/Chill:**
- Mode: CIRCULAR_WAVE or WAVEFORM
- Color: BLUE or GREEN

---

## 🎯 What Makes Each Mode Distinct

| Mode | Visual Style | Best For | Uniqueness |
|------|-------------|----------|------------|
| BARS | Vertical bars | All music | Classic, reliable |
| SPECTRUM | Block gradient | Electronic | Smooth analog feel |
| WAVEFORM | Oscilloscope | Voice/simple | Shows actual signal |
| MIRROR_CIRCULAR | Vertical mirror | Bass music | Symmetrical beauty |
| CIRCULAR_WAVE | Circle modulation | Rhythmic music | Most unique! |
| LEVELS | Horizontal meters | Technical view | Pro studio look |

---

## 🔧 Technical Details

### Color Implementation
```python
# MULTICOLOR (green->yellow->red)
if level < 0.4:   # Green (safe)
    color = GREEN
elif level < 0.7: # Yellow (caution)
    color = YELLOW
else:             # Red (peak)
    color = RED
```

### CIRCULAR_WAVE Algorithm
1. Get waveform data
2. Map each point to angle (0 to π for semicircle)
3. Calculate base circle position
4. Modulate radius by waveform amplitude
5. Mirror top to bottom
6. Draw with color based on amplitude

---

## 🚀 Usage

```bash
python visualizer_smooth.py

# Try different combinations:
# 1. Press SPACE to cycle modes
# 2. Press ENTER to cycle colors
# 3. Find your favorite combo!
```

---

**The CIRCULAR_WAVE mode with MULTICOLOR scheme is particularly stunning!** 🎵✨

Try it with music that has good rhythm and dynamics!