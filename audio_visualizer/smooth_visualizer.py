"""Smooth curses-based visualizer with no flickering."""

import curses
import numpy as np
from typing import Optional
import math


class SmoothVisualizer:
    """Non-flickering visualizer using selective updates."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.current_mode = 0
        self.modes = ["bars", "spectrum", "mirror_circular", "waveform"]
        
        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        curses.use_default_colors()
        stdscr.nodelay(1)
        stdscr.timeout(0)  # Non-blocking
        
        # Initialize colors
        self._init_colors()
        
        # Smoothing - reduced for more responsiveness
        self.smoothing_factor = 0.6
        self.previous_values = None
        
        # FFT parameters
        self.fft_size = 4096  # Larger for better frequency resolution
        
        # Store previous frame to avoid redrawing unchanged areas
        self.prev_height = 0
        self.prev_width = 0
        self.prev_bars = None
        
        # Mode changed flag
        self.mode_changed = False
        
        # Clear once at start
        self.stdscr.clear()
        self.stdscr.refresh()
    
    def _init_colors(self):
        """Initialize color pairs."""
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLUE, -1)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_RED, -1)
            curses.init_pair(6, curses.COLOR_MAGENTA, -1)
            curses.init_pair(7, curses.COLOR_WHITE, -1)
    
    def _get_color(self, level: float) -> int:
        """Get color based on amplitude level."""
        if not curses.has_colors():
            return 0
        
        level = max(0, min(1, level))
        
        if level < 0.2:
            return curses.color_pair(1)
        elif level < 0.4:
            return curses.color_pair(2)
        elif level < 0.6:
            return curses.color_pair(3)
        elif level < 0.8:
            return curses.color_pair(4)
        else:
            return curses.color_pair(5)
    
    def _apply_smoothing(self, values: np.ndarray) -> np.ndarray:
        """Apply temporal smoothing."""
        if self.previous_values is None or len(self.previous_values) != len(values):
            self.previous_values = values
            return values
        
        smoothed = (self.smoothing_factor * self.previous_values + 
                   (1 - self.smoothing_factor) * values)
        self.previous_values = smoothed
        return smoothed
    
    def _compute_frequency_bars(self, audio_data: np.ndarray, num_bars: int):
        """Compute frequency bars with logarithmic spacing for full spectrum."""
        # Compute FFT
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)), 'constant')
        
        fft = np.fft.rfft(audio_data[:self.fft_size])
        magnitude = np.abs(fft)
        
        # Use logarithmic frequency scaling for better distribution
        # This shows both bass and treble properly
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / 44100)
        
        # Create logarithmic bins from 20 Hz to 20 kHz
        min_freq = 20
        max_freq = 20000
        
        # Logarithmic spacing
        log_bins = np.logspace(np.log10(min_freq), np.log10(max_freq), num_bars + 1)
        
        bar_heights = []
        for i in range(num_bars):
            # Find frequencies in this bin
            freq_mask = (freqs >= log_bins[i]) & (freqs < log_bins[i + 1])
            if np.any(freq_mask):
                # Use max instead of mean for more responsive visualization
                bar_heights.append(np.max(magnitude[freq_mask]))
            else:
                bar_heights.append(0)
        
        bar_heights = np.array(bar_heights)
        
        # Normalize with some boost for visibility
        if np.max(bar_heights) > 0:
            bar_heights = bar_heights / np.max(bar_heights)
            # Apply a slight curve for better visibility of lower levels
            bar_heights = np.power(bar_heights, 0.7)
        
        return bar_heights
    
    def _draw_bars(self, audio_data: np.ndarray, height: int, width: int, y_offset: int):
        """Draw bar visualization with selective updates."""
        bar_heights = self._compute_frequency_bars(audio_data, width)
        bar_heights = self._apply_smoothing(bar_heights)
        
        # Convert to integer heights
        current_bars = (bar_heights * height).astype(int)
        
        # Force full redraw if mode changed
        if self.mode_changed or self.prev_bars is None or len(self.prev_bars) != len(current_bars):
            self.prev_bars = np.zeros_like(current_bars)
            self.mode_changed = False
        
        for col in range(min(width, len(current_bars))):
            cur_height = current_bars[col]
            prev_height = self.prev_bars[col]
            
            # Update if changed or significant
            if abs(cur_height - prev_height) > 0:
                # Clear the old bar
                for row in range(height):
                    try:
                        self.stdscr.addch(row + y_offset, col, ord(' '))
                    except curses.error:
                        pass
                
                # Draw new bar
                height_ratio = bar_heights[col]
                color = self._get_color(height_ratio)
                
                for row in range(height):
                    if height - row <= cur_height:
                        try:
                            self.stdscr.addch(row + y_offset, col, ord('█'), color)
                        except curses.error:
                            pass
        
        self.prev_bars = current_bars
    
    def draw_header(self, width: int, audio_active: bool, device_name: str = ""):
        """Draw header (only when needed)."""
        height, _ = self.stdscr.getmaxyx()
        
        # Only redraw header if size changed
        if width != self.prev_width or height != self.prev_height:
            try:
                # Clear header area
                self.stdscr.move(0, 0)
                self.stdscr.clrtoeol()
                self.stdscr.move(1, 0)
                self.stdscr.clrtoeol()
                
                title = "♪ CLI AUDIO VISUALIZER ♪"
                self.stdscr.addstr(0, (width - len(title)) // 2, title, 
                                 curses.color_pair(6) | curses.A_BOLD)
                
                mode_text = f"Mode: {self.modes[self.current_mode].upper()}"
                self.stdscr.addstr(1, 2, mode_text, curses.color_pair(2))
                
                if device_name and len(device_name) < width - 20:
                    dev_text = f"Source: {device_name[:width-30]}"
                    self.stdscr.addstr(1, 20, dev_text, curses.color_pair(7) | curses.A_DIM)
            except curses.error:
                pass
        
        # Always update audio status indicator
        try:
            status = "●" if audio_active else "○"
            status_color = curses.color_pair(3) if audio_active else curses.color_pair(5)
            self.stdscr.addstr(1, width - 10, f"Audio {status}", status_color)
        except curses.error:
            pass
    
    def draw_footer(self, width: int, height: int):
        """Draw footer (only when needed)."""
        # Only redraw footer if size changed
        if width != self.prev_width or height != self.prev_height:
            try:
                self.stdscr.move(height - 1, 0)
                self.stdscr.clrtoeol()
                
                controls = "[SPACE] Change Mode  [Q] Quit"
                self.stdscr.addstr(height - 1, (width - len(controls)) // 2, controls,
                                 curses.color_pair(4))
            except curses.error:
                pass
    
    def _draw_mirror_circular(self, audio_data: np.ndarray, height: int, width: int, y_offset: int):
        """Draw mirror circular visualization like YouTube videos."""
        # Get frequency bars for half the width
        num_bars = width // 2
        bar_heights = self._compute_frequency_bars(audio_data, num_bars)
        bar_heights = self._apply_smoothing(bar_heights)
        
        # Mirror visualization - bars grow from center
        center = height // 2
        
        # Clear previous if mode changed
        if self.mode_changed:
            for row in range(height):
                for col in range(width):
                    try:
                        self.stdscr.addch(row + y_offset, col, ord(' '))
                    except curses.error:
                        pass
            self.mode_changed = False
        
        # Draw left half (mirrored from center)
        for i in range(num_bars):
            bar_height = int(bar_heights[i] * center)
            color = self._get_color(bar_heights[i])
            
            col = num_bars - i - 1  # Mirror position
            
            # Draw from center outward (both up and down)
            for offset in range(bar_height):
                # Upper half
                try:
                    self.stdscr.addch(center - offset + y_offset, col, ord('█'), color)
                except curses.error:
                    pass
                # Lower half (mirror)
                try:
                    self.stdscr.addch(center + offset + y_offset, col, ord('█'), color)
                except curses.error:
                    pass
            
            # Clear above/below if bar shrunk
            for offset in range(bar_height, center):
                try:
                    self.stdscr.addch(center - offset + y_offset, col, ord(' '))
                except curses.error:
                    pass
                try:
                    self.stdscr.addch(center + offset + y_offset, col, ord(' '))
                except curses.error:
                    pass
        
        # Draw right half (mirrored)
        for i in range(num_bars):
            bar_height = int(bar_heights[i] * center)
            color = self._get_color(bar_heights[i])
            
            col = num_bars + i
            if col >= width:
                break
            
            # Draw from center outward (both up and down)
            for offset in range(bar_height):
                try:
                    self.stdscr.addch(center - offset + y_offset, col, ord('█'), color)
                except curses.error:
                    pass
                try:
                    self.stdscr.addch(center + offset + y_offset, col, ord('█'), color)
                except curses.error:
                    pass
            
            # Clear above/below if bar shrunk
            for offset in range(bar_height, center):
                try:
                    self.stdscr.addch(center - offset + y_offset, col, ord(' '))
                except curses.error:
                    pass
                try:
                    self.stdscr.addch(center + offset + y_offset, col, ord(' '))
                except curses.error:
                    pass
    
    def visualize(self, audio_data: Optional[np.ndarray], device_name: str = "Unknown"):
        """Main visualization with selective updates."""
        try:
            height, width = self.stdscr.getmaxyx()
            
            # Check if audio is active
            audio_active = audio_data is not None and len(audio_data) > 0 and np.max(np.abs(audio_data)) > 0.001
            
            # Draw header and footer (only updates if needed)
            self.draw_header(width, audio_active, device_name)
            self.draw_footer(width, height)
            
            # Visualization area
            viz_height = height - 4
            viz_width = width
            y_offset = 3
            
            # Draw visualization (only updates changed areas)
            if audio_data is not None and len(audio_data) > 0:
                mode = self.modes[self.current_mode]
                
                if mode == "bars":
                    self._draw_bars(audio_data, viz_height, viz_width, y_offset)
                elif mode == "spectrum":
                    self._draw_bars(audio_data, viz_height, viz_width, y_offset)
                elif mode == "mirror_circular":
                    self._draw_mirror_circular(audio_data, viz_height, viz_width, y_offset)
                elif mode == "waveform":
                    self._draw_bars(audio_data, viz_height, viz_width, y_offset)
            
            # Store current dimensions
            self.prev_height = height
            self.prev_width = width
            
            # Refresh only once per frame
            self.stdscr.refresh()
            
        except curses.error:
            pass
    
    def handle_input(self) -> bool:
        """Handle keyboard input."""
        try:
            key = self.stdscr.getch()
            
            # Check for no input
            if key == -1 or key == curses.ERR:
                return True
            
            if key == ord('q') or key == ord('Q') or key == 27:
                return False
            elif key == ord(' '):
                # Change mode
                old_mode = self.current_mode
                self.current_mode = (self.current_mode + 1) % len(self.modes)
                self.previous_values = None
                self.prev_bars = None
                self.mode_changed = True
                
                # Clear visualization area
                height, width = self.stdscr.getmaxyx()
                for row in range(3, height - 1):
                    try:
                        self.stdscr.move(row, 0)
                        self.stdscr.clrtoeol()
                    except curses.error:
                        pass
                
                # Force header redraw to show new mode
                self.prev_width = 0
                self.prev_height = 0
            
        except curses.error:
            pass
        
        return True