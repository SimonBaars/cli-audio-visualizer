"""Main entry point for the CLI audio visualizer."""

import sys
import time
import threading
import signal
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
import os

# Handle keyboard input across platforms
try:
    import termios
    import tty
    import select
    UNIX_LIKE = True
except ImportError:
    import msvcrt
    UNIX_LIKE = False

# Try to import the full implementations, fall back to demo mode if needed
try:
    import numpy as np
    import sounddevice as sd
    from .audio_capture import AudioCapture
    from .visualizer import Visualizer
    FULL_MODE = True
    print("Full audio capture mode available")
except ImportError as e:
    from .fallback_audio import FallbackAudioCapture as AudioCapture
    from .fallback_visualizer import FallbackVisualizer as Visualizer
    FULL_MODE = False
    print("Using fallback demo mode (install numpy and sounddevice for real audio)")

from .config import Config

class AudioVisualizerApp:
    """Main application class for the audio visualizer."""
    
    def __init__(self):
        self.console = Console()
        self.config = Config()
        self.audio_capture = AudioCapture()
        self.visualizer = Visualizer()
        self.running = False
        self.layout = Layout()
        
        # Set initial visualization mode from config
        self.visualizer.set_mode(self.config.last_visualization)
        
        # Setup layout
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
    def _setup_keyboard_input(self):
        """Setup non-blocking keyboard input."""
        if UNIX_LIKE:
            # Unix-like systems (Linux, macOS)
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        # Windows uses msvcrt which doesn't need setup
    
    def _restore_keyboard_input(self):
        """Restore keyboard input settings."""
        if UNIX_LIKE:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
    
    def _get_keypress(self):
        """Get a keypress without blocking."""
        if UNIX_LIKE:
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                return sys.stdin.read(1)
        else:
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8')
        return None
    
    def _handle_input(self):
        """Handle keyboard input in a separate thread."""
        while self.running:
            try:
                key = self._get_keypress()
                if key:
                    if key.lower() == 'q' or ord(key) == 27:  # 'q' or ESC
                        self.running = False
                        break
                    elif key == ' ':  # Space bar
                        new_mode = self.visualizer.cycle_mode()
                        self.config.last_visualization = new_mode
                time.sleep(0.01)  # Small delay to prevent busy waiting
            except (KeyboardInterrupt, EOFError):
                self.running = False
                break
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.running = False
    
    def _generate_layout_content(self):
        """Generate the content for the layout."""
        # Get audio data
        audio_data = self.audio_capture.get_audio_data()
        
        # Generate visualization
        viz_content = self.visualizer.visualize(audio_data)
        
        # Header
        mode_suffix = " (Demo Mode)" if not FULL_MODE else ""
        header_text = Text(f"CLI AUDIO VISUALIZER{mode_suffix}", style="bold magenta", justify="center")
        self.layout["header"].update(Panel(header_text, style="blue"))
        
        # Main visualization
        viz_panel = Panel(
            viz_content,
            title=f"Visualization: {self.visualizer.current_mode.upper()}",
            border_style="green",
            height=self.visualizer.height + 2
        )
        self.layout["main"].update(viz_panel)
        
        # Footer with controls
        footer_text = Text()
        footer_text.append("Controls: ", style="bold")
        footer_text.append("[SPACE] ", style="cyan")
        footer_text.append("Cycle modes  ", style="white")
        footer_text.append("[Q] ", style="cyan")
        footer_text.append("Quit", style="white")
        
        if hasattr(self.audio_capture, 'device_info') and self.audio_capture.device_info:
            device_name = self.audio_capture.device_info.get('name', 'Unknown')
            footer_text.append(f"  Device: {device_name[:30]}", style="dim white")
        
        if not FULL_MODE:
            footer_text.append("  Install numpy + sounddevice for real audio", style="dim yellow")
        
        self.layout["footer"].update(Panel(footer_text, style="blue"))
        
        return self.layout
    
    def run(self):
        """Run the audio visualizer application."""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Setup keyboard input
            self._setup_keyboard_input()
            
            # Start audio capture
            self.audio_capture.start()
            self.running = True
            
            # Start input handling thread
            input_thread = threading.Thread(target=self._handle_input, daemon=True)
            input_thread.start()
            
            # Main visualization loop
            with Live(
                self._generate_layout_content(),
                console=self.console,
                refresh_per_second=30,
                screen=True
            ) as live:
                while self.running:
                    try:
                        live.update(self._generate_layout_content())
                        time.sleep(1/30)  # 30 FPS
                    except KeyboardInterrupt:
                        break
        
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return 1
        
        finally:
            # Cleanup
            self.running = False
            self.audio_capture.stop()
            self._restore_keyboard_input()
        
        return 0

def main():
    """Main entry point."""
    try:
        app = AudioVisualizerApp()
        return app.run()
    except KeyboardInterrupt:
        print("\nExiting...")
        return 0
    except Exception as e:
        print(f"Error starting audio visualizer: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())