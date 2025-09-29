#!/usr/bin/env python3
"""Capture actual screen snapshots of each visualization mode."""

import sys
import time
import curses
from audio_visualizer.parec_audio import ParecAudioCapture
from audio_visualizer.smooth_visualizer import SmoothVisualizer


def capture_screen_to_file(stdscr, filename, mode_name):
    """Capture the actual screen content to a file."""
    height, width = stdscr.getmaxyx()
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"MODE: {mode_name}\n")
        f.write(f"Screen size: {width}x{height}\n")
        f.write("=" * width + "\n\n")
        
        for y in range(height):
            line = ""
            for x in range(width):
                try:
                    ch_attr = stdscr.inch(y, x)
                    ch = ch_attr & 0xFF
                    
                    # Get actual character
                    if 32 <= ch <= 126 or ch >= 128:  # Printable
                        char = chr(ch)
                    else:
                        char = ' '
                    
                    # Get color pair number
                    color_pair = (ch_attr & curses.A_COLOR) >> 8
                    
                    # Add color info as annotation
                    if color_pair > 0 and char != ' ':
                        line += f"{char}[{color_pair}]"
                    else:
                        line += char
                except:
                    line += ' '
            
            f.write(line.rstrip() + "\n")
    
    print(f"✓ Captured {mode_name} to {filename}", file=sys.stderr)


def test_all_modes(stdscr):
    """Test each visualization mode and capture snapshots."""
    # Initialize audio
    print("Starting audio capture...", file=sys.stderr)
    audio = ParecAudioCapture(chunk_size=1024)
    audio.start()
    time.sleep(1.0)  # Wait for audio to start
    
    # Initialize visualizer
    viz = SmoothVisualizer(stdscr)
    
    modes = viz.modes
    
    for mode_idx, mode_name in enumerate(modes):
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Testing mode {mode_idx + 1}/{len(modes)}: {mode_name.upper()}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        
        # Switch to this mode
        viz.current_mode = mode_idx
        viz.mode_changed = True
        viz.viz_state = {}
        viz.previous_values = None
        viz.previous_waveform = None
        
        # Let it run for several frames to stabilize
        for frame in range(30):
            try:
                audio_data = audio.audio_queue.get(timeout=0.1)
            except:
                audio_data = None
            
            if audio_data is not None and len(audio_data) > 0:
                viz.visualize(audio_data, "System Audio")
            
            time.sleep(0.016)  # ~60 FPS
        
        # Capture the final frame
        filename = f"snapshot_{mode_idx+1}_{mode_name}.txt"
        capture_screen_to_file(stdscr, filename, mode_name.upper())
        
        # Brief pause between modes
        time.sleep(0.3)
    
    audio.stop()
    
    print("\n" + "="*60, file=sys.stderr)
    print("ALL SNAPSHOTS CAPTURED", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print("\nSnapshot files created:", file=sys.stderr)
    for i, mode in enumerate(modes):
        print(f"  {i+1}. snapshot_{i+1}_{mode}.txt", file=sys.stderr)
    print("\nPress any key to exit...", file=sys.stderr)
    
    stdscr.getch()


if __name__ == "__main__":
    try:
        # Set up environment for better terminal support
        import os
        if 'TERM' not in os.environ or os.environ['TERM'] == 'dumb':
            os.environ['TERM'] = 'xterm-256color'
        
        curses.wrapper(test_all_modes)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)