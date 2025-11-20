#!/usr/bin/env python3
"""
Analyze and visualize STL file from multiple angles
Shows ASCII art views from different perspectives
"""
import numpy as np
import struct

def read_binary_stl(filename):
    """Read a binary STL file and extract vertices."""
    with open(filename, 'rb') as f:
        header = f.read(80)
        num_triangles = struct.unpack('I', f.read(4))[0]

        vertices = []
        for i in range(num_triangles):
            normal = struct.unpack('fff', f.read(12))
            v1 = struct.unpack('fff', f.read(12))
            v2 = struct.unpack('fff', f.read(12))
            v3 = struct.unpack('fff', f.read(12))
            vertices.extend([v1, v2, v3])
            f.read(2)

        return np.array(vertices)

def ascii_plot_2d(points_2d, title, width=80, height=40, x_label='X', y_label='Y'):
    """Create ASCII art plot of 2D points"""
    if len(points_2d) == 0:
        return f"No data for {title}"

    xs = points_2d[:, 0]
    ys = points_2d[:, 1]

    min_x, max_x = xs.min(), xs.max()
    min_y, max_y = ys.min(), ys.max()

    # Add margin
    margin = max(max_x - min_x, max_y - min_y) * 0.1
    min_x -= margin
    max_x += margin
    min_y -= margin
    max_y += margin

    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Plot points
    for x, y in zip(xs, ys):
        grid_x = int((x - min_x) / (max_x - min_x) * (width - 1))
        grid_y = int((y - min_y) / (max_y - min_y) * (height - 1))
        grid_y = height - 1 - grid_y  # Flip Y

        if 0 <= grid_x < width and 0 <= grid_y < height:
            grid[grid_y][grid_x] = '█'

    # Add axes
    zero_x = int((0 - min_x) / (max_x - min_x) * (width - 1))
    zero_y = height - 1 - int((0 - min_y) / (max_y - min_y) * (height - 1))

    for i in range(height):
        if 0 <= zero_x < width:
            if grid[i][zero_x] == ' ':
                grid[i][zero_x] = '│'
    for j in range(width):
        if 0 <= zero_y < height:
            if grid[zero_y][j] == ' ':
                grid[zero_y][j] = '─'
    if 0 <= zero_x < width and 0 <= zero_y < height:
        grid[zero_y][zero_x] = '┼'

    # Build output
    result = [f"\n{title}"]
    result.append(f"Range: {x_label}=[{min_x:.1f}, {max_x:.1f}], {y_label}=[{min_y:.1f}, {max_y:.1f}]")
    result.append('┌' + '─' * width + '┐')
    for row in grid:
        result.append('│' + ''.join(row) + '│')
    result.append('└' + '─' * width + '┘')
    result.append(f"   {x_label} axis →     (0 at center lines)")

    return '\n'.join(result)

def analyze_slices(vertices, axis_idx, axis_name, num_slices=5):
    """Analyze cross-sections along an axis"""
    axis_values = vertices[:, axis_idx]
    min_val, max_val = axis_values.min(), axis_values.max()

    print(f"\n{'='*80}")
    print(f"CROSS-SECTIONS ALONG {axis_name}-AXIS")
    print(f"{'='*80}")

    slice_positions = np.linspace(min_val, max_val, num_slices)

    for slice_pos in slice_positions:
        # Get vertices near this slice position
        tolerance = (max_val - min_val) / (num_slices * 2)
        mask = np.abs(vertices[:, axis_idx] - slice_pos) < tolerance
        slice_verts = vertices[mask]

        if len(slice_verts) > 0:
            print(f"\n{axis_name} = {slice_pos:.2f}mm ({len(slice_verts)} vertices)")

            # Determine which axes to plot
            if axis_idx == 0:  # Slicing X, plot Y-Z
                other_axes = slice_verts[:, [1, 2]]
                labels = ('Y', 'Z')
            elif axis_idx == 1:  # Slicing Y, plot X-Z
                other_axes = slice_verts[:, [0, 2]]
                labels = ('X', 'Z')
            else:  # Slicing Z, plot X-Y
                other_axes = slice_verts[:, [0, 1]]
                labels = ('X', 'Y')

            print(ascii_plot_2d(other_axes, f"Cross-section at {axis_name}={slice_pos:.2f}mm",
                              width=60, height=25, x_label=labels[0], y_label=labels[1]))

