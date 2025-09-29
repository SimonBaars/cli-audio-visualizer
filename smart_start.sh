#!/bin/bash
# Smart launcher - tests audio then runs visualizer

set -e

echo "🎵 CLI Audio Visualizer - Smart Start"
echo "======================================"
echo ""

# Check venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check dependencies
python -c "import sounddevice, numpy, curses" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencies not installed!"
    echo "Run: pip install -r requirements.txt"
    exit 1
fi

echo "Step 1: Testing audio detection..."
echo ""

# Quick audio test
timeout 3 python test_audio.py 2>&1 | head -50 || true

echo ""
echo "======================================"
echo ""
read -p "Did you see audio bars moving? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "✅ Great! Starting visualizer..."
    echo ""
    sleep 1
    python visualizer_stable.py
else
    echo ""
    echo "⚠️  Audio not detected. Here's what to do:"
    echo ""
    echo "Option 1 (Easiest):"
    echo "  1. Open another terminal and run: pavucontrol"
    echo "  2. Start the visualizer: python visualizer_stable.py"
    echo "  3. In pavucontrol, go to Recording tab"
    echo "  4. Select 'Monitor of...' as input"
    echo ""
    echo "Option 2 (Set default):"
    echo "  pactl set-default-source alsa_output.pci-0000_65_00.6.analog-stereo.monitor"
    echo "  python visualizer_stable.py"
    echo ""
    echo "See QUICKSTART.md for detailed instructions."
    echo ""
    read -p "Try running visualizer anyway? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python visualizer_stable.py
    fi
fi