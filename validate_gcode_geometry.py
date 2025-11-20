#!/usr/bin/env python3
"""
Validate G-code geometry - show detailed cross-sections and check for errors
"""
import re
import numpy as np
from collections import defaultdict

def parse_gcode_detailed(filename):
    """Parse G-code and extract all extrusion moves"""
    positions = []
    current_pos = {'X': 0, 'Y': 0, 'Z': 0}

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip().split(';')[0]
            if not line:
                continue

            # Parse G0/G1 commands - update position from both
            if line.startswith('G0') or line.startswith('G1'):
                x_match = re.search(r'X([-\d.]+)', line)
                y_match = re.search(r'Y([-\d.]+)', line)
                z_match = re.search(r'Z([-\d.]+)', line)

                if x_match:
                    current_pos['X'] = float(x_match.group(1))
                if y_match:
                    current_pos['Y'] = float(y_match.group(1))
                if z_match:
                    current_pos['Z'] = float(z_match.group(1))

            # Only record extrusion moves
            if line.startswith('G1') and 'E' in line:
                positions.append((current_pos['X'], current_pos['Y'], current_pos['Z']))

    return np.array(positions)

def check_geometry_issues(positions):
    """Check for common geometry issues"""
    print("\n" + "="*80)
    print("GEOMETRY VALIDATION")
    print("="*80)

    # Find bounds
    min_coords = positions.min(axis=0)
    max_coords = positions.max(axis=0)
    dims = max_coords - min_coords

    print(f"\nBounding box:")
    print(f"  X: [{min_coords[0]:.2f}, {max_coords[0]:.2f}] → {dims[0]:.2f}mm")
    print(f"  Y: [{min_coords[1]:.2f}, {max_coords[1]:.2f}] → {dims[1]:.2f}mm")
    print(f"  Z: [{min_coords[2]:.2f}, {max_coords[2]:.2f}] → {dims[2]:.2f}mm")

    # Check for positions outside expected cylinder
    expected_radius = 6.0  # 12mm diameter
    radii = np.sqrt(positions[:, 0]**2 + positions[:, 1]**2)
    outside_cylinder = radii > expected_radius + 0.5

    if np.any(outside_cylinder):
        print(f"\n⚠ WARNING: {np.sum(outside_cylinder)} points outside expected cylinder!")
        print(f"  Expected radius: {expected_radius:.1f}mm")
        print(f"  Max radius found: {radii.max():.2f}mm")
        print(f"  Sample outliers:")
        outlier_idx = np.where(outside_cylinder)[0][:5]
        for idx in outlier_idx:
            x, y, z = positions[idx]
            r = np.sqrt(x**2 + y**2)
            print(f"    Z={z:.1f}mm: (X={x:.2f}, Y={y:.2f}) r={r:.2f}mm")

    # Check for overlapping/intersecting paths
    return dims

def plot_cross_section(positions, z_target, tolerance=0.1, width=70, height=35):
    """Show detailed ASCII cross-section at a specific Z height"""
    # Get points near this Z
    mask = np.abs(positions[:, 2] - z_target) < tolerance
    layer_points = positions[mask]

    if len(layer_points) == 0:
        return f"No data at Z={z_target:.1f}mm"

    xs = layer_points[:, 0]
    ys = layer_points[:, 1]

    # Calculate bounds
    extent = 8  # Show ±8mm
    min_x, max_x = -extent, extent
    min_y, max_y = -extent, extent

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Plot circle outline for reference (expected cylinder)
    for i in range(width):
        for j in range(height):
            x = min_x + (i / (width-1)) * (max_x - min_x)
            y = max_y - (j / (height-1)) * (max_y - min_y)
            r = np.sqrt(x**2 + y**2)
            if 5.8 < r < 6.2:  # Cylinder radius ±0.2mm
                grid[j][i] = '·'

    # Plot actual points
    for x, y in zip(xs, ys):
        grid_x = int((x - min_x) / (max_x - min_x) * (width - 1))
        grid_y = int((max_y - y) / (max_y - min_y) * (height - 1))

        if 0 <= grid_x < width and 0 <= grid_y < height:
            r = np.sqrt(x**2 + y**2)
            if r > 6.5:
                grid[grid_y][grid_x] = 'X'  # Outside cylinder
            else:
                grid[grid_y][grid_x] = '█'

    # Add axes
    zero_x = int((0 - min_x) / (max_x - min_x) * (width - 1))
    zero_y = int((max_y - 0) / (max_y - min_y) * (height - 1))

    for i in range(height):
        if grid[i][zero_x] in [' ', '·']:
            grid[i][zero_x] = '│'
    for j in range(width):
        if grid[zero_y][j] in [' ', '·']:
            grid[zero_y][j] = '─'
    grid[zero_y][zero_x] = '┼'

    # Build output
    result = [f"\nZ = {z_target:.1f}mm ({len(layer_points)} points)"]
    result.append("┌" + "─" * width + "┐")
    for row in grid:
        result.append("│" + ''.join(row) + "│")
    result.append("└" + "─" * width + "┘")
    result.append(f"  · = expected cylinder outline   █ = actual   X = OUTSIDE")

    # Calculate statistics
    radii = np.sqrt(xs**2 + ys**2)
    result.append(f"  Radii: min={radii.min():.2f}, max={radii.max():.2f}, mean={radii.mean():.2f}mm")

    # Check for gaps/openings
    angles = np.arctan2(ys, xs)
    angles_deg = np.degrees(angles)
    angles_deg[angles_deg < 0] += 360
    angles_sorted = np.sort(angles_deg)

    # Find largest angular gap
    if len(angles_sorted) > 1:
        gaps = np.diff(angles_sorted)
        max_gap_idx = np.argmax(gaps)
        max_gap = gaps[max_gap_idx]
        gap_start = angles_sorted[max_gap_idx]
        gap_end = angles_sorted[max_gap_idx + 1]

        if max_gap > 30:
            result.append(f"  *** OPENING: {max_gap:.0f}° gap from {gap_start:.0f}° to {gap_end:.0f}° ***")

    return '\n'.join(result)

# Main
import sys
if len(sys.argv) < 2:
    print("Usage: python validate_gcode_geometry.py <gcode_file>")
    sys.exit(1)

filename = sys.argv[1]
print(f"Analyzing {filename}...")

positions = parse_gcode_detailed(filename)
print(f"Total extrusion points: {len(positions)}")

dims = check_geometry_issues(positions)

# Show cross-sections at key Z heights
print("\n" + "="*80)
print("CROSS-SECTIONS")
print("="*80)

key_heights = [1, 3, 5, 10, 12, 15, 18, 20, 25, 30]
for z in key_heights:
    if z <= positions[:, 2].max():
        print(plot_cross_section(positions, z, tolerance=0.15))

print("\n" + "="*80)
print("VALIDATION COMPLETE")
print("="*80)
