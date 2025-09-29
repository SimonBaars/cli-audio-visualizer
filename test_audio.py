#!/usr/bin/env python3
"""Test audio capture without the visualizer."""

import sys
import time
sys.path.insert(0, '.')

from audio_visualizer.improved_audio import ImprovedAudioCapture
import numpy as np

def main():
    print("\n" + "="*70)
    print("AUDIO CAPTURE TEST")
    print("="*70 + "\n")
    
    print("Initializing...")
    # Initialize
    audio = ImprovedAudioCapture(sample_rate=44100, chunk_size=2048)
    
    print("\n" + "="*70)
    print("Testing audio capture for 10 seconds...")
    print("🎵 PLAY SOME MUSIC NOW!")
    print("="*70 + "\n")
    
    try:
        samples_received = 0
        samples_with_audio = 0
        max_level = 0.0
        
        for i in range(100):  # 10 seconds at 100ms intervals
            data = audio.get_audio_data()
            
            if data is not None:
                samples_received += 1
                level = np.max(np.abs(data))
                max_level = max(max_level, level)
                
                # Lower threshold for system audio
                if level > 0.0001:
                    samples_with_audio += 1
                    # Scale up for visualization
                    scaled_level = min(level * 100, 1.0)
                    bars = int(scaled_level * 50)
                    print(f"Audio: {'█' * bars}{' ' * (50-bars)} {level:.6f}", end='\r')
                else:
                    print(f"Silence: {'-' * 50} {level:.6f}", end='\r')
            else:
                print("No data received" + " " * 50, end='\r')
            
            time.sleep(0.1)
        
        print("\n\n" + "="*70)
        print(f"Test complete!")
        print(f"  Samples received: {samples_received}/100")
        print(f"  Samples with audio: {samples_with_audio}")
        print(f"  Max audio level: {max_level:.6f}")
        
        if samples_with_audio > 10:
            print("\n✅ Audio capture is working!")
            if audio.using_monitor:
                print(f"  ✓ Capturing from system audio monitor")
                print(f"  ✓ Source: {audio.monitor_source_name}")
            print("\n🎵 You're ready to run the visualizer!")
        elif samples_received > 0:
            print("\n⚠️  Audio capture working but no strong signal detected")
            print("  - Is music actually playing?")
            print("  - Try turning up the volume")
            print(f"  - Max level detected: {max_level:.6f}")
        else:
            print("\n❌ No audio data received")
            print("  Check the setup instructions above")
        
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    
    finally:
        audio.stop()

if __name__ == "__main__":
    main()