"""Visualization engine with multiple visualization types."""

import numpy as np
from rich.console import Console
from rich.text import Text
from rich import box
from rich.panel import Panel
from rich.columns import Columns
import math
import time
from typing import List, Tuple

class Visualizer:
    """Main visualization engine with multiple visualization modes."""
    
    def __init__(self, width: int = 80, height: int = 20):
        self.console = Console()
        self.width = width
        self.height = height
        self.current_mode = "bars"
        self.modes = ["bars", "waveform", "spectrum", "dots", "blocks"]
        self.colors = [
            "red", "yellow", "green", "cyan", "blue", "magenta",
            "bright_red", "bright_yellow", "bright_green", 
            "bright_cyan", "bright_blue", "bright_magenta"
        ]
        
        # FFT parameters
        self.fft_size = 1024
        self.freq_bins = self.width // 2
        
        # Smoothing parameters
        self.smoothing_factor = 0.7
        self.previous_values = np.zeros(self.width)
        
    def cycle_mode(self):
        """Cycle to the next visualization mode."""
        current_index = self.modes.index(self.current_mode)
        self.current_mode = self.modes[(current_index + 1) % len(self.modes)]
        return self.current_mode
    
    def set_mode(self, mode: str):
        """Set the visualization mode."""
        if mode in self.modes:
            self.current_mode = mode
    
    def _apply_smoothing(self, values: np.ndarray) -> np.ndarray:
        """Apply smoothing to reduce flickering."""
        self.previous_values = (self.smoothing_factor * self.previous_values + 
                               (1 - self.smoothing_factor) * values)
        return self.previous_values
    
    def _get_color_for_level(self, level: float) -> str:
        """Get color based on amplitude level."""
        if level < 0.3:
            return "blue"
        elif level < 0.6:
            return "green"
        elif level < 0.8:
            return "yellow"
        else:
            return "red"
    
    def _visualize_bars(self, audio_data: np.ndarray) -> str:
        """Create bar visualization."""
        # Compute FFT
        fft = np.fft.rfft(audio_data, n=self.fft_size)
        magnitude = np.abs(fft)
        
        # Reduce to desired number of bars
        bars_per_bin = len(magnitude) // self.width
        if bars_per_bin == 0:
            bars_per_bin = 1
        
        bar_heights = []
        for i in range(self.width):
            start_idx = i * bars_per_bin
            end_idx = min(start_idx + bars_per_bin, len(magnitude))
            if start_idx < len(magnitude):
                bar_heights.append(np.mean(magnitude[start_idx:end_idx]))
            else:
                bar_heights.append(0)
        
        # Normalize and apply smoothing
        if len(bar_heights) > 0:
            max_height = max(bar_heights) if max(bar_heights) > 0 else 1
            normalized_heights = np.array(bar_heights) / max_height
            smoothed_heights = self._apply_smoothing(normalized_heights)
        else:
            smoothed_heights = np.zeros(self.width)
        
        # Create bars
        lines = []
        for row in range(self.height - 1, -1, -1):
            line = Text()
            for col in range(self.width):
                height_ratio = smoothed_heights[col]
                bar_height = int(height_ratio * self.height)
                
                if row < bar_height:
                    color = self._get_color_for_level(height_ratio)
                    line.append("█", style=color)
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def _visualize_waveform(self, audio_data: np.ndarray) -> str:
        """Create waveform visualization."""
        # Downsample to fit width
        if len(audio_data) > self.width:
            step = len(audio_data) // self.width
            waveform = audio_data[::step][:self.width]
        else:
            waveform = np.pad(audio_data, (0, self.width - len(audio_data)), 'constant')
        
        # Apply smoothing
        waveform = self._apply_smoothing(waveform)
        
        # Normalize to height
        if np.max(np.abs(waveform)) > 0:
            waveform = waveform / np.max(np.abs(waveform))
        
        # Create waveform display
        lines = []
        middle = self.height // 2
        
        for row in range(self.height):
            line = Text()
            for col in range(self.width):
                wave_value = waveform[col]
                wave_height = int(wave_value * middle)
                current_row = row - middle
                
                if abs(current_row - wave_height) <= 1:
                    color = self._get_color_for_level(abs(wave_value))
                    line.append("█", style=color)
                elif row == middle:
                    line.append("─", style="dim white")
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def _visualize_spectrum(self, audio_data: np.ndarray) -> str:
        """Create spectrum analyzer visualization."""
        # Compute FFT
        fft = np.fft.rfft(audio_data, n=self.fft_size)
        magnitude = np.abs(fft)
        
        # Convert to dB scale
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        
        # Reduce to desired width
        bins_per_col = len(magnitude_db) // self.width
        if bins_per_col == 0:
            bins_per_col = 1
        
        spectrum = []
        for i in range(self.width):
            start_idx = i * bins_per_col
            end_idx = min(start_idx + bins_per_col, len(magnitude_db))
            if start_idx < len(magnitude_db):
                spectrum.append(np.mean(magnitude_db[start_idx:end_idx]))
            else:
                spectrum.append(-80)  # Very low value
        
        # Normalize
        spectrum = np.array(spectrum)
        spectrum = np.clip((spectrum + 80) / 80, 0, 1)  # Normalize from -80dB to 0dB
        spectrum = self._apply_smoothing(spectrum)
        
        # Create spectrum display
        lines = []
        for row in range(self.height - 1, -1, -1):
            line = Text()
            for col in range(self.width):
                height_ratio = spectrum[col]
                bar_height = int(height_ratio * self.height)
                
                if row < bar_height:
                    # Use different colors for different frequency ranges
                    freq_color_index = col // (self.width // len(self.colors))
                    freq_color_index = min(freq_color_index, len(self.colors) - 1)
                    color = self.colors[freq_color_index]
                    line.append("▆", style=color)
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def _visualize_dots(self, audio_data: np.ndarray) -> str:
        """Create dot matrix visualization."""
        # Compute FFT for frequency data
        fft = np.fft.rfft(audio_data, n=self.fft_size)
        magnitude = np.abs(fft)
        
        # Create a 2D representation
        dots_width = self.width
        dots_height = self.height
        
        # Map frequency bins to grid
        freq_per_col = len(magnitude) // dots_width
        time_chunks = len(audio_data) // dots_height
        
        lines = []
        for row in range(dots_height):
            line = Text()
            for col in range(dots_width):
                # Get magnitude for this frequency bin
                freq_idx = col * freq_per_col
                if freq_idx < len(magnitude):
                    intensity = magnitude[freq_idx]
                    # Get time-domain info for this row
                    time_idx = row * time_chunks
                    if time_idx < len(audio_data):
                        time_intensity = abs(audio_data[time_idx])
                        combined_intensity = intensity * time_intensity * 1000
                        
                        if combined_intensity > 0.1:
                            color = self._get_color_for_level(min(combined_intensity, 1.0))
                            line.append("●", style=color)
                        else:
                            line.append("·", style="dim white")
                    else:
                        line.append(" ")
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def _visualize_blocks(self, audio_data: np.ndarray) -> str:
        """Create block visualization."""
        # Similar to bars but with block characters
        fft = np.fft.rfft(audio_data, n=self.fft_size)
        magnitude = np.abs(fft)
        
        # Reduce to desired number of blocks
        blocks_per_bin = len(magnitude) // self.width
        if blocks_per_bin == 0:
            blocks_per_bin = 1
        
        block_heights = []
        for i in range(self.width):
            start_idx = i * blocks_per_bin
            end_idx = min(start_idx + blocks_per_bin, len(magnitude))
            if start_idx < len(magnitude):
                block_heights.append(np.mean(magnitude[start_idx:end_idx]))
            else:
                block_heights.append(0)
        
        # Normalize and apply smoothing
        if len(block_heights) > 0:
            max_height = max(block_heights) if max(block_heights) > 0 else 1
            normalized_heights = np.array(block_heights) / max_height
            smoothed_heights = self._apply_smoothing(normalized_heights)
        else:
            smoothed_heights = np.zeros(self.width)
        
        # Block characters for different heights
        block_chars = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        lines = []
        for row in range(self.height - 1, -1, -1):
            line = Text()
            for col in range(self.width):
                height_ratio = smoothed_heights[col]
                total_blocks = int(height_ratio * self.height * len(block_chars))
                current_block = total_blocks - (row * len(block_chars))
                
                if current_block > 0:
                    block_index = min(current_block, len(block_chars) - 1)
                    color = self._get_color_for_level(height_ratio)
                    line.append(block_chars[block_index], style=color)
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def visualize(self, audio_data: np.ndarray) -> str:
        """Visualize audio data using the current mode."""
        if audio_data is None or len(audio_data) == 0:
            # Return empty visualization
            return "\n".join([" " * self.width for _ in range(self.height)])
        
        if self.current_mode == "bars":
            return self._visualize_bars(audio_data)
        elif self.current_mode == "waveform":
            return self._visualize_waveform(audio_data)
        elif self.current_mode == "spectrum":
            return self._visualize_spectrum(audio_data)
        elif self.current_mode == "dots":
            return self._visualize_dots(audio_data)
        elif self.current_mode == "blocks":
            return self._visualize_blocks(audio_data)
        else:
            return self._visualize_bars(audio_data)  # Default fallback
    
    def get_info_panel(self) -> Panel:
        """Get information panel showing current mode and controls."""
        info_text = Text()
        info_text.append(f"Mode: {self.current_mode.upper()}", style="bold cyan")
        info_text.append("\n")
        info_text.append("Controls: ", style="bold")
        info_text.append("[SPACE] Cycle modes  [Q] Quit", style="yellow")
        
        return Panel(
            info_text,
            title="Audio Visualizer",
            border_style="blue",
            box=box.ROUNDED
        )