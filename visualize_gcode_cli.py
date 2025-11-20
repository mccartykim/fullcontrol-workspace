#!/usr/bin/env python3
"""
CLI G-code visualizer - shows ASCII cross-sections at different Z heights
"""
import sys
import re
from collections import defaultdict

def parse_gcode(filename):
    """Parse G-code file and extract positions"""
    positions_by_layer = defaultdict(list)
    current_pos = {'X': 0, 'Y': 0, 'Z': 0}

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip().split(';')[0]  # Remove comments
            if not line:
                continue

            # Parse G0/G1 commands
            if line.startswith('G0') or line.startswith('G1'):
                # Extract coordinates
                x_match = re.search(r'X([-\d.]+)', line)
                y_match = re.search(r'Y([-\d.]+)', line)
                z_match = re.search(r'Z([-\d.]+)', line)

                if x_match:
                    current_pos['X'] = float(x_match.group(1))
                if y_match:
                    current_pos['Y'] = float(y_match.group(1))
                if z_match:
                    current_pos['Z'] = float(z_match.group(1))

                # Store position for this Z layer
                z_key = round(current_pos['Z'], 1)
                if line.startswith('G1'):  # Only extrusion moves
                    positions_by_layer[z_key].append((current_pos['X'], current_pos['Y']))

    return positions_by_layer

def ascii_plot_layer(positions, z_height, width=80, height=40):
    """Create ASCII art plot of a layer"""
    if not positions:
        return f"No data at Z={z_height:.1f}mm"

    # Find bounds
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Add margin
    margin = 1
    min_x -= margin
    max_x += margin
    min_y -= margin
    max_y += margin

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Plot positions
    for x, y in positions:
        # Map to grid coordinates
        grid_x = int((x - min_x) / (max_x - min_x) * (width - 1))
        grid_y = int((y - min_y) / (max_y - min_y) * (height - 1))
        grid_y = height - 1 - grid_y  # Flip Y axis

        if 0 <= grid_x < width and 0 <= grid_y < height:
            grid[grid_y][grid_x] = '█'

    # Add axes
    for i in range(height):
        grid[i][width//2] = '│' if grid[i][width//2] == ' ' else grid[i][width//2]
    for j in range(width):
        grid[height//2][j] = '─' if grid[height//2][j] == ' ' else grid[height//2][j]
    grid[height//2][width//2] = '┼'

    # Convert to string
    result = [f"Z = {z_height:.1f}mm (X: {min_x:.1f} to {max_x:.1f}, Y: {min_y:.1f} to {max_y:.1f})"]
    result.append('┌' + '─' * width + '┐')
    for row in grid:
        result.append('│' + ''.join(row) + '│')
    result.append('└' + '─' * width + '┘')

    return '\n'.join(result)

def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_gcode_cli.py <gcode_file> [z_heights...]")
        print("Example: python visualize_gcode_cli.py whistle.gcode 0.2 5 10 15 20")
        sys.exit(1)

    filename = sys.argv[1]

    print(f"Parsing {filename}...")
    layers = parse_gcode(filename)

    available_z = sorted(layers.keys())
    print(f"Found {len(available_z)} layers")
    print(f"Z range: {min(available_z):.1f} to {max(available_z):.1f}mm")

    # Determine which layers to show
    if len(sys.argv) > 2:
        # User specified Z heights
        target_z = [float(z) for z in sys.argv[2:]]
    else:
        # Show a selection of layers
        num_samples = 8
        step = len(available_z) // num_samples
        target_z = [available_z[i * step] for i in range(num_samples)]

    # Show each layer
    for z in target_z:
        # Find closest actual Z
        closest_z = min(available_z, key=lambda x: abs(x - z))
        positions = layers[closest_z]

        print("\n" + "="*80)
        print(ascii_plot_layer(positions, closest_z, width=70, height=30))
        print(f"Points at this layer: {len(positions)}")

if __name__ == '__main__':
    main()
