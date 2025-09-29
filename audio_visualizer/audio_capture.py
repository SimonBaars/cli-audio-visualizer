"""Cross-platform audio capture module."""

import numpy as np
import sounddevice as sd
import threading
import queue
from typing import Optional, Callable
import sys
import platform

class AudioCapture:
    """Cross-platform audio capture using sounddevice (works with PulseAudio, WASAPI, CoreAudio)."""
    
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024, channels: int = 1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.stream = None
        self.running = False
        self.device_info = None
        
        # Initialize audio system
        self._setup_audio_device()
    
    def _setup_audio_device(self):
        """Setup the audio input device based on the platform."""
        try:
            # Get default input device
            self.device_info = sd.query_devices(kind='input')
            
            # On Linux, try to find system audio monitor/loopback device
            if platform.system() == "Linux":
                devices = sd.query_devices()
                
                # Look for monitor devices (for system audio capture)
                monitor_devices = []
                for i, device in enumerate(devices):
                    device_name = str(device).lower()
                    if ('monitor' in device_name or 'loopback' in device_name) and device['max_input_channels'] > 0:
                        monitor_devices.append((i, device))
                
                # If monitor devices found, use the first one
                if monitor_devices:
                    device_id, device = monitor_devices[0]
                    sd.default.device[0] = device_id
                    self.device_info = device
                    print(f"Using system audio monitor: {device['name']}")
                else:
                    # Fall back to PulseAudio default or regular input
                    pulse_devices = [d for d in devices if 'pulse' in str(d).lower()]
                    if pulse_devices:
                        for i, device in enumerate(devices):
                            if 'pulse' in str(device).lower() and device['max_input_channels'] > 0:
                                sd.default.device[0] = i
                                break
                    print(f"Using audio device: {self.device_info['name']}")
                    print("Note: For system audio, configure a monitor source with:")
                    print("  pactl load-module module-loopback latency_msec=1")
            else:
                print(f"Using audio device: {self.device_info['name']}")
                print("Note: For system audio capture, you may need to configure virtual audio routing")
            
            print(f"Sample rate: {self.sample_rate}, Channels: {self.channels}")
            
        except Exception as e:
            print(f"Warning: Could not setup audio device: {e}")
            print("Using system default audio device")
    
    def _audio_callback(self, indata, frames, time, status):
        """Callback function for audio input stream."""
        if status:
            print(f"Audio input error: {status}")
        
        # Convert to mono if stereo
        if len(indata.shape) > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata.flatten()
        
        # Put audio data in queue for processing
        try:
            self.audio_queue.put(audio_data, block=False)
        except queue.Full:
            # Drop old data if queue is full
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put(audio_data, block=False)
            except queue.Empty:
                pass
    
    def start(self):
        """Start audio capture."""
        if self.running:
            return
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                blocksize=self.chunk_size,
                dtype=np.float32
            )
            self.stream.start()
            self.running = True
            print("Audio capture started")
        except Exception as e:
            print(f"Error starting audio capture: {e}")
            sys.exit(1)
    
    def stop(self):
        """Stop audio capture."""
        if self.stream and self.running:
            self.stream.stop()
            self.stream.close()
            self.running = False
            print("Audio capture stopped")
    
    def get_audio_data(self) -> Optional[np.ndarray]:
        """Get the latest audio data from the queue."""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def is_running(self) -> bool:
        """Check if audio capture is running."""
        return self.running