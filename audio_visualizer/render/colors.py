"""Color management utilities for the visualizer.

Provides color scheme definitions and color selection based on
intensity level and position across the visualization.
"""
import curses
from typing import List

# Available color scheme names
SCHEMES: List[str] = [
    "multicolor",  # Dynamic blend of green/yellow/red
    "blue",        # Blue gradient  
    "green",       # Green/yellow gradient
    "red",         # Yellow/red gradient
    "rainbow",     # Full spectrum by position
    "fire",        # Red/yellow/white flame effect
    "prism",       # Six-color spectrum
    "heat",        # Blue->green->yellow->red heatmap
    "ocean",       # Cyan/blue/white waves
]

# Color pair mapping (matches curses init in smooth_visualizer)
# 1=Blue, 2=Cyan, 3=Green, 4=Yellow, 5=Red, 6=Magenta, 7=White
_BLUE, _CYAN, _GREEN, _YELLOW, _RED, _MAGENTA, _WHITE = range(1, 8)


def init_colors() -> None:
    """Initialize curses color pairs if terminal supports colors."""
    if not curses.has_colors():
        return
    curses.start_color()
    # Color pairs are initialized in smooth_visualizer._init_colors()


def get_color(level: float, position: float, scheme: str) -> int:
    """Get curses color attribute for given intensity and position.
    
    Args:
        level: Intensity level 0.0-1.0 (louder = higher)
        position: Horizontal position 0.0-1.0 (left to right)
        scheme: Color scheme name from SCHEMES
    
    Returns:
        Curses color attribute (color_pair with optional attributes)
    """
    if not curses.has_colors():
        return 0
    
    level = max(0.0, min(1.0, level))
    position = max(0.0, min(1.0, position))
    C = curses.color_pair

    # Scheme-specific color selection
    if scheme == "prism":
        # Six-band spectrum across position
        idx = int(position * 5.99)
        colors = [_RED, _YELLOW, _GREEN, _CYAN, _BLUE, _MAGENTA]
        return C(colors[idx])

    if scheme == "rainbow":
        # Five-band spectrum across position
        idx = int(position * 4.99)
        colors = [_RED, _YELLOW, _GREEN, _CYAN, _BLUE]
        return C(colors[idx])

    if scheme == "multicolor":
        # Dynamic blend based on level + position
        blend = level * 0.5 + position * 0.5
        if blend < 0.33:
            return C(_GREEN)
        if blend < 0.66:
            return C(_YELLOW)
        return C(_RED)

    if scheme == "blue":
        # Blue intensity gradient
        if level < 0.3:
            return C(_BLUE)
        if level < 0.7:
            return C(_CYAN)
        return C(_WHITE)

    if scheme == "green":
        # Green to yellow
        return C(_YELLOW) if level >= 0.5 else C(_GREEN)

    if scheme == "red":
        # Yellow to red
        return C(_RED) if level >= 0.5 else C(_YELLOW)

    if scheme == "fire":
        # Flame: red -> yellow -> white
        if level < 0.3:
            return C(_RED)
        if level < 0.6:
            return C(_YELLOW)
        return C(_WHITE)

    if scheme == "heat":
        # Thermal: blue -> green -> yellow -> red
        if level < 0.25:
            return C(_BLUE)
        if level < 0.5:
            return C(_GREEN)
        if level < 0.75:
            return C(_YELLOW)
        return C(_RED)

    if scheme == "ocean":
        # Wave: cyan -> blue -> white across position
        if position < 0.33:
            return C(_CYAN)
        if position < 0.66:
            return C(_BLUE)
        return C(_WHITE)

    # Default fallback
    return C(_GREEN)
