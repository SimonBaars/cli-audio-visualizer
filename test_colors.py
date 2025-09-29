#!/usr/bin/env python3
"""Test color functionality"""

import curses
import sys
import time

def test_colors(stdscr):
    curses.curs_set(0)
    
    # Initialize colors
    try:
        curses.use_default_colors()
    except:
        pass  # Some terminals don't support this
    
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)
        curses.init_pair(7, curses.COLOR_WHITE, -1)
    
    stdscr.clear()
    stdscr.addstr(0, 0, "Color Test", curses.color_pair(6) | curses.A_BOLD)
    stdscr.addstr(2, 0, "Testing color pairs:")
    
    # Test each color
    colors = [
        (1, "BLUE", curses.COLOR_BLUE),
        (2, "CYAN", curses.COLOR_CYAN),
        (3, "GREEN", curses.COLOR_GREEN),
        (4, "YELLOW", curses.COLOR_YELLOW),
        (5, "RED", curses.COLOR_RED),
        (6, "MAGENTA", curses.COLOR_MAGENTA),
        (7, "WHITE", curses.COLOR_WHITE),
    ]
    
    for i, (pair, name, _) in enumerate(colors):
        stdscr.addstr(4 + i, 0, f"{name}: ", curses.color_pair(7))
        stdscr.addstr(4 + i, 12, "████████", curses.color_pair(pair))
    
    stdscr.addstr(13, 0, "Test multicolor gradient:")
    
    # Test gradient (green -> yellow -> red)
    width = 60
    for col in range(width):
        level = col / width
        if level < 0.4:
            color = curses.color_pair(3)  # Green
        elif level < 0.7:
            color = curses.color_pair(4)  # Yellow
        else:
            color = curses.color_pair(5)  # Red
        
        stdscr.addch(14, col, ord('█'), color)
    
    stdscr.addstr(16, 0, "Press Q to quit", curses.color_pair(4))
    stdscr.refresh()
    
    # Wait for key
    stdscr.timeout(5000)
    key = stdscr.getch()
    
    return 0

if __name__ == "__main__":
    sys.exit(curses.wrapper(test_colors))