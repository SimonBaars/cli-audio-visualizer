"""Circular wave visualizer - circle with waveform modulation."""

import numpy as np
import curses
from .base import clear_area


def draw_circular_wave(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                       get_color_func, apply_smoothing_func, state: dict):
    """Draw actual circle with waveform modulation."""
    # Clear area every frame
    clear_area(stdscr, y_offset, height, width)
    
    # Get waveform  
    num_samples = 60  # Sample points for waveform data
    if len(audio_data) > num_samples:
        step = len(audio_data) // num_samples
        waveform = audio_data[::step][:num_samples]
    else:
        waveform = np.pad(audio_data, (0, num_samples - len(audio_data)), 'constant')
    
    waveform = apply_smoothing_func(waveform, True)
    if np.max(np.abs(waveform)) > 0:
        waveform = waveform / np.max(np.abs(waveform))
    
    center_y = height // 2
    center_x = width // 2
    base_radius = min(height // 2 - 2, width // 3)
    
    # Calculate perimeter to determine how many points we need
    perimeter = int(2 * np.pi * base_radius * 1.5)  # Overestimate for good coverage
    num_draw_points = max(perimeter, 200)  # At least 200 points for smooth circle
    
    # Draw full circle with line segments between points
    prev_x, prev_y = None, None
    
    # Overall energy for extra effects
    energy = float(np.mean(np.abs(waveform))) if len(waveform) else 0.0
    energy_sm = state.get('energy_sm', energy)
    energy_sm = 0.9 * energy_sm + 0.1 * energy
    state['energy_sm'] = energy_sm

    for i in range(num_draw_points + 1):  # +1 to close the circle
        angle = (i / num_draw_points) * 2 * np.pi

        # Sample waveform (interpolate between samples)
        waveform_idx = int((i / num_draw_points) * num_samples) % num_samples
        wave_offset = waveform[waveform_idx] * base_radius * 0.7  # more dramatic
        # Smooth abrupt radius jumps using previous radius (store in state)
        prev_r = state.get('prev_radius', base_radius)
        target_r = base_radius + wave_offset
        radius = 0.5 * prev_r + 0.5 * target_r
        state['prev_radius'] = radius
        
        # Calculate position
        x = int(center_x + radius * np.cos(angle))
        y = int(center_y + radius * np.sin(angle) * 0.6)  # Slightly less vertical squish
        
        # Get color
        position = i / max(1, num_draw_points - 1)
        intensity = abs(wave_offset / base_radius) if base_radius > 0 else 0
    color = get_color_func(intensity * 0.7 + energy_sm * 0.3, position)
        
        # Draw current point
        simple = state.get('simple_ascii')
        ch_point = '*' if simple else '█'
        if 0 <= x < width and 0 <= y < height:
            try:
                stdscr.addch(y + y_offset, x, ord(ch_point), color)
            except curses.error:
                pass
        
        # Draw line from previous point to current (fill gaps)
        if prev_x is not None and prev_y is not None:
            # Simple line drawing - interpolate between points
            dx = x - prev_x
            dy = y - prev_y
            steps = max(abs(dx), abs(dy))
            
            if steps > 0:
                for step in range(steps + 1):
                    t = step / steps
                    interp_x = int(prev_x + t * dx)
                    interp_y = int(prev_y + t * dy)
                    
                    if 0 <= interp_x < width and 0 <= interp_y < height:
                        try:
                            stdscr.addch(interp_y + y_offset, interp_x, ord(ch_point), color)
                        except curses.error:
                            pass
        
        prev_x, prev_y = x, y

    # Orbiting sparks (small particles moving along circle perimeter)
    sparks = state.get('sparks')
    if sparks is None:
        sparks = []
    # Spawn a few based on energy
    import random, math as _m
    if random.random() < 0.3 + energy_sm * 0.4 and len(sparks) < 120:
        sparks.append({
            'a': random.random() * 2 * _m.pi,
            'speed': (0.02 + energy_sm * 0.08) * (0.5 + random.random()),
            'life': 0,
            'max': 120 + int(random.random() * 120),
            'rad_jitter': random.random() * 0.4
        })
    new_sparks = []
    for sp in sparks:
        sp['a'] += sp['speed']
        sp['life'] += 1
        if sp['life'] < sp['max']:
            new_sparks.append(sp)
            rr = base_radius * (1 + 0.08 * np.sin(sp['life'] * 0.2) + 0.05 * sp['rad_jitter'])
            sx = int(center_x + rr * np.cos(sp['a']))
            sy = int(center_y + rr * np.sin(sp['a']) * 0.6)
            if 0 <= sx < width and 0 <= sy < height:
                life_ratio = sp['life'] / sp['max']
                spark_int = min(1.0, (1 - life_ratio) * 1.2)
                c = get_color_func(spark_int, (np.cos(sp['a']) + 1)/2)
                try:
                    stdscr.addch(sy + y_offset, sx, ord('*' if state.get('simple_ascii') else '✦'), c)
                except curses.error:
                    pass
    state['sparks'] = new_sparks

    # Pulsing inner ring ( faint )
    inner_r = int(base_radius * (0.55 + 0.1 * np.sin(energy_sm * 10 + center_x)))
    for a_i in range(0, 360, 8):
        a = np.deg2rad(a_i)
        x = int(center_x + inner_r * np.cos(a))
        y = int(center_y + inner_r * np.sin(a) * 0.6)
        if 0 <= x < width and 0 <= y < height:
            try:
                stdscr.addch(y + y_offset, x, ord('.'), get_color_func(energy_sm * 0.5 + 0.1, (a_i/360)))
            except curses.error:
                pass

    # Radial rays (sporadic)
    rays = state.get('rays')
    if rays is None:
        rays = []
    if random.random() < 0.05 + energy_sm * 0.1 and len(rays) < 12:
        rays.append({'a': random.random() * 2 * _m.pi, 'life':0, 'max': 25 + int(random.random()*25)})
    new_rays = []
    for r in rays:
        r['life'] += 1
        if r['life'] < r['max']:
            new_rays.append(r)
            frac = r['life'] / r['max']
            length = int(base_radius * 0.3 + frac * base_radius * 0.7)
            dx = np.cos(r['a'])
            dy = np.sin(r['a']) * 0.6
            for step in range(length):
                rx = int(center_x + dx * step)
                ry = int(center_y + dy * step)
                if 0 <= rx < width and 0 <= ry < height:
                    inten = (1-frac) * (step/length)
                    c = get_color_func(inten, (dx+1)/2)
                    try:
                        stdscr.addch(ry + y_offset, rx, ord('|' if state.get('simple_ascii') else '·'), c)
                    except curses.error:
                        pass
    state['rays'] = new_rays

    # Energy halo dots
    halo_count = int(40 + energy_sm * 120)
    rng = np.random.random
    for _ in range(halo_count):
        a = rng() * 2 * np.pi
        rr = base_radius * (1.05 + 0.35 * rng())
        hx = int(center_x + rr * np.cos(a))
        hy = int(center_y + rr * np.sin(a) * 0.6)
        if 0 <= hx < width and 0 <= hy < height:
            lvl = 0.2 + 0.8 * rng() * energy_sm
            try:
                stdscr.addch(hy + y_offset, hx, ord('.'), get_color_func(lvl, (np.cos(a)+1)/2))
            except curses.error:
                pass