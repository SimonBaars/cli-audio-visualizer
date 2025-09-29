#!/usr/bin/env python3
"""
Stable CLI Audio Visualizer - Uses curses for rock-solid terminal UI
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio_visualizer.curses_main import main

if __name__ == "__main__":
    sys.exit(main())