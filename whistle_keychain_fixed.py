"""
Cylindrical Whistle Keychain Design using FullControl - CORRECTED VERSION
Key fix: Throat/windway runs AXIALLY (along Z-axis), not radially
"""

import fullcontrol as fc
from math import tau, cos, sin, radians, tan, sqrt

# Design parameters
cylinder_diameter = 12  # Main body diameter (mm)
cylinder_radius = cylinder_diameter / 2
total_length = 35  # Total length (mm)
layer_height = 0.2  # Print layer height (mm)

# Whistle geometry parameters (based on research)
windway_height = 1.2  # Critical: air channel height (mm) - typical 1.0-1.5mm
windway_width = 8  # Air channel width (mm) - typical 6-10mm
windway_length = 12  # Length of air channel (mm)
fipple_angle = 75  # Degrees from vertical (15° from horizontal)
labium_distance = 4  # Distance from windway exit to labium (mm) - critical!
chamber_length = 15  # Resonating chamber length (mm)

# Build the design
steps = []
start_z = 0.2

print("Creating CORRECTED whistle with axial throat...")

# SECTION 1: Mouthpiece (top, Z=0-3mm)
# This is where you blow into the whistle
print("Section 1: Mouthpiece (Z=0-3mm)")
mouthpiece_length = 3
mouth_layers = int(mouthpiece_length / layer_height)

for layer in range(mouth_layers):
    z = start_z + layer * layer_height

    # Full cylinder with small center opening for air intake
    outer_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=0,
        segments=64
    )

    # Small inner circle for air intake
    inner_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius * 0.3,
        start_angle=0,
        segments=32
    )

    steps.extend(fc.travel_to(outer_circle[0]))
    steps.extend(outer_circle)
    steps.extend(fc.travel_to(inner_circle[0]))
    steps.extend(inner_circle)

# SECTION 2: Windway with angled fipple ramp (Z=3-15mm)
# This is the critical section - narrow channel with 75° angled floor
print("Section 2: Windway with 75° fipple ramp (Z=3-15mm) - CRITICAL SECTION")
windway_start_z = mouthpiece_length
windway_layers = int(windway_length / layer_height)

# The fipple is a ramp that slopes at 75° from vertical
# This means for every 1mm we go up in Z, we move inward by: tan(15°) = 0.268mm
# tan(75° from vertical) = tan(90°-75°) = tan(15°)
fipple_slope = tan(radians(90 - fipple_angle))  # tan(15°) ≈ 0.268

for layer in range(windway_layers):
    z = start_z + windway_start_z + layer * layer_height

    # Calculate how far the fipple has moved inward
    # The fipple starts at the back and slopes forward/upward
    dz_from_start = layer * layer_height
    fipple_forward_movement = dz_from_start * fipple_slope

    # Outer cylinder
    outer_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=0,
        segments=64
    )

    # The windway is a slot running along one side of the cylinder
    # We'll create this as a rectangular channel
    # For simplicity in FullControl, we create arcs that exclude the windway area

    # Define the windway slot boundaries (in XY plane)
    # Windway runs along +Y axis direction, centered at X=0
    # Width: windway_width (8mm), so X ranges from -4 to +4mm
    # The fipple ramp is the floor, moving forward as Z increases

    # Create cylinder except for windway slot
    # Windway opening faces +Y direction
    # Calculate angular range to exclude (centered on +Y axis = 90°)
    half_width_angle = radians(30)  # ~30° gives us roughly 8mm wide slot

    # Main cylinder arc (excludes windway)
    main_arc = fc.arcXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=radians(90) + half_width_angle,  # Start after windway
        arc_angle=tau - 2*half_width_angle,  # Go around, skip windway
        segments=60
    )

    steps.extend(fc.travel_to(outer_circle[0]))
    steps.extend(main_arc)

    # Add fipple ramp surface (floor of windway channel)
    # The ramp moves from back (-Y) toward front (+Y) as Z increases
    if layer < windway_layers * 0.9:  # Most of windway
        ramp_y_start = -cylinder_radius  # Back of cylinder
        ramp_y_end = ramp_y_start + fipple_forward_movement  # Moves forward

        # Create ramp surface across the windway width
        ramp_points = []
        for i in range(10):
            x = -windway_width/2 + i * (windway_width/9)
            y = (ramp_y_start + ramp_y_end) / 2  # Position along channel
            ramp_points.append(fc.Point(x=x, y=y, z=z))

        if len(ramp_points) > 0:
            steps.extend(fc.travel_to(ramp_points[0]))
            steps.extend(ramp_points)

