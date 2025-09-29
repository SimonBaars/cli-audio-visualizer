#!/usr/bin/env python3
"""Test parec-based audio capture."""

import sys
import time
sys.path.insert(0, '.')

from audio_visualizer.parec_audio import ParecAudioCapture
import numpy as np

def main():
    print("\n" + "="*70)
    print("PAREC AUDIO CAPTURE TEST")
    print("="*70 + "\n")
    
    print("Initializing parec audio capture...")
    audio = ParecAudioCapture(sample_rate=44100, chunk_size=2048)
    
    if not audio.using_monitor:
        print("\n⚠️  WARNING: No monitor source detected!")
        print("   This will likely capture from microphone.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    print("\n" + "="*70)
    print("Testing for 10 seconds...")
    print("🎵 PLAY MUSIC NOW!")
    print("="*70 + "\n")
    
    audio.start()
    time.sleep(1)  # Let it initialize
    
    try:
        samples_received = 0
        samples_with_audio = 0
        max_level = 0.0
        
        for i in range(100):
            data = audio.get_audio_data()
            
            if data is not None:
                samples_received += 1
                level = np.max(np.abs(data))
                max_level = max(max_level, level)
                
                if level > 0.0001:
                    samples_with_audio += 1
                    scaled_level = min(level * 100, 1.0)
                    bars = int(scaled_level * 50)
                    print(f"Audio: {'█' * bars}{' ' * (50-bars)} {level:.6f}", end='\r')
                else:
                    print(f"Silence: {'-' * 50} {level:.6f}", end='\r')
            else:
                print("No data" + " " * 50, end='\r')
            
            time.sleep(0.1)
        
        print("\n\n" + "="*70)
        print("Test Results:")
        print(f"  Samples received: {samples_received}/100")
        print(f"  Samples with audio: {samples_with_audio}")
        print(f"  Max level: {max_level:.6f}")
        
        if samples_with_audio > 10:
            print("\n✅ Audio capture is working!")
            print(f"  ✓ Capturing from: {audio.get_device_name()}")
        elif samples_received > 0:
            print("\n⚠️  Audio capture working but weak signal")
            print("  - Is music playing?")
            print("  - Turn up system volume")
        else:
            print("\n❌ No audio data received")
            print("  Check that parec is installed: which parec")
        
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
    finally:
        audio.stop()

if __name__ == "__main__":
    main()