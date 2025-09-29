"""Fallback audio capture using synthetic data for demonstration."""

import math
import time
import threading
import queue
import random
from typing import Optional

class FallbackAudioCapture:
    """Fallback audio capture that generates synthetic audio data for demonstration."""
    
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024, channels: int = 1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.time_offset = 0
        
        print("Using fallback audio capture with synthetic data for demonstration")
    
    def _generate_synthetic_audio(self):
        """Generate synthetic audio data for visualization."""
        # Create a mix of sine waves with some noise
        t = [self.time_offset + i / self.sample_rate for i in range(self.chunk_size)]
        
        # Base frequencies for a musical visualization
        frequencies = [220, 440, 880, 1760]  # A notes in different octaves
        
        # Generate waveform
        audio_data = []
        for i in range(self.chunk_size):
            sample = 0
            for freq in frequencies:
                # Add some variation to make it more interesting
                amplitude = 0.1 + 0.3 * abs(math.sin(self.time_offset * 0.5 + freq * 0.001))
                sample += amplitude * math.sin(2 * math.pi * freq * t[i])
            
            # Add some noise for realism
            sample += 0.1 * (random.random() - 0.5)
            
            # Clamp to reasonable range
            sample = max(-1.0, min(1.0, sample))
            audio_data.append(sample)
        
        self.time_offset += self.chunk_size / self.sample_rate
        return audio_data
    
    def _audio_generation_loop(self):
        """Main loop for generating audio data."""
        while self.running:
            audio_data = self._generate_synthetic_audio()
            
            try:
                self.audio_queue.put(audio_data, block=False)
            except queue.Full:
                # Drop old data if queue is full
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put(audio_data, block=False)
                except queue.Empty:
                    pass
            
            # Sleep to maintain roughly real-time generation
            time.sleep(self.chunk_size / self.sample_rate * 0.8)  # Slightly faster than real-time
    
    def start(self):
        """Start synthetic audio generation."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._audio_generation_loop, daemon=True)
        self.thread.start()
        print("Synthetic audio generation started")
    
    def stop(self):
        """Stop synthetic audio generation."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=1.0)
            print("Synthetic audio generation stopped")
    
    def get_audio_data(self) -> Optional[list]:
        """Get the latest synthetic audio data from the queue."""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def is_running(self) -> bool:
        """Check if synthetic audio generation is running."""
        return self.running
    
    @property
    def device_info(self):
        """Provide fake device info for compatibility."""
        return {"name": "Synthetic Audio Generator (Demo Mode)"}