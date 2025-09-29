"""Stable curses-based terminal UI for audio visualization."""

import curses
import numpy as np
import time
from typing import Optional, Tuple
import math


class CursesVisualizer:
    """Stable terminal visualizer using curses."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.current_mode = 0
        self.modes = ["bars", "spectrum", "waveform", "blocks"]
        
        # Initialize curses
        curses.curs_set(0)  # Hide cursor
        curses.use_default_colors()
        stdscr.nodelay(1)  # Non-blocking input
        stdscr.timeout(16)  # ~60 FPS
        
        # Initialize color pairs
        self._init_colors()
        
        # Smoothing
        self.smoothing_factor = 0.75
        self.previous_values = None
        
        # FFT parameters
        self.fft_size = 2048
        
    def _init_colors(self):
        """Initialize color pairs for the visualizer."""
        if curses.has_colors():
            curses.start_color()
            # Define color pairs (foreground, background)
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
            return curses.color_pair(1)  # Blue
        elif level < 0.4:
            return curses.color_pair(2)  # Cyan
        elif level < 0.6:
            return curses.color_pair(3)  # Green
        elif level < 0.8:
            return curses.color_pair(4)  # Yellow
        else:
            return curses.color_pair(5)  # Red
    
    def _get_spectrum_color(self, position: float, level: float) -> int:
        """Get color based on frequency position in spectrum."""
        if not curses.has_colors():
            return 0
        
        position = max(0, min(1, position))
        
        if position < 0.15:
            return curses.color_pair(5)  # Red (bass)
        elif position < 0.35:
            return curses.color_pair(4)  # Yellow
        elif position < 0.55:
            return curses.color_pair(3)  # Green (mids)
        elif position < 0.75:
            return curses.color_pair(2)  # Cyan
        else:
            return curses.color_pair(1)  # Blue (treble)
    
    def _apply_smoothing(self, values: np.ndarray) -> np.ndarray:
        """Apply temporal smoothing to reduce flickering."""
        if self.previous_values is None:
            self.previous_values = values
            return values
        
        if len(self.previous_values) != len(values):
            self.previous_values = values
            return values
        
        smoothed = (self.smoothing_factor * self.previous_values + 
                   (1 - self.smoothing_factor) * values)
        self.previous_values = smoothed
        return smoothed
    
    def _draw_bars(self, audio_data: np.ndarray, height: int, width: int):
        """Draw bar visualization."""
        # Compute FFT
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)), 'constant')
        
        fft = np.fft.rfft(audio_data[:self.fft_size])
        magnitude = np.abs(fft)
        
        # Focus on lower frequencies (more visible music)
        magnitude = magnitude[:len(magnitude)//2]
        
        # Reduce to width
        bars_per_bin = max(1, len(magnitude) // width)
        bar_heights = []
        
        for i in range(width):
            start_idx = i * bars_per_bin
            end_idx = min(start_idx + bars_per_bin, len(magnitude))
            if start_idx < len(magnitude):
                bar_heights.append(np.mean(magnitude[start_idx:end_idx]))
            else:
                bar_heights.append(0)
        
        # Normalize and apply smoothing
        bar_heights = np.array(bar_heights)
        if np.max(bar_heights) > 0:
            bar_heights = bar_heights / np.max(bar_heights)
        
        bar_heights = self._apply_smoothing(bar_heights)
        
        # Draw bars
        bar_chars = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
        for row in range(height):
            for col in range(width):
                if col >= len(bar_heights):
                    continue
                
                height_ratio = bar_heights[col]
                bar_height = int(height_ratio * height)
                
                # Calculate which character to use
                if height - row <= bar_height:
                    color = self._get_color(height_ratio)
                    try:
                        self.stdscr.addch(row + 3, col, ord('█'), color)
                    except curses.error:
                        pass  # Edge of screen
    
    def _draw_spectrum(self, audio_data: np.ndarray, height: int, width: int):
        """Draw spectrum analyzer."""
        # Compute FFT
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)), 'constant')
        
        fft = np.fft.rfft(audio_data[:self.fft_size])
        magnitude = np.abs(fft)
        
        # Convert to dB scale and focus on audible range
        magnitude = magnitude[:len(magnitude)//2]
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        
        # Reduce to width
        bins_per_col = max(1, len(magnitude_db) // width)
        spectrum = []
        
        for i in range(width):
            start_idx = i * bins_per_col
            end_idx = min(start_idx + bins_per_col, len(magnitude_db))
            if start_idx < len(magnitude_db):
                spectrum.append(np.mean(magnitude_db[start_idx:end_idx]))
            else:
                spectrum.append(-80)
        
        # Normalize
        spectrum = np.array(spectrum)
        spectrum = np.clip((spectrum + 80) / 60, 0, 1)
        spectrum = self._apply_smoothing(spectrum)
        
        # Draw spectrum
        for row in range(height):
            for col in range(width):
                if col >= len(spectrum):
                    continue
                
                height_ratio = spectrum[col]
                bar_height = int(height_ratio * height)
                
                if height - row <= bar_height:
                    position_ratio = col / max(1, width - 1)
                    color = self._get_spectrum_color(position_ratio, height_ratio)
                    try:
                        self.stdscr.addch(row + 3, col, ord('▆'), color)
                    except curses.error:
                        pass
    
    def _draw_waveform(self, audio_data: np.ndarray, height: int, width: int):
        """Draw waveform visualization."""
        # Downsample to width
        if len(audio_data) > width:
            step = len(audio_data) // width
            waveform = audio_data[::step][:width]
        else:
            waveform = np.pad(audio_data, (0, width - len(audio_data)), 'constant')
        
        waveform = self._apply_smoothing(waveform)
        
        # Normalize
        if np.max(np.abs(waveform)) > 0:
            waveform = waveform / np.max(np.abs(waveform))
        
        middle = height // 2
        
        # Draw waveform
        for col in range(min(width, len(waveform))):
            wave_value = waveform[col]
            wave_height = int(wave_value * middle)
            row = middle - wave_height + 3
            
            if 3 <= row < height + 3:
                color = self._get_color(abs(wave_value))
                try:
                    self.stdscr.addch(row, col, ord('█'), color)
                except curses.error:
                    pass
        
        # Draw center line
        try:
            for col in range(width):
                self.stdscr.addch(middle + 3, col, ord('─'), curses.color_pair(7) | curses.A_DIM)
        except curses.error:
            pass
    
    def _draw_blocks(self, audio_data: np.ndarray, height: int, width: int):
        """Draw block visualization with gradient characters."""
        # Similar to bars but with gradient blocks
        if len(audio_data) < self.fft_size:
            audio_data = np.pad(audio_data, (0, self.fft_size - len(audio_data)), 'constant')
        
        fft = np.fft.rfft(audio_data[:self.fft_size])
        magnitude = np.abs(fft)
        magnitude = magnitude[:len(magnitude)//2]
        
        # Reduce to width
        blocks_per_bin = max(1, len(magnitude) // width)
        block_heights = []
        
        for i in range(width):
            start_idx = i * blocks_per_bin
            end_idx = min(start_idx + blocks_per_bin, len(magnitude))
            if start_idx < len(magnitude):
                block_heights.append(np.mean(magnitude[start_idx:end_idx]))
            else:
                block_heights.append(0)
        
        # Normalize
        block_heights = np.array(block_heights)
        if np.max(block_heights) > 0:
            block_heights = block_heights / np.max(block_heights)
        
        block_heights = self._apply_smoothing(block_heights)
        
        # Block gradient characters
        block_chars = ' ▁▂▃▄▅▆▇█'
        
        for row in range(height):
            for col in range(width):
                if col >= len(block_heights):
                    continue
                
                height_ratio = block_heights[col]
                blocks_high = height_ratio * height
                current_height = height - row
                
                if current_height <= blocks_high:
                    # Calculate which block character to use
                    block_fraction = blocks_high - current_height + 1
                    char_idx = min(int(block_fraction * len(block_chars)), len(block_chars) - 1)
                    char = block_chars[char_idx]
                    color = self._get_color(height_ratio)
                    
                    try:
                        self.stdscr.addch(row + 3, col, ord(char), color)
                    except curses.error:
                        pass
    
    def draw_header(self, width: int, audio_active: bool, device_name: str = ""):
        """Draw header with title and status."""
        try:
            title = "♪ CLI AUDIO VISUALIZER ♪"
            self.stdscr.addstr(0, (width - len(title)) // 2, title, 
                             curses.color_pair(6) | curses.A_BOLD)
            
            mode_text = f"Mode: {self.modes[self.current_mode].upper()}"
            status = "●" if audio_active else "○"
            status_color = curses.color_pair(3) if audio_active else curses.color_pair(5)
            
            self.stdscr.addstr(1, 2, mode_text, curses.color_pair(2))
            self.stdscr.addstr(1, width - 12, f"Audio {status}", status_color)
            
            if device_name:
                dev_text = f"Device: {device_name[:width-20]}"
                self.stdscr.addstr(1, 20, dev_text, curses.color_pair(7) | curses.A_DIM)
            
        except curses.error:
            pass
    
    def draw_footer(self, width: int, height: int):
        """Draw footer with controls."""
        try:
            controls = "[SPACE] Change Mode  [Q] Quit"
            self.stdscr.addstr(height - 1, (width - len(controls)) // 2, controls,
                             curses.color_pair(4))
        except curses.error:
            pass
    
    def visualize(self, audio_data: Optional[np.ndarray], device_name: str = "Unknown"):
        """Main visualization function."""
        try:
            self.stdscr.erase()
            height, width = self.stdscr.getmaxyx()
            
            # Check if audio is active (has signal above threshold)
            audio_active = audio_data is not None and len(audio_data) > 0 and np.max(np.abs(audio_data)) > 0.001
            
            # Draw header
            self.draw_header(width, audio_active, device_name)
            
            # Draw visualization area
            viz_height = height - 4
            viz_width = width
            
            # Always visualize, even if no signal - just shows empty/flat
            # This prevents the "Waiting for audio" flashing
            if audio_data is not None and len(audio_data) > 0:
                mode = self.modes[self.current_mode]
                
                if mode == "bars":
                    self._draw_bars(audio_data, viz_height, viz_width)
                elif mode == "spectrum":
                    self._draw_spectrum(audio_data, viz_height, viz_width)
                elif mode == "waveform":
                    self._draw_waveform(audio_data, viz_height, viz_width)
                elif mode == "blocks":
                    self._draw_blocks(audio_data, viz_height, viz_width)
            
            # Draw footer
            self.draw_footer(width, height)
            
            # Refresh screen
            self.stdscr.refresh()
            
        except curses.error:
            pass  # Ignore terminal size errors
    
    def handle_input(self) -> bool:
        """Handle keyboard input. Returns True if should continue running."""
        try:
            key = self.stdscr.getch()
            
            if key == ord('q') or key == ord('Q') or key == 27:  # q or ESC
                return False
            elif key == ord(' '):  # Space
                self.current_mode = (self.current_mode + 1) % len(self.modes)
                self.previous_values = None  # Reset smoothing
            
        except curses.error:
            pass
        
        return True