"""Cross-platform audio capture abstraction.

Linux: uses parec (PulseAudio / PipeWire) via ParecAudioCapture (existing implementation).
Windows: uses sounddevice WASAPI loopback if available (captures system output directly).
macOS: attempts to capture from a virtual loopback device (e.g. BlackHole / Loopback). If not found,
       falls back to the default input (microphone) with a warning (one-time, silent by default).

If no backend is available, provides a SilentAudioCapture that yields None.

All capture classes expose:
- start()
- stop()
- get_audio_data() -> np.ndarray | None
- get_device_name() -> str
"""
from __future__ import annotations
import sys
import threading
import queue
import numpy as np
from typing import Optional

# Reuse existing Linux implementation
from .parec_audio import ParecAudioCapture  # noqa: F401

try:
    import sounddevice as sd  # type: ignore
except Exception:  # pragma: no cover - optional dependency fallback
    sd = None  # type: ignore


class SilentAudioCapture:
    def __init__(self, *_, **__):
        self.sample_rate = 44100
    def start(self):
        pass
    def stop(self):
        pass
    def get_audio_data(self):
        return None
    def get_device_name(self):
        return "silent"


class WASAPILoopbackCapture:
    """Windows WASAPI loopback using sounddevice."""
    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=5)
        self.stream = None
        self.running = False
        self.device_name = None

    def _choose_loopback_device(self):
        try:
            devices = sd.query_devices()  # type: ignore[attr-defined]
            # Prefer default output
            default_out = sd.default.device[1] if hasattr(sd, 'default') else None  # type: ignore
            if default_out is not None and default_out >= 0:
                info = sd.query_devices(default_out)
                self.device_name = info.get('name', 'WASAPI loopback')
                return default_out
            # Fallback: first output device
            for idx, d in enumerate(devices):
                if d.get('max_output_channels', 0) > 0:
                    self.device_name = d.get('name', f'device_{idx}')
                    return idx
        except Exception:
            pass
        return None

    def start(self):
        if sd is None or self.running:
            return
        dev = self._choose_loopback_device()
        if dev is None:
            return
        try:
            settings = None
            # WASAPI specific extra settings
            if hasattr(sd, 'WasapiSettings'):
                try:
                    settings = sd.WasapiSettings(loopback=True)  # type: ignore[attr-defined]
                except Exception:
                    settings = None

            def callback(indata, frames, time_, status):  # noqa: D401
                if status:
                    # Drop status messages silently
                    pass
                if not self.running:
                    return
                try:
                    # indata shape: (frames, channels)
                    if indata.ndim == 2 and indata.shape[1] > 1:
                        mono = np.mean(indata, axis=1)
                    else:
                        mono = indata[:, 0] if indata.ndim == 2 else indata
                    # Ensure float32
                    mono = mono.astype(np.float32)
                    # Pad / trim to chunk_size
                    if len(mono) < self.chunk_size:
                        mono = np.pad(mono, (0, self.chunk_size - len(mono)))
                    elif len(mono) > self.chunk_size:
                        mono = mono[:self.chunk_size]
                    try:
                        self.audio_queue.put_nowait(mono)
                    except queue.Full:
                        try:
                            self.audio_queue.get_nowait()
                            self.audio_queue.put_nowait(mono)
                        except queue.Empty:
                            pass
                except Exception:
                    pass

            self.running = True
            self.stream = sd.InputStream(  # type: ignore[attr-defined]
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                channels=2,
                dtype='float32',
                device=dev,
                callback=callback,
                extra_settings=settings
            )
            self.stream.start()
        except Exception:
            self.running = False
            self.stream = None

    def stop(self):
        self.running = False
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
        except Exception:
            pass
        self.stream = None

    def get_audio_data(self):
        if not self.running:
            return None
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def get_device_name(self):
        return self.device_name or "WASAPI loopback"


