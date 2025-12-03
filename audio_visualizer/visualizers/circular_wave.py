"""Circular wave visualizer - pulsing circle with waveform modulation and particle effects."""

import numpy as np
import curses
from .base import clear_area


def _interpolate_waveform(waveform: np.ndarray, num_points: int) -> np.ndarray:
    """Interpolate waveform to desired number of points."""
    n = len(waveform)
    if n == num_points:
        return waveform
    x_old = np.linspace(0, 1, n)
    x_new = np.linspace(0, 1, num_points)
    return np.interp(x_new, x_old, waveform)


def draw_circular_wave(stdscr, audio_data: np.ndarray, height: int, width: int, y_offset: int,
                       get_color_func, apply_smoothing_func, state: dict):
    """Draw pulsing circle with waveform modulation and orbiting particles."""
    clear_area(stdscr, y_offset, height, width)
    
    # Sample and process waveform
    num_samples = 60
    if len(audio_data) > num_samples:
        step = len(audio_data) // num_samples
        waveform = audio_data[::step][:num_samples]
    else:
        waveform = np.pad(audio_data, (0, max(0, num_samples - len(audio_data))), 'constant')
    
    waveform = apply_smoothing_func(waveform, True)
    max_val = np.max(np.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val
    
    # Geometry
    center_x, center_y = width // 2, height // 2
    base_radius = min(height // 2 - 2, width // 3)
    
    # Smooth energy tracking
    energy = float(np.mean(np.abs(waveform)))
    energy_sm = state.get('energy_sm', energy)
    energy_sm = 0.9 * energy_sm + 0.1 * energy
    state['energy_sm'] = energy_sm
    
    # Precompute circle points
    num_draw_points = max(200, int(2 * np.pi * base_radius * 1.5))
    angles = np.linspace(0, 2 * np.pi, num_draw_points + 1)
    
    # Interpolate waveform to match draw points
    wave_interp = _interpolate_waveform(waveform, num_draw_points + 1)
    wave_offsets = wave_interp * base_radius * 0.7
    
    # Smooth radius transitions
    prev_radii = state.get('prev_radii')
    if prev_radii is None or len(prev_radii) != len(wave_offsets):
        prev_radii = np.full_like(wave_offsets, base_radius)
    target_radii = base_radius + wave_offsets
    radii = 0.5 * prev_radii + 0.5 * target_radii
    state['prev_radii'] = radii.copy()
    
    # Compute all positions vectorized
    aspect = 0.6  # Terminal character aspect ratio compensation
    xs = (center_x + radii * np.cos(angles)).astype(int)
    ys = (center_y + radii * np.sin(angles) * aspect).astype(int)
    
    # Color intensities
    intensities = np.abs(wave_offsets / base_radius) * 0.7 + energy_sm * 0.3
    positions = np.linspace(0, 1, len(angles))
    
    simple = state.get('simple_ascii')
    point_char = ord('*') if simple else ord('█')
    
    # Draw main circle with line interpolation
    prev_x, prev_y = None, None
    for i in range(len(angles)):
        x, y = xs[i], ys[i]
        intensity = min(1.0, intensities[i])
        color = get_color_func(intensity, positions[i])
        
        if 0 <= x < width and 0 <= y < height:
            try:
                stdscr.addch(y + y_offset, x, point_char, color)
            except curses.error:
                pass
        
        # Fill gaps between points
        if prev_x is not None:
            dx, dy = x - prev_x, y - prev_y
            steps = max(abs(dx), abs(dy))
            if steps > 1:
                for step in range(1, steps):
                    t = step / steps
                    ix, iy = int(prev_x + t * dx), int(prev_y + t * dy)
                    if 0 <= ix < width and 0 <= iy < height:
                        try:
                            stdscr.addch(iy + y_offset, ix, point_char, color)
                        except curses.error:
                            pass
        prev_x, prev_y = x, y
    
    # Orbiting sparks - simplified particle system
    rng = np.random.random
    sparks = state.get('sparks', [])
    
    # Spawn based on energy
    spawn_chance = 0.3 + energy_sm * 0.4
    max_sparks = 120
    if rng() < spawn_chance and len(sparks) < max_sparks:
        sparks.append({
            'a': rng() * 2 * np.pi,
            'speed': (0.02 + energy_sm * 0.08) * (0.5 + rng()),
            'life': 0,
            'max': 120 + int(rng() * 120),
            'jitter': rng() * 0.4
        })
    
    # Update and render sparks
    spark_char = ord('*') if simple else ord('✦')
    new_sparks = []
    for sp in sparks:
        sp['a'] += sp['speed']
        sp['life'] += 1
        if sp['life'] < sp['max']:
            new_sparks.append(sp)
            rr = base_radius * (1 + 0.08 * np.sin(sp['life'] * 0.2) + 0.05 * sp['jitter'])
            sx = int(center_x + rr * np.cos(sp['a']))
            sy = int(center_y + rr * np.sin(sp['a']) * aspect)
            if 0 <= sx < width and 0 <= sy < height:
                life_ratio = sp['life'] / sp['max']
                spark_int = min(1.0, (1 - life_ratio) * 1.2)
                color = get_color_func(spark_int, (np.cos(sp['a']) + 1) / 2)
                try:
                    stdscr.addch(sy + y_offset, sx, spark_char, color)
                except curses.error:
                    pass
    state['sparks'] = new_sparks
    
    # Pulsing inner ring
    inner_r = int(base_radius * (0.55 + 0.1 * np.sin(energy_sm * 10)))
    inner_angles = np.arange(0, 360, 8)
    for a_deg in inner_angles:
        a = np.deg2rad(a_deg)
        ix = int(center_x + inner_r * np.cos(a))
        iy = int(center_y + inner_r * np.sin(a) * aspect)
        if 0 <= ix < width and 0 <= iy < height:
            try:
                stdscr.addch(iy + y_offset, ix, ord('.'), 
                           get_color_func(energy_sm * 0.5 + 0.1, a_deg / 360))
            except curses.error:
                pass
    
    # Radial rays - simplified
    rays = state.get('rays', [])
    if rng() < 0.05 + energy_sm * 0.1 and len(rays) < 12:
        rays.append({'a': rng() * 2 * np.pi, 'life': 0, 'max': 25 + int(rng() * 25)})
    
    ray_char = ord('|') if simple else ord('·')
    new_rays = []
    for r in rays:
        r['life'] += 1
        if r['life'] < r['max']:
            new_rays.append(r)
            frac = r['life'] / r['max']
            length = int(base_radius * (0.3 + frac * 0.7))
            dx, dy = np.cos(r['a']), np.sin(r['a']) * aspect
            for step in range(length):
                rx = int(center_x + dx * step)
                ry = int(center_y + dy * step)
                if 0 <= rx < width and 0 <= ry < height:
                    inten = (1 - frac) * (step / max(1, length))
                    try:
                        stdscr.addch(ry + y_offset, rx, ray_char, 
                                   get_color_func(inten, (dx + 1) / 2))
                    except curses.error:
                        pass
    state['rays'] = new_rays
    
    # Energy halo dots
    halo_count = int(40 + energy_sm * 120)
    for _ in range(halo_count):
        a = rng() * 2 * np.pi
        rr = base_radius * (1.05 + 0.35 * rng())
        hx = int(center_x + rr * np.cos(a))
        hy = int(center_y + rr * np.sin(a) * aspect)
        if 0 <= hx < width and 0 <= hy < height:
            try:
                stdscr.addch(hy + y_offset, hx, ord('.'), 
                           get_color_func(0.2 + 0.8 * rng() * energy_sm, (np.cos(a) + 1) / 2))
            except curses.error:
                pass