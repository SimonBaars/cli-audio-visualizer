#!/usr/bin/env python3
"""
CLI Audio Visualizer - Standalone script
A beautiful cross-platform audio visualizer for your terminal.
"""

import sys
import os

# Add the current directory to the Python path to find the audio_visualizer module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audio_visualizer.main import main

if __name__ == "__main__":
    sys.exit(main())