class MacSoundDeviceCapture:
    """macOS capture via sounddevice.

    Tries to locate a loopback-style device (BlackHole / Loopback). Otherwise falls back to default input.
    NOTE: True system output capture on macOS generally requires installing a virtual device.
    """
    PREFERRED_KEYWORDS = ["blackhole", "loopback", "aggregate"]

    def __init__(self, sample_rate: int = 44100, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=5)
        self.stream = None
        self.running = False
        self.device_name = None
        self.device_index = None

    def _pick_device(self):
        try:
            devices = sd.query_devices()  # type: ignore[attr-defined]
            # Search for preferred loopback style device
            for idx, d in enumerate(devices):
                name = (d.get('name') or '').lower()
                if any(k in name for k in self.PREFERRED_KEYWORDS) and d.get('max_input_channels', 0) > 0:
                    self.device_index = idx
                    self.device_name = d.get('name', 'loopback')
                    return
            # Fallback: default input
            default_in = sd.default.device[0] if hasattr(sd, 'default') else None  # type: ignore
            if default_in is not None and default_in >= 0:
                info = sd.query_devices(default_in)
                self.device_index = default_in
                self.device_name = info.get('name', 'default input')
                return
            # Last resort: first input device
            for idx, d in enumerate(devices):
                if d.get('max_input_channels', 0) > 0:
                    self.device_index = idx
                    self.device_name = d.get('name', f'device_{idx}')
                    return
            # No device found
            print("macOS audio: No input device found", file=sys.stderr)
        except Exception as e:
            print(f"macOS audio: Error selecting device: {e}", file=sys.stderr)

    def start(self):
        if sd is None or self.running:
            return
        self._pick_device()
        if self.device_index is None:
            print("macOS audio: Cannot start - no device available", file=sys.stderr)
            return
        def callback(indata, frames, time_, status):
            if status:
                pass
            if not self.running:
                return
            try:
                if indata.ndim == 2 and indata.shape[1] > 1:
                    mono = np.mean(indata, axis=1)
                else:
                    mono = indata[:, 0] if indata.ndim == 2 else indata
                mono = mono.astype(np.float32)
                if len(mono) < self.chunk_size:
                    mono = np.pad(mono, (0, self.chunk_size - len(mono)))
                elif len(mono) > self.chunk_size:
                    mono = mono[:self.chunk_size]
                try:
                    self.audio_queue.put_nowait(mono)
                except queue.Full:
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put_nowait(mono)
                    except queue.Empty:
                        pass
            except Exception as e:
                if self.running:
                    print(f"macOS audio: Callback error: {e}", file=sys.stderr)
        try:
            self.running = True
            self.stream = sd.InputStream(  # type: ignore[attr-defined]
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                channels=2,
                dtype='float32',
                device=self.device_index,
                callback=callback
            )
            self.stream.start()
        except Exception as e:
            print(f"macOS audio: Failed to start stream: {e}", file=sys.stderr)
            print(f"macOS audio: This may be a microphone permission issue", file=sys.stderr)
            self.running = False
            self.stream = None

    def stop(self):
        self.running = False
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
        except Exception:
            pass
        self.stream = None

    def get_audio_data(self):
        if not self.running:
            return None
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def get_device_name(self):
        return self.device_name or "input"


def create_audio_capture(sample_rate: int = 44100, chunk_size: int = 1024):
    plat = sys.platform
    if plat.startswith('linux'):
        from .parec_audio import ParecAudioCapture  # local import to keep fast path
        return ParecAudioCapture(sample_rate=sample_rate, chunk_size=chunk_size)
    if plat == 'win32':
        if sd is not None:
            cap = WASAPILoopbackCapture(sample_rate=sample_rate, chunk_size=chunk_size)
            return cap
        print("Windows: sounddevice not available, using silent mode", file=sys.stderr)
        return SilentAudioCapture()
    if plat == 'darwin':
        if sd is not None:
            return MacSoundDeviceCapture(sample_rate=sample_rate, chunk_size=chunk_size)
        print("macOS: sounddevice not available, using silent mode", file=sys.stderr)
        print("macOS: Install with: pip install sounddevice", file=sys.stderr)
        return SilentAudioCapture()
    # Unknown platform fallback
    return SilentAudioCapture()

