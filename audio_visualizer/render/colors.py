"""Color management utilities for the visualizer."""
import curses

SCHEMES = ["multicolor", "blue", "green", "red", "rainbow", "fire", "prism", "heat", "ocean"]


def init_colors():
    if not curses.has_colors():
        return
    curses.start_color()
    # Reuse base palette indexes 1..7 already chosen in original code
    # Optionally could define extended pairs if terminal supports it.


def get_color(level: float, position: float, scheme: str) -> int:
    if not curses.has_colors():
        return 0
    level = max(0.0, min(1.0, level))
    position = max(0.0, min(1.0, position))

    # Helper shortcuts
    C = curses.color_pair

    if scheme == "prism":
        if position < 0.16: return C(5)
        if position < 0.32: return C(4)
        if position < 0.48: return C(3)
        if position < 0.64: return C(2)
        if position < 0.80: return C(1)
        return C(6)

    if scheme == "rainbow":
        if position < 0.2: return C(5)
        if position < 0.4: return C(4)
        if position < 0.6: return C(3)
        if position < 0.8: return C(2)
        return C(1)

    if scheme == "multicolor":
        # Blend position + level for more variation
        blend = (level * 0.5 + position * 0.5)
        if blend < 0.33: return C(3)   # Green
        if blend < 0.66: return C(4)   # Yellow
        return C(5)                    # Red

    if scheme == "blue":
        if level < 0.3: return C(1)
        if level < 0.7: return C(2)
        return C(7)

    if scheme == "green":
        if level < 0.5: return C(3)
        return C(4)

    if scheme == "red":
        if level < 0.5: return C(4)
        return C(5)

    if scheme == "fire":
        if level < 0.3: return C(5)
        if level < 0.6: return C(4)
        return C(7)

    if scheme == "heat":
        # Blue -> green -> yellow -> red progression using level only
        if level < 0.25: return C(1)
        if level < 0.5: return C(3)
        if level < 0.75: return C(4)
        return C(5)

    if scheme == "ocean":
        # Cyan/blue/white based more on position for sweeping effect
        if position < 0.33: return C(2)
        if position < 0.66: return C(1)
        return C(7)

    return C(3)