# Main analysis
print("="*80)
print("WHISTLE STL GEOMETRY ANALYSIS")
print("="*80)

vertices = read_binary_stl('whistle.stl')

print(f"\nTotal vertices: {len(vertices)}")

# Get bounding box
min_coords = vertices.min(axis=0)
max_coords = vertices.max(axis=0)
dimensions = max_coords - min_coords

print(f"\nBounding Box:")
print(f"  X: [{min_coords[0]:.2f}, {max_coords[0]:.2f}] → {dimensions[0]:.2f}mm")
print(f"  Y: [{min_coords[1]:.2f}, {max_coords[1]:.2f}] → {dimensions[1]:.2f}mm")
print(f"  Z: [{min_coords[2]:.2f}, {max_coords[2]:.2f}] → {dimensions[2]:.2f}mm")

print(f"\n*** The whistle is longest along the X-axis ({dimensions[0]:.2f}mm) ***")

# Show main orthogonal projections
print("\n" + "="*80)
print("ORTHOGONAL PROJECTIONS (Main Views)")
print("="*80)

# Top view (looking down Z-axis, see X-Y)
print(ascii_plot_2d(vertices[:, [0, 1]], "TOP VIEW (looking down -Z axis, X-Y plane)",
                   width=70, height=30, x_label='X', y_label='Y'))

# Front view (looking along Y-axis, see X-Z)
print(ascii_plot_2d(vertices[:, [0, 2]], "FRONT VIEW (looking along -Y axis, X-Z plane)",
                   width=70, height=30, x_label='X', y_label='Z'))

# Side view (looking along X-axis, see Y-Z)
print(ascii_plot_2d(vertices[:, [1, 2]], "SIDE VIEW (looking along -X axis, Y-Z plane)",
                   width=70, height=30, x_label='Y', y_label='Z'))

# Cross-sections along X axis (length)
analyze_slices(vertices, 0, 'X', num_slices=7)

# Analyze the throat geometry more carefully
print("\n" + "="*80)
print("THROAT GEOMETRY ANALYSIS")
print("="*80)

# The throat should be somewhere in the middle X range
middle_x = (min_coords[0] + max_coords[0]) / 2
# Look at a narrow band around the middle
throat_region = vertices[np.abs(vertices[:, 0] - middle_x) < 5]

print(f"\nThroat region analysis (X ≈ {middle_x:.1f} ± 5mm):")
print(f"  Vertices in region: {len(throat_region)}")

if len(throat_region) > 0:
    throat_y_range = throat_region[:, 1].max() - throat_region[:, 1].min()
    throat_z_range = throat_region[:, 2].max() - throat_region[:, 2].min()
    print(f"  Y range: {throat_y_range:.2f}mm")
    print(f"  Z range: {throat_z_range:.2f}mm")

    # Find the opening - look for vertices on the outer edges
    y_min_verts = throat_region[throat_region[:, 1] == throat_region[:, 1].min()]
    y_max_verts = throat_region[throat_region[:, 1] == throat_region[:, 1].max()]

    print(f"\n  Vertices at Y_min: {len(y_min_verts)}")
    print(f"  Vertices at Y_max: {len(y_max_verts)}")

    print(f"\n  *** The throat opening likely faces ±Y direction ***")
    print(f"  *** The whistle is held horizontally along X-axis ***")

print("\n" + "="*80)
print("INTERPRETATION FOR CYLINDRICAL DESIGN:")
print("="*80)
print("""
Original STL:
  - Main axis: X (34.17mm length, horizontal)
  - Cross-section: 5×5mm square (Y-Z plane)
  - Throat opening: faces ±Y direction
  - Air flows: along +X direction

For vertical cylindrical whistle (Z-up):
  - Main axis should be: Z (vertical)
  - Cross-section: circular (X-Y plane)
  - Throat opening should face: ±Y direction (horizontal)
  - Air should flow: DOWN along Z, then OUT through +Y

CRITICAL FIX NEEDED:
  The throat channel should:
  1. Run VERTICALLY along Z-axis inside the cylinder
  2. Have an OPENING on the SIDE (±Y direction) where air exits
  3. The fipple ramp slopes in the Z direction (vertical)
  4. The labium edge is HORIZONTAL (perpendicular to Z)
""")
