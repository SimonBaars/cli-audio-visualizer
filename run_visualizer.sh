#!/bin/bash
# Quick launcher for the stable audio visualizer

echo "🎵 Starting Stable CLI Audio Visualizer..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv and run
source venv/bin/activate

# Check if dependencies are installed
python -c "import sounddevice, numpy, curses" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencies not installed!"
    echo "Run: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Run the visualizer
python visualizer_stable.py