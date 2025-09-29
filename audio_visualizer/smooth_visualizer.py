"""Smooth curses-based visualizer with multiple distinct modes and color schemes."""

import curses
import numpy as np
from typing import Optional
import math
from . import visualizers


class SmoothVisualizer:
    """Non-flickering visualizer with distinct modes and color schemes."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.current_mode = 0
        self.current_color_scheme = 0
        self.modes = ["bars", "spectrum", "waveform", "mirror_circular", "circular_wave", "levels"]
        self.color_schemes = ["multicolor", "blue", "green", "red", "rainbow", "fire"]
        
        # Initialize curses
        curses.curs_set(0)
        try:
            curses.use_default_colors()
        except:
            pass  # Some terminals don't support this
        stdscr.nodelay(1)
        stdscr.timeout(0)
        
        # Initialize colors
        self._init_colors()
        
        # Smoothing - reduced for responsiveness
        self.smoothing_factor = 0.6
        self.previous_values = None
        self.previous_waveform = None
        
        # FFT parameters
        self.fft_size = 4096
        
        # Store previous frame
        self.prev_height = 0
        self.prev_width = 0
        self.prev_bars = None
        self.mode_changed = False
        
        # State dict for visualizers
        self.viz_state = {}
        
        # Clear once at start
        self.stdscr.clear()
        self.stdscr.refresh()
    
    def _init_colors(self):
        """Initialize color pairs."""
        if curses.has_colors():
            curses.start_color()
            # Basic colors
            curses.init_pair(1, curses.COLOR_BLUE, -1)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_RED, -1)
            curses.init_pair(6, curses.COLOR_MAGENTA, -1)
            curses.init_pair(7, curses.COLOR_WHITE, -1)
    
    def _get_color(self, level: float, position: float = 0.5) -> int:
        """Get color based on amplitude level and color scheme."""
        if not curses.has_colors():
            return 0
        
        level = max(0, min(1, level))
        scheme = self.color_schemes[self.current_color_scheme]
        
        if scheme == "multicolor":
            # Green -> Yellow -> Red gradient (common in audio visualizers)
            if level < 0.4:
                return curses.color_pair(3)  # Green
            elif level < 0.7:
                return curses.color_pair(4)  # Yellow
            else:
                return curses.color_pair(5)  # Red
        
        elif scheme == "blue":
            if level < 0.3:
                return curses.color_pair(1)  # Blue
            elif level < 0.7:
                return curses.color_pair(2)  # Cyan
            else:
                return curses.color_pair(7)  # White
        
        elif scheme == "green":
            if level < 0.5:
                return curses.color_pair(3)  # Green
            else:
                return curses.color_pair(4)  # Yellow
        
        elif scheme == "red":
            if level < 0.5:
                return curses.color_pair(4)  # Yellow
            else:
                return curses.color_pair(5)  # Red
        
        elif scheme == "rainbow":
            # Use position for rainbow effect
            if position < 0.2:
                return curses.color_pair(5)  # Red
            elif position < 0.4:
                return curses.color_pair(4)  # Yellow
            elif position < 0.6:
                return curses.color_pair(3)  # Green
            elif position < 0.8:
                return curses.color_pair(2)  # Cyan
            else:
                return curses.color_pair(1)  # Blue
        
        elif scheme == "fire":
            # Fire gradient
            if level < 0.3:
                return curses.color_pair(5)  # Red
            elif level < 0.6:
                return curses.color_pair(4)  # Yellow
            else:
                return curses.color_pair(7)  # White
        
        return curses.color_pair(3)
    
    def _apply_smoothing(self, values: np.ndarray, use_waveform: bool = False) -> np.ndarray:
        """Apply temporal smoothing."""
        if use_waveform:
            if self.previous_waveform is None or len(self.previous_waveform) != len(values):
                self.previous_waveform = values
                return values
            smoothed = (self.smoothing_factor * self.previous_waveform + 
                       (1 - self.smoothing_factor) * values)
            self.previous_waveform = smoothed
            return smoothed
        else:
            if self.previous_values is None or len(self.previous_values) != len(values):
                self.previous_values = values
                return values
            smoothed = (self.smoothing_factor * self.previous_values + 
                       (1 - self.smoothing_factor) * values)
            self.previous_values = smoothed
            return smoothed
    
    def draw_header(self, width: int, audio_active: bool, device_name: str = ""):
        """Draw header."""
        height, _ = self.stdscr.getmaxyx()
        
        if width != self.prev_width or height != self.prev_height:
            try:
                self.stdscr.move(0, 0)
                self.stdscr.clrtoeol()
                self.stdscr.move(1, 0)
                self.stdscr.clrtoeol()
                
                title = "♪ CLI AUDIO VISUALIZER ♪"
                self.stdscr.addstr(0, (width - len(title)) // 2, title, 
                                 curses.color_pair(6) | curses.A_BOLD)
                
                mode_text = f"Mode: {self.modes[self.current_mode].upper()}"
                color_text = f"Color: {self.color_schemes[self.current_color_scheme].upper()}"
                self.stdscr.addstr(1, 2, mode_text, curses.color_pair(2))
                self.stdscr.addstr(1, 30, color_text, curses.color_pair(3))
            except curses.error:
                pass
        
        try:
            status = "●" if audio_active else "○"
            status_color = curses.color_pair(3) if audio_active else curses.color_pair(5)
            self.stdscr.addstr(1, width - 10, f"Audio {status}", status_color)
        except curses.error:
            pass
    
    def draw_footer(self, width: int, height: int):
        """Draw footer."""
        if width != self.prev_width or height != self.prev_height:
            try:
                self.stdscr.move(height - 1, 0)
                self.stdscr.clrtoeol()
                
                controls = "[SPACE] Mode  [ENTER] Color  [Q] Quit"
                self.stdscr.addstr(height - 1, (width - len(controls)) // 2, controls,
                                 curses.color_pair(4))
            except curses.error:
                pass
    
    def visualize(self, audio_data: Optional[np.ndarray], device_name: str = "Unknown"):
        """Main visualization."""
        try:
            height, width = self.stdscr.getmaxyx()
            audio_active = audio_data is not None and len(audio_data) > 0 and np.max(np.abs(audio_data)) > 0.001
            
            # No header or footer - full screen visualization
            viz_height = height
            viz_width = width
            y_offset = 0
            
            # Draw visualization
            if audio_data is not None and len(audio_data) > 0:
                mode = self.modes[self.current_mode]
                
                # Clear state on mode change
                if self.mode_changed:
                    self.viz_state = {}
                    visualizers.base.clear_area(self.stdscr, y_offset, viz_height, viz_width)
                    self.mode_changed = False
                
                if mode == "bars":
                    visualizers.draw_bars(self.stdscr, audio_data, viz_height, viz_width, y_offset,
                                        self._get_color, self._apply_smoothing, self.viz_state)
                elif mode == "spectrum":
                    visualizers.draw_spectrum(self.stdscr, audio_data, viz_height, viz_width, y_offset,
                                            self._get_color, self._apply_smoothing, self.viz_state)
                elif mode == "waveform":
                    visualizers.draw_waveform(self.stdscr, audio_data, viz_height, viz_width, y_offset,
                                            self._get_color, self._apply_smoothing, self.viz_state)
                elif mode == "mirror_circular":
                    visualizers.draw_mirror_circular(self.stdscr, audio_data, viz_height, viz_width, y_offset,
                                                   self._get_color, self._apply_smoothing, self.viz_state)
                elif mode == "circular_wave":
                    visualizers.draw_circular_wave(self.stdscr, audio_data, viz_height, viz_width, y_offset,
                                                  self._get_color, self._apply_smoothing, self.viz_state)
                elif mode == "levels":
                    visualizers.draw_levels(self.stdscr, audio_data, viz_height, viz_width, y_offset,
                                          self._get_color, self._apply_smoothing, self.viz_state)
            
            self.prev_height = height
            self.prev_width = width
            self.stdscr.refresh()
            
        except curses.error:
            pass
    
    def handle_input(self) -> bool:
        """Handle keyboard input."""
        try:
            key = self.stdscr.getch()
            
            if key == -1 or key == curses.ERR:
                return True
            
            if key == ord('q') or key == ord('Q') or key == 27:
                return False
            elif key == ord(' '):
                # Change mode
                self.current_mode = (self.current_mode + 1) % len(self.modes)
                self.previous_values = None
                self.previous_waveform = None
                self.prev_bars = None
                self.mode_changed = True
                self.prev_width = 0
                self.prev_height = 0
            elif key == ord('\n') or key == ord('\r') or key == 10 or key == 13:
                # Change color scheme
                self.current_color_scheme = (self.current_color_scheme + 1) % len(self.color_schemes)
                self.prev_width = 0
                self.prev_height = 0
        
        except curses.error:
            pass
        
        return True