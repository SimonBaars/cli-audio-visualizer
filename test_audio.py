#!/usr/bin/env python3
"""Test audio capture without the visualizer."""

import sys
import time
sys.path.insert(0, '.')

from audio_visualizer.improved_audio import ImprovedAudioCapture

def main():
    print("\n" + "="*70)
    print("AUDIO CAPTURE TEST")
    print("="*70 + "\n")
    
    # Initialize
    audio = ImprovedAudioCapture(sample_rate=44100, chunk_size=2048)
    
    print("\nTesting audio capture for 5 seconds...")
    print("Play some audio and watch for signal detection.\n")
    
    audio.start()
    
    try:
        samples_received = 0
        samples_with_audio = 0
        
        for i in range(50):  # 5 seconds at 100ms intervals
            data = audio.get_audio_data()
            
            if data is not None:
                samples_received += 1
                import numpy as np
                level = np.max(np.abs(data))
                
                if level > 0.001:
                    samples_with_audio += 1
                    bars = int(level * 50)
                    print(f"Audio level: {'█' * bars} {level:.4f}", end='\r')
                else:
                    print("Waiting for audio..." + " " * 40, end='\r')
            
            time.sleep(0.1)
        
        print("\n\n" + "="*70)
        print(f"Test complete!")
        print(f"  Samples received: {samples_received}/50")
        print(f"  Samples with audio: {samples_with_audio}")
        
        if samples_with_audio > 0:
            print("\n✓ Audio capture is working!")
        else:
            print("\n⚠ No audio detected. Make sure:")
            print("  1. Audio is playing")
            print("  2. Volume is up")
            print("  3. You selected the correct input device")
        
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    
    finally:
        audio.stop()

if __name__ == "__main__":
    main()