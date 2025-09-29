"""Main entry point using parec audio capture and smooth visualizer."""

import curses
import sys
import signal
import time
from .parec_audio import ParecAudioCapture
from .smooth_visualizer import SmoothVisualizer


class SmoothAudioVisualizerApp:
    """Main application using parec and smooth rendering."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.running = False
    
    def run(self):
        """Main application loop."""
        try:
            # Initialize components
            self.visualizer = SmoothVisualizer(self.stdscr)
            self.audio_capture.start()
            
            # Main loop
            while self.running:
                # Get audio data
                audio_data = self.audio_capture.get_audio_data()
                
                # Visualize
                device_name = self.audio_capture.get_device_name()
                self.visualizer.visualize(audio_data, device_name)
                
                # Handle input
                if not self.visualizer.handle_input():
                    break
                
                # Small delay for ~60 FPS
                time.sleep(0.016)
        
        except Exception as e:
            curses.endwin()
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        finally:
            self.audio_capture.stop()
        
        return 0


def main():
    """Entry point for smooth visualizer."""
    # Initialize audio BEFORE curses
    print("="*70)
    print("CLI AUDIO VISUALIZER - Smooth Edition")
    print("="*70)
    print()
    
    audio_capture = ParecAudioCapture(sample_rate=44100, chunk_size=2048)
    
    if not audio_capture.using_monitor:
        print("\n⚠️  WARNING: Not using monitor source!")
        print("   The visualizer may capture microphone instead of system audio.")
        print()
    
    print("Waiting 2 seconds for audio to initialize...")
    time.sleep(2)
    
    def _run(stdscr):
        app = SmoothAudioVisualizerApp(stdscr)
        app.audio_capture = audio_capture
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