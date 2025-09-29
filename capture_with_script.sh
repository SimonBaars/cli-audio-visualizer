#!/bin/bash
# Capture visualizer output using script command

cd /home/simon/git/cli-audio-visualizer
source venv/bin/activate

echo "Capturing visualization snapshots..."

# Create a simple script that switches modes automatically
cat > auto_capture.py << 'EOAUTO'
import sys
import time

modes = ['bars', 'spectrum', 'waveform', 'mirror_circular', 'circular_wave', 'levels']

for i, mode in enumerate(modes):
    print(f"\n=== Capturing {mode.upper()} ===", file=sys.stderr)
    time.sleep(2)
    print(" ", file=sys.stderr)  # Send space to switch mode
    sys.stderr.flush()

time.sleep(1)
print("q", file=sys.stderr)  # Quit
EOAUTO

# Run with timeout
timeout 15 python visualizer.py 2>&1 | tee visualizer_output.txt

echo "Output captured to visualizer_output.txt"