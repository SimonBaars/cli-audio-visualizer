"""Smooth curses-based visualizer with multiple distinct modes and color schemes."""

import curses
import numpy as np
from typing import Optional
import math


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
    
    def _compute_frequency_bars(self, audio_data: np.ndarray, num_bars: int):
        """Compute frequency bars with logarithmic spacing."""
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)), 'constant')
        
        fft = np.fft.rfft(audio_data[:self.fft_size])
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(self.fft_size, 1.0 / 44100)
        
        # Logarithmic bins
        log_bins = np.logspace(np.log10(20), np.log10(20000), num_bars + 1)
        
        bar_heights = []
        for i in range(num_bars):
            freq_mask = (freqs >= log_bins[i]) & (freqs < log_bins[i + 1])
            if np.any(freq_mask):
                bar_heights.append(np.max(magnitude[freq_mask]))
            else:
                bar_heights.append(0)
        
        bar_heights = np.array(bar_heights)
        if np.max(bar_heights) > 0:
            bar_heights = bar_heights / np.max(bar_heights)
            bar_heights = np.power(bar_heights, 0.7)
        
        return bar_heights
    
    def _clear_area(self, y_start: int, height: int, width: int):
        """Clear a rectangular area."""
        for row in range(height):
            try:
                self.stdscr.move(y_start + row, 0)
                self.stdscr.clrtoeol()
            except curses.error:
                pass
    
    def _draw_bars(self, audio_data: np.ndarray, height: int, width: int, y_offset: int):
        """Draw classic frequency bars."""
        bar_heights = self._compute_frequency_bars(audio_data, width)
        bar_heights = self._apply_smoothing(bar_heights)
        current_bars = (bar_heights * height).astype(int)
        
        # Full clear on mode change
        if self.mode_changed:
            self._clear_area(y_offset, height, width)
            self.prev_bars = None
            self.mode_changed = False
        
        if self.prev_bars is None or len(self.prev_bars) != len(current_bars):
            self.prev_bars = np.zeros_like(current_bars)
        
        for col in range(min(width, len(current_bars))):
            cur_height = current_bars[col]
            prev_height = self.prev_bars[col]
            
            if cur_height != prev_height:
                # Clear the entire column first
                for row in range(height):
                    try:
                        self.stdscr.addch(row + y_offset, col, ord(' '))
                    except curses.error:
                        pass
                
                # Draw new bar from bottom up
                height_ratio = bar_heights[col]
                position = col / max(1, width - 1)
                color = self._get_color(height_ratio, position)
                
                for row in range(height):
                    if height - row <= cur_height:
                        try:
                            self.stdscr.addch(row + y_offset, col, ord('█'), color)
                        except curses.error:
                            pass
        
        self.prev_bars = current_bars.copy()
    
    def _draw_spectrum(self, audio_data: np.ndarray, height: int, width: int, y_offset: int):
        """Draw spectrum with block gradient."""
        bar_heights = self._compute_frequency_bars(audio_data, width)
        bar_heights = self._apply_smoothing(bar_heights)
        
        if self.mode_changed:
            self._clear_area(y_offset, height, width)
            self.mode_changed = False
        
        block_chars = ' ▁▂▃▄▅▆▇█'
        
        for col in range(width):
            height_ratio = bar_heights[col]
            bar_height = int(height_ratio * height)
            position = col / max(1, width - 1)
            
            for row in range(height):
                if height - row <= bar_height:
                    # Use gradient blocks
                    block_progress = (height - row) / max(1, bar_height)
                    char_idx = int(block_progress * (len(block_chars) - 1))
                    char = block_chars[min(char_idx, len(block_chars) - 1)]
                    color = self._get_color(height_ratio, position)
                    try:
                        self.stdscr.addch(row + y_offset, col, ord(char), color)
                    except curses.error:
                        pass
                else:
                    try:
                        self.stdscr.addch(row + y_offset, col, ord(' '))
                    except curses.error:
                        pass
    
    def _draw_waveform(self, audio_data: np.ndarray, height: int, width: int, y_offset: int):
        """Draw actual time-domain waveform."""
        if len(audio_data) > width:
            step = len(audio_data) // width
            waveform = audio_data[::step][:width]
        else:
            waveform = np.pad(audio_data, (0, width - len(audio_data)), 'constant')
        
        waveform = self._apply_smoothing(waveform, use_waveform=True)
        
        if np.max(np.abs(waveform)) > 0:
            waveform = waveform / np.max(np.abs(waveform))
        
        if self.mode_changed:
            self._clear_area(y_offset, height, width)
            self.mode_changed = False
        
        middle = height // 2
        
        # Clear and draw
        for col in range(min(width, len(waveform))):
            wave_value = waveform[col]
            wave_height = int(wave_value * middle)
            target_row = middle - wave_height
            
            # Clear column
            for row in range(height):
                try:
                    if row == middle:
                        self.stdscr.addch(row + y_offset, col, ord('─'), curses.color_pair(7) | curses.A_DIM)
                    elif row == target_row:
                        color = self._get_color(abs(wave_value))
                        self.stdscr.addch(row + y_offset, col, ord('█'), color)
                    else:
                        self.stdscr.addch(row + y_offset, col, ord(' '))
                except curses.error:
                    pass
    
    def _draw_mirror_circular(self, audio_data: np.ndarray, height: int, width: int, y_offset: int):
        """Draw mirror circular (vertical bars from center)."""
        num_bars = width // 2
        bar_heights = self._compute_frequency_bars(audio_data, num_bars)
        bar_heights = self._apply_smoothing(bar_heights)
        center = height // 2
        
        if self.mode_changed:
            self._clear_area(y_offset, height, width)
            self.mode_changed = False
        
        for i in range(num_bars):
            bar_height = int(bar_heights[i] * center)
            position = i / max(1, num_bars - 1)
            color = self._get_color(bar_heights[i], position)
            
            # Left half
            col_left = num_bars - i - 1
            # Right half
            col_right = num_bars + i
            
            for col in [col_left, col_right]:
                if col >= width:
                    continue
                
                # Clear column
                for row in range(height):
                    try:
                        self.stdscr.addch(row + y_offset, col, ord(' '))
                    except curses.error:
                        pass
                
                # Draw from center outward
                for offset in range(bar_height):
                    try:
                        self.stdscr.addch(center - offset + y_offset, col, ord('█'), color)
                        self.stdscr.addch(center + offset + y_offset, col, ord('█'), color)
                    except curses.error:
                        pass
    
    def _draw_circular_wave(self, audio_data: np.ndarray, height: int, width: int, y_offset: int):
        """Draw actual circle with mirrored waveform."""
        # Clear area every frame for this mode
        self._clear_area(y_offset, height, width)
        
        # Get waveform
        num_points = 100  # Fixed number of points for smooth circle
        if len(audio_data) > num_points:
            step = len(audio_data) // num_points
            waveform = audio_data[::step][:num_points]
        else:
            waveform = np.pad(audio_data, (0, num_points - len(audio_data)), 'constant')
        
        waveform = self._apply_smoothing(waveform, use_waveform=True)
        if np.max(np.abs(waveform)) > 0:
            waveform = waveform / np.max(np.abs(waveform))
        
        center_y = height // 2
        center_x = width // 2
        radius = min(height // 2 - 3, width // 4)
        
        # Draw full circle (0 to 2π) with left-right mirroring
        for i in range(num_points):
            # Left half (0 to π)
            angle = (i / num_points) * np.pi
            wave_offset = waveform[i] * radius * 0.6
            
            # Calculate modulated radius
            mod_radius = radius + wave_offset
            
            # Top half
            x_left = int(center_x - mod_radius * np.cos(angle))
            y_top = int(center_y - mod_radius * np.sin(angle))
            
            # Bottom half (mirror)
            y_bottom = int(center_y + mod_radius * np.sin(angle))
            
            position = i / max(1, num_points - 1)
            color = self._get_color(abs(wave_offset / radius), position)
            
            # Draw left side (top and bottom)
            for y in [y_top, y_bottom]:
                if 0 <= x_left < width and 0 <= y < height:
                    try:
                        self.stdscr.addch(y + y_offset, x_left, ord('●'), color)
                    except curses.error:
                        pass
            
            # Right side (mirror of left)
            x_right = center_x + (center_x - x_left)
            for y in [y_top, y_bottom]:
                if 0 <= x_right < width and 0 <= y < height:
                    try:
                        self.stdscr.addch(y + y_offset, x_right, ord('●'), color)
                    except curses.error:
                        pass
    
    def _draw_levels(self, audio_data: np.ndarray, height: int, width: int, y_offset: int):
        """Draw level meters (VU meter style)."""
        bar_heights = self._compute_frequency_bars(audio_data, 20)  # 20 frequency bands
        bar_heights = self._apply_smoothing(bar_heights)
        
        if self.mode_changed:
            self._clear_area(y_offset, height, width)
            self.mode_changed = False
        
        bands_per_row = 4
        rows = (len(bar_heights) + bands_per_row - 1) // bands_per_row
        bar_width = width // bands_per_row - 2
        
        for idx, height_val in enumerate(bar_heights):
            row = idx // bands_per_row
            col_start = (idx % bands_per_row) * (bar_width + 2)
            
            if row >= height:
                break
            
            bar_length = int(height_val * bar_width)
            position = idx / max(1, len(bar_heights) - 1)
            
            # Draw bar
            try:
                for x in range(bar_length):
                    progress = x / max(1, bar_width - 1)
                    color = self._get_color(progress, position)
                    self.stdscr.addch(row * 2 + y_offset, col_start + x, ord('█'), color)
                
                # Clear rest
                for x in range(bar_length, bar_width):
                    self.stdscr.addch(row * 2 + y_offset, col_start + x, ord('░'), curses.color_pair(7) | curses.A_DIM)
            except curses.error:
                pass
    
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
            
            self.draw_header(width, audio_active, device_name)
            self.draw_footer(width, height)
            
            viz_height = height - 4
            viz_width = width
            y_offset = 3
            
            if audio_data is not None and len(audio_data) > 0:
                mode = self.modes[self.current_mode]
                
                if mode == "bars":
                    self._draw_bars(audio_data, viz_height, viz_width, y_offset)
                elif mode == "spectrum":
                    self._draw_spectrum(audio_data, viz_height, viz_width, y_offset)
                elif mode == "waveform":
                    self._draw_waveform(audio_data, viz_height, viz_width, y_offset)
                elif mode == "mirror_circular":
                    self._draw_mirror_circular(audio_data, viz_height, viz_width, y_offset)
                elif mode == "circular_wave":
                    self._draw_circular_wave(audio_data, viz_height, viz_width, y_offset)
                elif mode == "levels":
                    self._draw_levels(audio_data, viz_height, viz_width, y_offset)
            
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