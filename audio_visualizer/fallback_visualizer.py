"""Fallback visualization engine that works without external dependencies."""

import math
import cmath
from rich.console import Console
from rich.text import Text
from rich import box
from rich.panel import Panel
from typing import List, Tuple

class FallbackVisualizer:
    """Fallback visualization engine that works without numpy."""
    
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
        
        # Smoothing parameters
        self.smoothing_factor = 0.7
        self.previous_values = [0.0] * self.width
    
    def cycle_mode(self):
        """Cycle to the next visualization mode."""
        current_index = self.modes.index(self.current_mode)
        self.current_mode = self.modes[(current_index + 1) % len(self.modes)]
        return self.current_mode
    
    def set_mode(self, mode: str):
        """Set the visualization mode."""
        if mode in self.modes:
            self.current_mode = mode
    
    def _apply_smoothing(self, values: List[float]) -> List[float]:
        """Apply smoothing to reduce flickering."""
        for i in range(len(values)):
            if i < len(self.previous_values):
                self.previous_values[i] = (self.smoothing_factor * self.previous_values[i] + 
                                         (1 - self.smoothing_factor) * values[i])
            else:
                self.previous_values.append(values[i])
        
        return self.previous_values[:len(values)]
    
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
    
    def _simple_fft(self, audio_data: List[float], n_bins: int = None) -> List[float]:
        """Simple FFT implementation for frequency analysis."""
        if n_bins is None:
            n_bins = min(len(audio_data), self.width)
        
        # Simple frequency analysis using sliding window approach
        frequencies = []
        window_size = len(audio_data) // n_bins
        
        for i in range(n_bins):
            start_idx = i * window_size
            end_idx = min(start_idx + window_size, len(audio_data))
            
            if start_idx < len(audio_data):
                # Calculate magnitude of frequency component using simple DFT approach
                window_data = audio_data[start_idx:end_idx]
                
                # Simple magnitude calculation
                magnitude = 0
                for j, sample in enumerate(window_data):
                    # Simple frequency analysis using sin/cos
                    freq_component = sample * math.cos(2 * math.pi * i * j / len(window_data))
                    magnitude += abs(freq_component)
                
                frequencies.append(magnitude / len(window_data) if window_data else 0)
            else:
                frequencies.append(0)
        
        return frequencies
    
    def _visualize_bars(self, audio_data: List[float]) -> str:
        """Create bar visualization."""
        # Get frequency components
        frequencies = self._simple_fft(audio_data, self.width)
        
        # Normalize
        max_freq = max(frequencies) if frequencies and max(frequencies) > 0 else 1
        normalized_freqs = [f / max_freq for f in frequencies]
        
        # Apply smoothing
        smoothed_freqs = self._apply_smoothing(normalized_freqs)
        
        # Create bars
        lines = []
        for row in range(self.height - 1, -1, -1):
            line = Text()
            for col in range(self.width):
                if col < len(smoothed_freqs):
                    height_ratio = smoothed_freqs[col]
                    bar_height = int(height_ratio * self.height)
                    
                    if row < bar_height:
                        color = self._get_color_for_level(height_ratio)
                        line.append("█", style=color)
                    else:
                        line.append(" ")
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def _visualize_waveform(self, audio_data: List[float]) -> str:
        """Create waveform visualization."""
        # Downsample to fit width
        if len(audio_data) > self.width:
            step = len(audio_data) // self.width
            waveform = [audio_data[i] for i in range(0, len(audio_data), step)][:self.width]
        else:
            waveform = audio_data + [0] * (self.width - len(audio_data))
        
        # Apply smoothing
        waveform = self._apply_smoothing(waveform)
        
        # Normalize to height
        max_val = max(abs(v) for v in waveform) if waveform else 1
        if max_val > 0:
            waveform = [v / max_val for v in waveform]
        
        # Create waveform display
        lines = []
        middle = self.height // 2
        
        for row in range(self.height):
            line = Text()
            for col in range(self.width):
                if col < len(waveform):
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
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def _visualize_spectrum(self, audio_data: List[float]) -> str:
        """Create spectrum analyzer visualization."""
        # Get frequency components
        frequencies = self._simple_fft(audio_data, self.width)
        
        # Convert to dB-like scale
        spectrum = []
        for freq in frequencies:
            if freq > 0:
                db_val = math.log10(freq + 1e-10) * 20
                spectrum.append(max(0, (db_val + 80) / 80))  # Normalize
            else:
                spectrum.append(0)
        
        # Apply smoothing
        spectrum = self._apply_smoothing(spectrum)
        
        # Create spectrum display
        lines = []
        for row in range(self.height - 1, -1, -1):
            line = Text()
            for col in range(self.width):
                if col < len(spectrum):
                    height_ratio = spectrum[col]
                    bar_height = int(height_ratio * self.height)
                    
                    if row < bar_height:
                        # Use different colors for different frequency ranges
                        freq_color_index = col // max(1, self.width // len(self.colors))
                        freq_color_index = min(freq_color_index, len(self.colors) - 1)
                        color = self.colors[freq_color_index]
                        line.append("▆", style=color)
                    else:
                        line.append(" ")
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def _visualize_dots(self, audio_data: List[float]) -> str:
        """Create dot matrix visualization."""
        # Create a 2D representation
        frequencies = self._simple_fft(audio_data, self.width)
        
        lines = []
        for row in range(self.height):
            line = Text()
            for col in range(self.width):
                # Get frequency for this column
                if col < len(frequencies):
                    freq_intensity = frequencies[col]
                    # Get time-domain info for this row
                    time_idx = row * len(audio_data) // self.height
                    if time_idx < len(audio_data):
                        time_intensity = abs(audio_data[time_idx])
                        combined_intensity = freq_intensity * time_intensity * 100
                        
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
    
    def _visualize_blocks(self, audio_data: List[float]) -> str:
        """Create block visualization."""
        # Get frequency components
        frequencies = self._simple_fft(audio_data, self.width)
        
        # Normalize
        max_freq = max(frequencies) if frequencies and max(frequencies) > 0 else 1
        normalized_freqs = [f / max_freq for f in frequencies]
        
        # Apply smoothing
        smoothed_freqs = self._apply_smoothing(normalized_freqs)
        
        # Block characters for different heights
        block_chars = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        lines = []
        for row in range(self.height - 1, -1, -1):
            line = Text()
            for col in range(self.width):
                if col < len(smoothed_freqs):
                    height_ratio = smoothed_freqs[col]
                    total_blocks = int(height_ratio * self.height * len(block_chars))
                    current_block = total_blocks - (row * len(block_chars))
                    
                    if current_block > 0:
                        block_index = min(current_block, len(block_chars) - 1)
                        color = self._get_color_for_level(height_ratio)
                        line.append(block_chars[block_index], style=color)
                    else:
                        line.append(" ")
                else:
                    line.append(" ")
            lines.append(line)
        
        return "\n".join(str(line) for line in lines)
    
    def visualize(self, audio_data) -> str:
        """Visualize audio data using the current mode."""
        if audio_data is None or len(audio_data) == 0:
            # Return empty visualization
            return "\n".join([" " * self.width for _ in range(self.height)])
        
        # Convert to list if needed
        if not isinstance(audio_data, list):
            audio_data = list(audio_data)
        
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
            title="Audio Visualizer (Demo Mode)",
            border_style="blue",
            box=box.ROUNDED
        )