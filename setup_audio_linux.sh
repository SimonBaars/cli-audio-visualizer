#!/bin/bash
# Setup script for capturing system audio on Linux

echo "=================================="
echo "Linux System Audio Setup Helper"
echo "=================================="
echo ""

# Detect audio system
if command -v pipewire &> /dev/null; then
    echo "✓ Detected: PipeWire"
    echo ""
    echo "PipeWire usually works out of the box."
    echo "The visualizer should automatically detect monitor sources."
    echo ""
    echo "If it doesn't work, try:"
    echo "  pw-top    # Check if audio is flowing"
    echo ""
    
elif command -v pulseaudio &> /dev/null || command -v pactl &> /dev/null; then
    echo "✓ Detected: PulseAudio"
    echo ""
    echo "Available audio sources:"
    pactl list sources short | grep -i monitor
    echo ""
    echo "The visualizer will automatically try to use a monitor source."
    echo ""
    echo "If you don't see any monitor sources, your audio might be"
    echo "going through a different device. Try:"
    echo ""
    echo "Option 1: Use pavucontrol (GUI)"
    echo "  1. Install: sudo apt install pavucontrol"
    echo "  2. Run: pavucontrol"
    echo "  3. Go to 'Recording' tab while visualizer is running"
    echo "  4. Select 'Monitor of [your output device]'"
    echo ""
    echo "Option 2: Create a loopback"
    echo "  pactl load-module module-loopback latency_msec=1"
    echo ""
    
else
    echo "⚠ Could not detect PulseAudio or PipeWire"
    echo ""
    echo "You may be using ALSA directly. For ALSA:"
    echo "  1. You'll need to set up a loopback device"
    echo "  2. See: https://alsa.opensrc.org/Loopback"
    echo ""
fi

echo "After setup, run the visualizer with:"
echo "  source venv/bin/activate"
echo "  python visualizer_stable.py"
echo ""