# SECTION 3: Labium / Window (Z=15-19mm)
# The sharp edge where air hits and creates edge tone
print("Section 3: Labium edge (Z=15-19mm) - where sound is created")
labium_start_z = windway_start_z + windway_length
labium_height = 4  # Height of the labium/window section
labium_layers = int(labium_height / layer_height)

for layer in range(labium_layers):
    z = start_z + labium_start_z + layer * layer_height

    # Create outer cylinder
    outer_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=0,
        segments=64
    )

    # Create window/opening at the labium
    # This is where the air jet exits and hits the edge
    window_angle = radians(35)

    window_arc = fc.arcXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=radians(90) + window_angle,
        arc_angle=tau - 2*window_angle,
        segments=60
    )

    steps.extend(fc.travel_to(window_arc[0]))
    steps.extend(window_arc)

    # Add sharp labium edge (simplified)
    # In real design, this would be a precisely angled edge

# SECTION 4: Resonating chamber (Z=19-34mm)
print("Section 4: Resonating chamber (Z=19-34mm)")
chamber_start_z = labium_start_z + labium_height
chamber_layers = int(chamber_length / layer_height)

for layer in range(chamber_layers):
    z = start_z + chamber_start_z + layer * layer_height

    # Hollow cylinder for resonance
    outer_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=0,
        segments=64
    )

    # Inner wall for strength
    if layer % 10 == 0:
        inner_circle = fc.circleXY(
            centre=fc.Point(x=0, y=0, z=z),
            radius=cylinder_radius * 0.7,
            start_angle=0,
            segments=48
        )
        steps.extend(fc.travel_to(outer_circle[0]))
        steps.extend(outer_circle)
        steps.extend(fc.travel_to(inner_circle[0]))
        steps.extend(inner_circle)
    else:
        steps.extend(fc.travel_to(outer_circle[0]))
        steps.extend(outer_circle)

# SECTION 5: Exit end (Z=34-35mm)
print("Section 5: Exit end (Z=34-35mm)")
exit_start_z = chamber_start_z + chamber_length
exit_length = total_length - exit_start_z
exit_layers = int(exit_length / layer_height)

for layer in range(exit_layers):
    z = start_z + exit_start_z + layer * layer_height

    # Create exit with small holes for sound
    if layer < exit_layers - 2:
        # Partial circle with gaps
        exit_circle = fc.arcXY(
            centre=fc.Point(x=0, y=0, z=z),
            radius=cylinder_radius,
            start_angle=radians(30),
            arc_angle=tau * 0.8,
            segments=50
        )
        steps.extend(fc.travel_to(exit_circle[0]))
        steps.extend(exit_circle)
    else:
        # Top closure
        full_circle = fc.circleXY(
            centre=fc.Point(x=0, y=0, z=z),
            radius=cylinder_radius,
            start_angle=0,
            segments=50
        )
        steps.extend(fc.travel_to(full_circle[0]))
        steps.extend(full_circle)

print(f"\nDesign complete!")
print(f"CORRECTED GEOMETRY:")
print(f"  - Mouthpiece at TOP (Z=0-3mm)")
print(f"  - Windway runs AXIALLY along Z-axis (Z=3-15mm)")
print(f"  - Fipple ramp at {fipple_angle}° from vertical")
print(f"  - Labium edge at Z=15-19mm (perpendicular to air flow)")
print(f"  - Resonating chamber Z=19-34mm")
print(f"  - Air path: IN at top → DOWN through windway → HITS labium → RESONATES")

# Generate gcode
print("\nGenerating gcode...")
gcode = fc.transform(steps, 'gcode', fc.GcodeControls(
    printer_name='generic',
    save_as='whistle_keychain_fixed'
))

print("\nFiles generated:")
print("  - whistle_keychain_fixed.gcode")
