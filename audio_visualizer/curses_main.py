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
        
        # Initialize components (do this before curses starts)
        pass
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.running = False
    
    def run(self):
        """Main application loop."""
        try:
            # Initialize audio and visualizer
            self.visualizer = CursesVisualizer(self.stdscr)
            self.audio_capture.start()
            
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
    # Initialize audio BEFORE entering curses mode
    print("Initializing audio capture...")
    audio_capture = ImprovedAudioCapture(sample_rate=44100, chunk_size=2048)
    
    def _run(stdscr):
        app = CursesAudioVisualizerApp(stdscr)
        app.audio_capture = audio_capture  # Pass the pre-initialized audio
        return app.run()
    
    try:
        return curses.wrapper(_run)
    except KeyboardInterrupt:
        audio_capture.stop()
        return 0
    except Exception as e:
        audio_capture.stop()
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())