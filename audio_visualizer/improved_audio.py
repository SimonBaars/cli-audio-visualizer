"""Improved audio capture with better system audio detection."""

import numpy as np
import sounddevice as sd
import queue
import platform
import subprocess
import sys


class ImprovedAudioCapture:
    """Enhanced audio capture with better system audio detection."""
    
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 2048):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue(maxsize=5)
        self.stream = None
        self.running = False
        self.device_info = None
        self.device_id = None
        
        # Setup device
        self._setup_audio_device()
    
    def _list_audio_devices(self):
        """List all available audio devices with details."""
        print("\n" + "="*70)
        print("AVAILABLE AUDIO DEVICES:")
        print("="*70)
        
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                marker = ""
                name_lower = device['name'].lower()
                
                # Highlight potentially useful devices
                if any(keyword in name_lower for keyword in ['monitor', 'loopback', 'stereo mix', 'what u hear', 'wave out']):
                    marker = " ← SYSTEM AUDIO"
                elif 'pulse' in name_lower or 'pipewire' in name_lower:
                    marker = " ← AUDIO SERVER"
                
                print(f"  [{i}] {device['name']}{marker}")
                print(f"      Channels: {device['max_input_channels']}, "
                      f"Sample Rate: {device['default_samplerate']}")
        
        print("="*70 + "\n")
    
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
                            return source_name
        except:
            pass
        return None
    
    def _setup_audio_device(self):
        """Setup audio device with improved detection."""
        try:
            devices = sd.query_devices()
            system = platform.system()
            
            print(f"\nPlatform: {system}")
            
            if system == "Linux":
                print("Searching for system audio capture device...\n")
                
                # First, try to find monitor via pactl (most reliable for PipeWire/Pulse)
                monitor_source = self._find_pipewire_monitor()
                
                if monitor_source:
                    print(f"✓ Found monitor source via pactl: {monitor_source}")
                    
                    # Now find this device in sounddevice list
                    for i, device in enumerate(devices):
                        if device['max_input_channels'] <= 0:
                            continue
                        
                        # Check if the device name contains part of the monitor source name
                        device_name_clean = device['name'].lower().replace(' ', '').replace('-', '')
                        source_name_clean = monitor_source.lower().replace('.', '').replace('-', '').replace('_', '')
                        
                        # Try to match the device
                        if 'monitor' in device['name'].lower() or source_name_clean in device_name_clean:
                            self.device_id = i
                            self.device_info = device
                            print(f"✓ Matched to device: {device['name']}")
                            break
                    
                    # If we couldn't match it in sounddevice, try to use it directly as string
                    if not self.device_info:
                        try:
                            # Try using the PulseAudio source name directly
                            test = sd.query_devices(monitor_source)
                            if test and test['max_input_channels'] > 0:
                                self.device_id = monitor_source
                                self.device_info = test
                                print(f"✓ Using PulseAudio source directly: {monitor_source}")
                        except:
                            pass
                
                # If still not found, try searching sounddevice list directly
                if not self.device_info:
                    best_device = None
                    best_score = -1
                    
                    for i, device in enumerate(devices):
                        if device['max_input_channels'] <= 0:
                            continue
                        
                        name_lower = device['name'].lower()
                        score = 0
                        
                        # Score based on keywords
                        if 'monitor' in name_lower:
                            score += 10
                        if 'loopback' in name_lower:
                            score += 10
                        if 'analog' in name_lower and 'stereo' in name_lower:
                            score += 5
                        if 'pulse' in name_lower or 'pipewire' in name_lower:
                            score += 2
                        
                        if score > best_score:
                            best_score = score
                            best_device = (i, device)
                    
                    if best_device and best_score >= 5:
                        self.device_id, self.device_info = best_device
                        print(f"✓ Found system audio device: {self.device_info['name']}")
                
                # Still not found - show help
                if not self.device_info:
                    print("⚠ Could not auto-detect monitor device!\n")
                    print("Available sounddevice inputs:")
                    for i, device in enumerate(devices):
                        if device['max_input_channels'] > 0:
                            print(f"  [{i}] {device['name']}")
                    
                    if monitor_source:
                        print(f"\nPulseAudio/PipeWire monitor found: {monitor_source}")
                        print("But couldn't match it to a sounddevice. Trying anyway...")
                        self.device_id = monitor_source
                        self.device_info = {'name': monitor_source, 'default_samplerate': 48000}
                    else:
                        print("\n❌ No monitor sources found via pactl either!")
                        print("\nSetup instructions:")
                        print("  1. Run: pavucontrol")
                        print("  2. In Recording tab, select 'Monitor of...' as input")
                        print("  OR")
                        print("  3. Manually specify device with PULSE_SOURCE env var")
                        
                        # Fall back to default
                        self.device_info = sd.query_devices(kind='input')
                        print(f"\nUsing default input: {self.device_info['name']}")
                        print("(This captures microphone, not system audio)")
            
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
                            break
                
                if not self.device_info:
                    print("⚠ No system audio device found!")
                    print("\nTo capture system audio on Windows:")
                    print("1. Right-click speaker icon → Sounds → Recording tab")
                    print("2. Right-click empty space → Show Disabled Devices")
                    print("3. Enable 'Stereo Mix' or 'Wave Out Mix'")
                    print("4. Set as default recording device")
                    
                    self.device_info = sd.query_devices(kind='input')
                    print(f"\nUsing default input: {self.device_info['name']}")
            
            elif system == "Darwin":  # macOS
                print("\nSearching for audio capture device...")
                print("⚠ macOS requires additional setup for system audio capture:")
                print("1. Install BlackHole or Loopback Audio Driver")
                print("2. Configure Audio MIDI Setup to route system audio")
                print("   - Create Multi-Output Device")
                print("   - Add BlackHole and your speakers")
                
                self.device_info = sd.query_devices(kind='input')
                print(f"\nUsing default input: {self.device_info['name']}")
            
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
            sys.exit(1)
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            print(f"Audio callback status: {status}", file=sys.stderr)
        
        # Convert to mono
        if len(indata.shape) > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata.flatten()
        
        # Only queue if there's actual audio signal
        if np.max(np.abs(audio_data)) > 1e-6:
            try:
                self.audio_queue.put_nowait(audio_data.copy())
            except queue.Full:
                # Remove old data
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
            channels = 1
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
            
            print("✓ Audio capture started!")
            print("  If you don't see any visualization, make sure:")
            print("  1. Audio is playing on your system")
            print("  2. The volume is turned up")
            print("  3. You've configured the correct audio source\n")
            
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            print("Trying with default device...")
            
            try:
                self.stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    callback=self._audio_callback,
                    blocksize=self.chunk_size,
                    dtype=np.float32
                )
                self.stream.start()
                self.running = True
                print("✓ Started with default device")
            except Exception as e2:
                print(f"Failed to start audio capture: {e2}")
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