"""Audio capture using parec (PulseAudio/PipeWire recorder) for reliable system audio."""

import numpy as np
import subprocess
import threading
import queue
import struct
import sys


class ParecAudioCapture:
    """Audio capture using parec to directly capture from PulseAudio/PipeWire monitor."""
    
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue = queue.Queue(maxsize=5)  # Smaller queue for lower latency
        self.process = None
        self.running = False
        self.capture_thread = None
        self.monitor_source = None
        
        # Find monitor source
        self._find_monitor_source()
    
    def _find_monitor_source(self):
        """Find the monitor source using pactl."""
        try:
            result = subprocess.run(['pactl', 'list', 'sources', 'short'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if 'monitor' in line.lower() and line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            self.monitor_source = parts[1]
                            print(f"✓ Found monitor source: {self.monitor_source}")
                            return
        except Exception as e:
            print(f"Error finding monitor source: {e}")
        
        if not self.monitor_source:
            print("⚠ No monitor source found!")
            print("  Will try to use default source")
    
    def _capture_loop(self):
        """Capture audio in a separate thread."""
        try:
            # Build parec command
            cmd = ['parec']
            
            # Specify the monitor source if we found one
            if self.monitor_source:
                cmd.extend(['--device', self.monitor_source])
            
            # Audio format: 16-bit signed, mono, 44100 Hz
            cmd.extend([
                '--rate', str(self.sample_rate),
                '--channels', '1',
                '--format', 's16le',  # 16-bit signed little-endian
                '--latency-msec', '50'  # Low latency
            ])
            
            print(f"Starting parec: {' '.join(cmd)}")
            
            # Start parec process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=self.chunk_size * 2  # 2 bytes per sample
            )
            
            # Read audio data
            bytes_per_chunk = self.chunk_size * 2  # 2 bytes per sample (16-bit)
            
            while self.running:
                try:
                    # Read chunk
                    data = self.process.stdout.read(bytes_per_chunk)
                    
                    if not data:
                        break
                    
                    # Convert bytes to numpy array
                    # s16le = signed 16-bit little-endian
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    
                    # Convert to float32 in range [-1, 1]
                    audio_data = audio_data.astype(np.float32) / 32768.0
                    
                    # Pad if necessary
                    if len(audio_data) < self.chunk_size:
                        audio_data = np.pad(audio_data, (0, self.chunk_size - len(audio_data)))
                    
                    # Queue the data
                    try:
                        self.audio_queue.put_nowait(audio_data)
                    except queue.Full:
                        # Remove old data
                        try:
                            self.audio_queue.get_nowait()
                            self.audio_queue.put_nowait(audio_data)
                        except queue.Empty:
                            pass
                
                except Exception as e:
                    if self.running:
                        print(f"Error in capture loop: {e}", file=sys.stderr)
                    break
        
        except Exception as e:
            print(f"Error starting parec: {e}", file=sys.stderr)
            self.running = False
    
    def start(self):
        """Start audio capture."""
        if self.running:
            return
        
        if self.monitor_source:
            print(f"  ✓ Capturing from: {self.monitor_source}")
            print(f"  🎵 This will capture your system audio!")
        else:
            print(f"  ⚠ Using default source (may be microphone)")
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
    
    def stop(self):
        """Stop audio capture."""
        self.running = False
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except:
                try:
                    self.process.kill()
                except:
                    pass
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
    
    def get_audio_data(self):
        """Get latest audio data."""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_device_name(self) -> str:
        """Get the name of the current device."""
        if self.monitor_source:
            return self.monitor_source
        return "default"
    
    @property
    def using_monitor(self):
        """Check if using monitor source."""
        return self.monitor_source is not None