"""Improved audio capture with better system audio detection."""

import numpy as np
import sounddevice as sd
import queue
import platform
import subprocess
import sys
import os


class ImprovedAudioCapture:
    """Enhanced audio capture with better system audio detection."""
    
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 2048):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue(maxsize=10)  # Larger queue for smoother playback
        self.stream = None
        self.running = False
        self.device_info = None
        self.device_id = None
        self.using_monitor = False
        self.monitor_source_name = None
        
        # Setup device
        self._setup_audio_device()
    
    def _find_pipewire_monitor(self):
        """Find PipeWire/PulseAudio monitor source using pactl."""
        try:
            result = subprocess.run(['pactl', 'list', 'sources', 'short'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'monitor' in line.lower() and line.strip():
                        # Parse: ID  NAME  MODULE  FORMAT
                        parts = line.split()
                        if len(parts) >= 2:
                            source_name = parts[1]
                            source_id = parts[0]
                            return source_name, source_id
        except:
            pass
        return None, None
    
    def _setup_audio_device(self):
        """Setup audio device with improved detection."""
        try:
            devices = sd.query_devices()
            system = platform.system()
            
            print(f"\nPlatform: {system}")
            
            if system == "Linux":
                print("Searching for system audio capture device...\n")
                
                # Find monitor via pactl (most reliable for PipeWire/Pulse)
                monitor_source, monitor_id = self._find_pipewire_monitor()
                
                if monitor_source:
                    print(f"✓ Found monitor source: {monitor_source}")
                    
                    # Set the PULSE_SOURCE environment variable - this is the KEY!
                    # This tells PulseAudio/PipeWire which source to use
                    os.environ['PULSE_SOURCE'] = monitor_source
                    print(f"✓ Set PULSE_SOURCE environment variable")
                    
                    # Store this for later
                    self.monitor_source_name = monitor_source
                    self.using_monitor = True
                    
                    # Use the pulse/pipewire device from sounddevice
                    # These respect the PULSE_SOURCE environment variable
                    for i, device in enumerate(devices):
                        if device['max_input_channels'] <= 0:
                            continue
                        
                        device_name_lower = device['name'].lower()
                        # Look for pulse or pipewire device
                        if 'pulse' in device_name_lower or 'pipewire' in device_name_lower:
                            self.device_id = i
                            self.device_info = device
                            print(f"✓ Using audio server: {device['name']}")
                            break
                    
                    # If we didn't find pulse/pipewire, use default
                    if not self.device_info:
                        self.device_info = sd.query_devices(kind='input')
                        print(f"✓ Using default device: {self.device_info['name']}")
                    
                    print(f"✓ Will capture system audio from monitor source")
                else:
                    print("⚠ No monitor source found via pactl!")
                    print("\nSetup required:")
                    print("  1. Option A: Use pavucontrol")
                    print("     - Install: sudo pacman -S pavucontrol")
                    print("     - Run: pavucontrol")
                    print("     - Go to Recording tab and select 'Monitor of...'")
                    print("  2. Option B: Set default source")
                    print("     - pactl set-default-source [monitor-source-name]")
                    
                    # Fall back to default
                    self.device_info = sd.query_devices(kind='input')
                    print(f"\n⚠ Using default input: {self.device_info['name']}")
                    print("  (This will capture microphone, not system audio)")
            
            elif system == "Windows":
                print("\nSearching for system audio capture device...")
                
                # Look for Stereo Mix or similar
                for i, device in enumerate(devices):
                    if device['max_input_channels'] > 0:
                        name_lower = device['name'].lower()
                        if any(kw in name_lower for kw in ['stereo mix', 'wave out', 'what u hear', 'loopback']):
                            self.device_id = i
                            self.device_info = device
                            print(f"✓ Found: {device['name']}")
                            self.using_monitor = True
                            break
                
                if not self.device_info:
                    print("⚠ No system audio device found!")
                    print("\nTo capture system audio on Windows:")
                    print("  1. Right-click speaker icon → Sounds → Recording tab")
                    print("  2. Right-click empty space → Show Disabled Devices")
                    print("  3. Enable 'Stereo Mix' or 'Wave Out Mix'")
                    print("  4. Set as default recording device")
                    
                    self.device_info = sd.query_devices(kind='input')
                    print(f"\n⚠ Using default input: {self.device_info['name']}")
            
            elif system == "Darwin":  # macOS
                print("\nSearching for audio capture device...")
                print("⚠ macOS requires additional setup for system audio capture:")
                print("  1. Install BlackHole: brew install blackhole-2ch")
                print("  2. Configure Audio MIDI Setup to route system audio")
                
                self.device_info = sd.query_devices(kind='input')
                print(f"\n⚠ Using default input: {self.device_info['name']}")
            
            else:
                self.device_info = sd.query_devices(kind='input')
                print(f"Using default device: {self.device_info['name']}")
            
            print(f"\nConfiguration:")
            print(f"  Sample Rate: {self.sample_rate} Hz")
            print(f"  Chunk Size: {self.chunk_size} samples")
            if self.device_info:
                print(f"  Device: {self.device_info.get('name', 'Unknown')}")
            print("\nStarting in 2 seconds...")
            import time
            time.sleep(2)
            
        except Exception as e:
            print(f"Error setting up audio device: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            print(f"Audio status: {status}", file=sys.stderr)
        
        # Convert to mono
        if len(indata.shape) > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata.flatten()
        
        # Queue all data, not just when there's signal
        # This prevents the "Waiting for audio" flashing
        try:
            self.audio_queue.put_nowait(audio_data.copy())
        except queue.Full:
            # Remove old data and add new
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put_nowait(audio_data.copy())
            except queue.Empty:
                pass
    
    def start(self):
        """Start audio capture."""
        if self.running:
            return
        
        try:
            # Determine channels
            channels = 2  # Default to stereo
            if isinstance(self.device_info, dict) and 'max_input_channels' in self.device_info:
                channels = min(2, max(1, self.device_info['max_input_channels']))
            
            kwargs = {
                'samplerate': self.sample_rate,
                'channels': channels,
                'callback': self._audio_callback,
                'blocksize': self.chunk_size,
                'dtype': np.float32
            }
            
            if self.device_id is not None:
                kwargs['device'] = self.device_id
            
            self.stream = sd.InputStream(**kwargs)
            self.stream.start()
            self.running = True
            
            print("\n✓ Audio capture started!")
            if self.using_monitor:
                print(f"  ✓ Capturing system audio")
                if self.monitor_source_name:
                    print(f"     Source: {self.monitor_source_name}")
                print("  🎵 Play some music and you should see visualization!")
            else:
                print("  ⚠ Capturing from microphone (not system audio)")
                print("  📝 To capture system audio, see setup instructions above")
            print()
            
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def stop(self):
        """Stop audio capture."""
        if self.stream and self.running:
            self.stream.stop()
            self.stream.close()
            self.running = False
    
    def get_audio_data(self):
        """Get latest audio data."""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_device_name(self) -> str:
        """Get the name of the current device."""
        if self.device_info:
            if isinstance(self.device_info, dict):
                return self.device_info.get('name', 'Unknown')
            else:
                return str(self.device_info)
        return "Unknown"