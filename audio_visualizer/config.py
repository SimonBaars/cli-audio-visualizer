"""Configuration management for the audio visualizer."""

import json
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Manages configuration persistence for the audio visualizer."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".cli-audio-visualizer"
        self.config_file = self.config_dir / "config.json"
        self.default_config = {
            "last_visualization": "bars",
            "colors": True,
            "sensitivity": 1.0,
            "smoothing": 0.5,
            "fps": 30
        }
        self._config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except (json.JSONDecodeError, IOError):
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file."""
        self.config_dir.mkdir(exist_ok=True)
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError:
            # Silently fail if we can't save config
            pass
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value and save."""
        self._config[key] = value
        self.save_config()
    
    @property
    def last_visualization(self) -> str:
        """Get the last used visualization mode."""
        return self.get("last_visualization", "bars")
    
    @last_visualization.setter
    def last_visualization(self, value: str):
        """Set the last used visualization mode."""
        self.set("last_visualization", value)