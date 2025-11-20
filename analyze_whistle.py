import numpy as np
import struct

def read_binary_stl(filename):
    """Read a binary STL file and extract vertices."""
    with open(filename, 'rb') as f:
        # Read header (80 bytes)
        header = f.read(80)

        # Read number of triangles
        num_triangles = struct.unpack('I', f.read(4))[0]

        print(f"STL File: {filename}")
        print(f"Header: {header.decode('ascii', errors='ignore').strip()}")
        print(f"Number of triangles: {num_triangles}")

        vertices = []
        normals = []

        for i in range(num_triangles):
            # Normal vector (3 floats)
            normal = struct.unpack('fff', f.read(12))
            normals.append(normal)

            # Three vertices (3 * 3 floats)
            v1 = struct.unpack('fff', f.read(12))
            v2 = struct.unpack('fff', f.read(12))
            v3 = struct.unpack('fff', f.read(12))

            vertices.extend([v1, v2, v3])

            # Attribute byte count (usually 0)
            f.read(2)

        return np.array(vertices), np.array(normals)

# Analyze the whistle geometry
vertices, normals = read_binary_stl('whistle.stl')

print(f"\nTotal vertices: {len(vertices)}")
print(f"Total normals: {len(normals)}")

# Get bounding box
min_coords = vertices.min(axis=0)
max_coords = vertices.max(axis=0)
dimensions = max_coords - min_coords

print(f"\nBounding Box:")
print(f"  Min: {min_coords}")
print(f"  Max: {max_coords}")
print(f"  Dimensions (XYZ): {dimensions}")
print(f"  Width (X): {dimensions[0]:.2f} mm")
print(f"  Depth (Y): {dimensions[1]:.2f} mm")
print(f"  Height (Z): {dimensions[2]:.2f} mm")

# Find unique Z levels to identify key features
z_coords = vertices[:, 2]
unique_z = np.unique(np.round(z_coords, 2))

print(f"\nUnique Z levels: {len(unique_z)}")

# Analyze throat geometry - look for vertices in the middle section
# The throat is typically where air is compressed before exiting
middle_z = (min_coords[2] + max_coords[2]) / 2

# Get vertices near the middle
tolerance = dimensions[2] * 0.2
middle_vertices = vertices[np.abs(vertices[:, 2] - middle_z) < tolerance]

print(f"\nMiddle section analysis (Z ≈ {middle_z:.2f}):")
print(f"  Number of vertices: {len(middle_vertices)}")

if len(middle_vertices) > 0:
    # Find the throat opening (smallest cross-section)
    # This is typically the narrowest part in X or Y
    middle_x_range = middle_vertices[:, 0].max() - middle_vertices[:, 0].min()
    middle_y_range = middle_vertices[:, 1].max() - middle_vertices[:, 1].min()

    print(f"  X range: {middle_x_range:.2f} mm")
    print(f"  Y range: {middle_y_range:.2f} mm")

# Look for angled surfaces by examining normals
# Whistle throats typically have angled surfaces for directing air
print(f"\nNormal vector analysis:")
print(f"  Sample normals (first 5):")
for i in range(min(5, len(normals))):
    angle_from_z = np.degrees(np.arccos(abs(normals[i][2])))
    print(f"    Normal {i}: {normals[i]}, Angle from Z-axis: {angle_from_z:.1f}°")

# Find vertices with specific Y coordinates (front/back of whistle)
front_vertices = vertices[vertices[:, 1] == vertices[:, 1].max()]
back_vertices = vertices[vertices[:, 1] == vertices[:, 1].min()]

print(f"\nFront section (max Y): {len(front_vertices)} vertices")
print(f"Back section (min Y): {len(back_vertices)} vertices")

# Analyze the mouth opening (entrance for air)
# Typically at one end
bottom_vertices = vertices[np.abs(vertices[:, 2] - min_coords[2]) < 0.5]
top_vertices = vertices[np.abs(vertices[:, 2] - max_coords[2]) < 0.5]

print(f"\nBottom vertices (mouth area): {len(bottom_vertices)}")
print(f"Top vertices: {len(top_vertices)}")

# Estimate throat angle by looking at vertices that form the ramp
# The whistle works by having air flow over an angled edge
print(f"\nKey measurements for FullControl design:")
print(f"  Overall length: {dimensions[1]:.2f} mm")
print(f"  Overall diameter: {max(dimensions[0], dimensions[2]):.2f} mm")
print(f"  Estimated throat depth: {dimensions[1] * 0.3:.2f} mm")
print(f"  Estimated throat height: {dimensions[2] * 0.4:.2f} mm")

# Find vertices that might represent the air channel
# These are typically internal voids, so we look for edges
print(f"\nSearching for throat angle...")

# Group vertices by Z level and analyze Y positions
z_levels = np.linspace(min_coords[2], max_coords[2], 20)
for i, z in enumerate(z_levels[5:15]):  # Check middle section
    level_verts = vertices[np.abs(vertices[:, 2] - z) < 0.5]
    if len(level_verts) > 0:
        y_min = level_verts[:, 1].min()
        y_max = level_verts[:, 1].max()
        if i == 0:
            prev_y_min = y_min
        else:
            # Calculate angle of slope
            dz = z_levels[1] - z_levels[0]
            dy = y_min - prev_y_min
            if dz > 0:
                angle = np.degrees(np.arctan(dy / dz))
                if abs(angle) > 5:  # Only print significant angles
                    print(f"  Z={z:.2f}: throat angle ≈ {angle:.1f}° from vertical")
            prev_y_min = y_min
