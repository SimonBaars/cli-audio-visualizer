"""Main entry point using stable curses interface."""

import curses
import sys
import signal
import time
from .improved_audio import ImprovedAudioCapture
from .curses_visualizer import CursesVisualizer


class CursesAudioVisualizerApp:
    """Main application using curses."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize components
        print("Initializing audio capture...")
        self.audio_capture = ImprovedAudioCapture(sample_rate=44100, chunk_size=2048)
        self.visualizer = CursesVisualizer(stdscr)
        
        print("\nStarting audio capture...")
        self.audio_capture.start()
        
        print("Press any key to continue...")
        input()
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.running = False
    
    def run(self):
        """Main application loop."""
        try:
            while self.running:
                # Get audio data
                audio_data = self.audio_capture.get_audio_data()
                
                # Visualize
                device_name = self.audio_capture.get_device_name()
                self.visualizer.visualize(audio_data, device_name)
                
                # Handle input
                if not self.visualizer.handle_input():
                    break
                
                # Small delay to control frame rate (~60 FPS)
                time.sleep(0.016)
        
        except Exception as e:
            # Cleanup curses before showing error
            curses.endwin()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        finally:
            self.audio_capture.stop()
        
        return 0


def main():
    """Entry point for curses application."""
    def _run(stdscr):
        app = CursesAudioVisualizerApp(stdscr)
        return app.run()
    
    try:
        return curses.wrapper(_run)
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())