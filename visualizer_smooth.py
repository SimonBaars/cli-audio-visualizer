#!/usr/bin/env python3
"""
Smooth CLI Audio Visualizer - Uses parec for reliable audio capture
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio_visualizer.smooth_main import main

if __name__ == "__main__":
    sys.exit(main())