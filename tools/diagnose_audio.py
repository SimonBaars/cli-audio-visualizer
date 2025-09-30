#!/usr/bin/env python3
"""
Audio Diagnostics Tool for CLI Audio Visualizer

This script helps diagnose audio capture issues on different platforms.
Run this if you're experiencing a blank screen or no audio visualization.
"""
import sys
import platform

def main():
    print("=" * 70)
    print("CLI Audio Visualizer - Audio Diagnostics")
    print("=" * 70)
    print()
    
    # System info
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print()
    
    # Check sounddevice
    print("Checking sounddevice module...")
    try:
        import sounddevice as sd
        print("✓ sounddevice is installed")
        print(f"  Version: {sd.__version__ if hasattr(sd, '__version__') else 'unknown'}")
    except ImportError as e:
        print("✗ sounddevice is NOT installed")
        print(f"  Error: {e}")
        print("  Fix: pip install sounddevice")
        print()
        return 1
    print()
    
    # List audio devices
    print("Audio Devices:")
    print("-" * 70)
    try:
        devices = sd.query_devices()
        for idx, d in enumerate(devices):
            name = d.get('name', 'Unknown')
            max_in = d.get('max_input_channels', 0)
            max_out = d.get('max_output_channels', 0)
            default_marker = ""
            
            try:
                if hasattr(sd, 'default'):
                    if idx == sd.default.device[0]:
                        default_marker += " [DEFAULT INPUT]"
                    if idx == sd.default.device[1]:
                        default_marker += " [DEFAULT OUTPUT]"
            except:
                pass
            
            print(f"  {idx}: {name}{default_marker}")
            print(f"      Input channels: {max_in}, Output channels: {max_out}")
    except Exception as e:
        print(f"✗ Error listing devices: {e}")
        return 1
    print()
    
    # Platform-specific checks
    if sys.platform == 'darwin':
        print("macOS Specific Checks:")
        print("-" * 70)
        
        # Check for loopback devices
        print("Looking for loopback/virtual audio devices...")
        found_loopback = False
        keywords = ["blackhole", "loopback", "aggregate"]
        for idx, d in enumerate(devices):
            name = (d.get('name') or '').lower()
            if any(k in name for k in keywords) and d.get('max_input_channels', 0) > 0:
                print(f"  ✓ Found: {d.get('name')}")
                found_loopback = True
        
        if not found_loopback:
            print("  ✗ No loopback device found")
            print("  ")
            print("  To capture system audio on macOS, you need a virtual audio device:")
            print("  1. Install BlackHole: https://github.com/ExistentialAudio/BlackHole")
            print("  2. Or use Loopback: https://rogueamoeba.com/loopback/")
            print("  3. Configure it as your audio output or create an aggregate device")
            print()
            print("  Without a loopback device, only microphone input is available.")
        print()
        
        # Check microphone permission
        print("Testing microphone access...")
        try:
            default_in = sd.default.device[0] if hasattr(sd, 'default') else None
            if default_in is not None:
                # Try to open a stream briefly
                test_stream = sd.InputStream(
                    samplerate=44100,
                    blocksize=1024,
                    channels=1,
                    device=default_in
                )
                test_stream.start()
                test_stream.stop()
                test_stream.close()
                print("  ✓ Microphone access works")
            else:
                print("  ? No default input device")
        except Exception as e:
            print(f"  ✗ Cannot access microphone: {e}")
            print("  ")
            print("  This may be a permission issue:")
            print("  1. Go to System Preferences → Security & Privacy → Privacy → Microphone")
            print("  2. Ensure your terminal app (Terminal, iTerm2, etc.) is allowed")
            print("  3. You may need to restart your terminal after granting permission")
        print()
        
    elif sys.platform.startswith('linux'):
        print("Linux Specific Checks:")
        print("-" * 70)
        
        # Check for parec
        import subprocess
        try:
            result = subprocess.run(['which', 'parec'], capture_output=True, timeout=2)
            if result.returncode == 0:
                print("  ✓ parec is available")
            else:
                print("  ✗ parec is NOT available")
                print("  Fix: Install PulseAudio or PipeWire")
        except Exception as e:
            print(f"  ? Could not check for parec: {e}")
        
        # Check for monitor sources
        try:
            result = subprocess.run(['pactl', 'list', 'sources', 'short'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                monitors = [line for line in result.stdout.split('\n') 
                           if 'monitor' in line.lower() and line.strip()]
                if monitors:
                    print(f"  ✓ Found {len(monitors)} monitor source(s):")
                    for m in monitors:
                        parts = m.split()
                        if len(parts) >= 2:
                            print(f"    - {parts[1]}")
                else:
                    print("  ✗ No monitor sources found")
                    print("  Check your PulseAudio/PipeWire configuration")
        except Exception as e:
            print(f"  ? Could not check monitor sources: {e}")
        print()
        
    elif sys.platform == 'win32':
        print("Windows Specific Checks:")
        print("-" * 70)
        print("  WASAPI loopback is used for system audio capture")
        
        # Check if any output devices support loopback
        output_devices = [d for d in devices if d.get('max_output_channels', 0) > 0]
        if output_devices:
            print(f"  ✓ Found {len(output_devices)} output device(s)")
            print("  Output devices typically support WASAPI loopback")
        else:
            print("  ✗ No output devices found")
        print()
    
    print("=" * 70)
    print("Diagnostics complete!")
    print()
    print("If you're still experiencing issues:")
    print("1. Check the error messages when running the visualizer")
    print("2. Try running with: python visualizer.py 2>&1 | tee debug.log")
    print("3. Share the debug.log file when reporting issues")
    print("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
