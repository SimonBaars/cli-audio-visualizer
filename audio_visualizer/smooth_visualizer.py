"""Smooth curses-based visualizer with multiple distinct modes and color schemes."""

import curses
import numpy as np
from typing import Optional
from . import visualizers
from .render import colors as color_mod


class SmoothVisualizer:
    """Non-flickering visualizer with distinct modes and color schemes."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.current_mode = 0
        self.current_color_scheme = 0
        # Mode list (bars_simple removed; ASCII handled via toggle)
        self.modes = ["bars", "spectrum", "waveform", "mirror_circular", "circular_wave", "levels", "radial_burst"]
        self.color_schemes = color_mod.SCHEMES
        # State dict must exist before loading config
        self.viz_state = {}
        # Persistent config
        self.config_path = 'config.json'
        self._load_config()
        # Ensure default medium EQ if not set by config
        if 'adaptive_eq_mode' not in self.viz_state:
            # Default: medium mode (1)
            self.viz_state['adaptive_eq_mode'] = 1
            self.viz_state['adaptive_eq'] = True
            self.viz_state['adaptive_eq_strength'] = 0.4
        # Clamp restored indices
        self.current_mode = min(self.current_mode, len(self.modes) - 1)
        self.current_color_scheme = min(self.current_color_scheme, len(self.color_schemes) - 1)
        self.simple_ascii = self.viz_state.get('simple_ascii', False)
        
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
        
    # (viz_state already initialized earlier)
        
        # Clear once at start
        self.stdscr.clear()
        self.stdscr.refresh()
    
    def _init_colors(self):
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLUE, -1)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_RED, -1)
            curses.init_pair(6, curses.COLOR_MAGENTA, -1)
            curses.init_pair(7, curses.COLOR_WHITE, -1)
    
    def _get_color(self, level: float, position: float = 0.5) -> int:
        scheme = self.color_schemes[self.current_color_scheme]
        return color_mod.get_color(level, position, scheme)
    
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
                flags = []
                # Flatten flag removed
                eq_mode = self.viz_state.get('adaptive_eq_mode', 0)
                if eq_mode == 1: flags.append('EQ~')
                elif eq_mode == 2: flags.append('EQ+')
                if self.viz_state.get('simple_ascii'): flags.append('ASCII')
                flag_text = (' [' + ' '.join(flags) + ']') if flags else ''
                self.stdscr.addstr(1, 2, mode_text + flag_text, curses.color_pair(2))
                self.stdscr.addstr(1, 40, color_text, curses.color_pair(3))
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
                
                controls = "[SPACE] Mode  [ENTER] Color  [B] ASCII  [W] EQ  [S] Save Config  [Q] Quit"
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
                    # Preserve user preference flags while clearing per-mode transient data
                    persistent_keys = {
                        'adaptive_eq', 'adaptive_eq_mode', 'adaptive_eq_strength', 'simple_ascii'
                    }
                    preserved = {k: v for k, v in self.viz_state.items() if k in persistent_keys}
                    self.viz_state = preserved
                    visualizers.base.clear_area(self.stdscr, y_offset, viz_height, viz_width)
                    self.mode_changed = False
                
                # Adaptive tilt factor for frequency distribution balancing
                # Adjust after obtaining bars in modes using frequency bars
                if 'adaptive_tilt' not in self.viz_state:
                    self.viz_state['adaptive_tilt'] = 1.0

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
                elif mode == "radial_burst":
                    visualizers.draw_radial_burst(self.stdscr, audio_data, viz_height, viz_width, y_offset,
                                                  self._get_color, self._apply_smoothing, self.viz_state)
            else:
                # Show message when no audio data is available
                msg_lines = [
                    "No Audio Data",
                    "",
                    "Possible causes:",
                    "- No audio playing",
                    "- Microphone permission denied (macOS)",
                    "- No audio device available",
                    "",
                    "Check stderr output for details",
                    "",
                    "Press Q to quit"
                ]
                try:
                    start_y = (height - len(msg_lines)) // 2
                    for i, line in enumerate(msg_lines):
                        x = (width - len(line)) // 2
                        if 0 <= start_y + i < height and x >= 0:
                            self.stdscr.addstr(start_y + i, x, line, curses.color_pair(5))
                except curses.error:
                    pass
            
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
            elif key == ord('s') or key == ord('S'):
                # Save config (snapshot feature removed)
                self._save_config()
            # 'F' flatten toggle removed (legacy)
            elif key == ord('w') or key == ord('W'):
                # Cycle adaptive EQ mode: 0 (off) -> 1 (medium) -> 2 (strong)
                mode = self.viz_state.get('adaptive_eq_mode', 0)
                mode = (mode + 1) % 3
                self.viz_state['adaptive_eq_mode'] = mode
                if mode == 0:
                    self.viz_state['adaptive_eq'] = False
                    self.viz_state['adaptive_eq_strength'] = 0.0
                elif mode == 1:
                    self.viz_state['adaptive_eq'] = True
                    self.viz_state['adaptive_eq_strength'] = 0.4
                else:
                    self.viz_state['adaptive_eq'] = True
                    self.viz_state['adaptive_eq_strength'] = 0.65
                if 'adaptive_eq_mean' in self.viz_state:
                    del self.viz_state['adaptive_eq_mean']
                self.prev_width = 0
                self.prev_height = 0
            elif key == ord('b') or key == ord('B'):
                # Toggle global simple ascii flag for bar-style modes
                self.viz_state['simple_ascii'] = not self.viz_state.get('simple_ascii', False)
                self.simple_ascii = self.viz_state['simple_ascii']
                self.prev_width = 0
                self.prev_height = 0
            # Removed: 'P' key (redundant with S)
        
        except curses.error:
            pass
        
        return True

    # Snapshot functionality removed: S now directly saves config

    # ------------------ Config Persistence ------------------
    def _load_config(self):
        import json, os
        if not os.path.exists(self.config_path):
            # Set default medium EQ when no config exists
            self.viz_state['adaptive_eq_mode'] = 1
            self.viz_state['adaptive_eq'] = True
            self.viz_state['adaptive_eq_strength'] = 0.4
            return
        try:
            with open(self.config_path, 'r') as f:
                cfg = json.load(f)
            legacy_idx = cfg.get('current_mode', 0)
            saved_name = cfg.get('mode_name')
            if saved_name and saved_name in self.modes:
                self.current_mode = self.modes.index(saved_name)
            else:
                # Legacy index migration: if it referenced removed bars_simple (index 1), map to bars (0)
                # All following modes shift left by one.
                if legacy_idx == 1:
                    legacy_idx = 0
                elif legacy_idx > 1:
                    legacy_idx -= 1
                self.current_mode = max(0, min(legacy_idx, len(self.modes) - 1))
            self.current_color_scheme = cfg.get('current_color_scheme', 0)
            # Legacy flatten removed; ignore if present
            self.viz_state['adaptive_eq'] = cfg.get('adaptive_eq', False)
            self.viz_state['simple_ascii'] = cfg.get('simple_ascii', False)
            # Infer or load adaptive_eq_mode
            if 'adaptive_eq_mode' in cfg:
                self.viz_state['adaptive_eq_mode'] = cfg.get('adaptive_eq_mode', 1)
            else:
                # Derive from strength if present
                strength = cfg.get('adaptive_eq_strength', 0.0)
                if self.viz_state.get('adaptive_eq'):
                    if strength >= 0.6:
                        self.viz_state['adaptive_eq_mode'] = 2
                    elif strength >= 0.25:
                        self.viz_state['adaptive_eq_mode'] = 1
                    else:
                        self.viz_state['adaptive_eq_mode'] = 1  # default medium
                else:
                    # If off but user previously disabled, keep off
                    if cfg.get('adaptive_eq') is False:
                        self.viz_state['adaptive_eq_mode'] = 0
                    else:
                        self.viz_state['adaptive_eq_mode'] = 1
            # Apply normalized strength based on inferred mode if we derived it
            mode = self.viz_state.get('adaptive_eq_mode', 1)
            if mode == 0:
                self.viz_state['adaptive_eq'] = False
                self.viz_state['adaptive_eq_strength'] = 0.0
            elif mode == 1:
                self.viz_state['adaptive_eq'] = True
                self.viz_state['adaptive_eq_strength'] = 0.4
            else:
                self.viz_state['adaptive_eq'] = True
                self.viz_state['adaptive_eq_strength'] = 0.65
        except Exception:
            pass

    def _save_config(self):
        import json
        cfg = {
            'current_mode': self.current_mode,  # still write index for backward compat
            'mode_name': self.modes[self.current_mode],
            'current_color_scheme': self.current_color_scheme,
            'adaptive_eq': self.viz_state.get('adaptive_eq', False),
            'adaptive_eq_mode': self.viz_state.get('adaptive_eq_mode', 1),
            'simple_ascii': self.viz_state.get('simple_ascii', False)
        }
        try:
            with open(self.config_path, 'w') as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass