"""Background rendering utilities for visualizer modes.

Each background renderer should be lightweight (O(width*height)) or maintain
its own minimal state for animation. All functions mutate the screen directly.
"""
from __future__ import annotations
import curses
import random

BACKGROUND_NAMES = [
    'none',
    'dots',
    'grid',
    'gradient',
    'stars',
    'palm'
]

SHADE = [' ', '░', '▒', '▓', '█']


def _safe_addch(stdscr, y, x, ch, attr=0):
    try:
        stdscr.addch(y, x, ch, attr)
    except curses.error:
        pass


def draw_background(stdscr, width: int, height: int, state: dict, bg_index: int, get_color_func):
    """Dispatch to selected background. Always clears screen area first (full paint)."""
    if bg_index <= 0 or bg_index >= len(BACKGROUND_NAMES):
        # Clear to spaces (acts as 'none')
        for row in range(height):
            try:
                stdscr.move(row, 0)
                stdscr.clrtoeol()
            except curses.error:
                pass
        return

    name = BACKGROUND_NAMES[bg_index]
    # Clear first
    for row in range(height):
        try:
            stdscr.move(row, 0)
            stdscr.clrtoeol()
        except curses.error:
            pass

    if name == 'dots':
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                _safe_addch(stdscr, y, x, ord('·'), curses.color_pair(7) | curses.A_DIM)
    elif name == 'grid':
        for y in range(height):
            is_row = (y % 4 == 0)
            for x in range(width):
                if is_row or (x % 8 == 0):
                    _safe_addch(stdscr, y, x, ord('·'), curses.color_pair(7) | curses.A_DIM)
    elif name == 'gradient':
        for y in range(height):
            t = y / max(1, height - 1)
            shade_idx = min(len(SHADE)-1, int(t * (len(SHADE)-1)))
            ch = SHADE[shade_idx]
            for x in range(width):
                if ch != ' ':
                    col = get_color_func(t * 0.8 + 0.2, x / max(1, width - 1))
                    _safe_addch(stdscr, y, x, ord(ch), col)
    elif name == 'stars':
        # Animated sparse star field (stored in state)
        stars = state.get('bg_stars')
        if stars is None or len(stars) < 60 or width != state.get('bg_w') or height != state.get('bg_h'):
            stars = []
            for _ in range(120):
                stars.append([random.randint(0, width-1), random.randint(0, height-1), random.choice(['·','·','✦','*'])])
        # Drift
        for s in stars:
            if random.random() < 0.12:
                s[0] = (s[0] + 1) % max(1, width)
            if random.random() < 0.08:
                s[1] = (s[1] + 1) % max(1, height)
            ch = s[2]
            _safe_addch(stdscr, s[1], s[0], ord(ch), curses.color_pair(7))
        state['bg_stars'] = stars
        state['bg_w'] = width
        state['bg_h'] = height
    elif name == 'palm':
        art = [
            "    __ _", 
            "   /  / ", 
            "  /--/  ", 
            " /  /   ", 
            "(  (    ", 
            " \  \\   ", 
            "  \  \\  ", 
            "   \  \\ ", 
            "    | | ", 
            "    | | ",
        ]
        # Place at left or center depending on width
        left = 2 if width < 60 else max(2, width//2 - 25)
        top = max(0, height//2 - len(art)//2)
        col = curses.color_pair(3)
        for dy, line in enumerate(art):
            if top+dy >= height:
                break
            for dx, ch in enumerate(line):
                x = left + dx
                if 0 <= x < width and ch != ' ':
                    _safe_addch(stdscr, top+dy, x, ord(ch), col)
    # else: unknown treated as cleared
