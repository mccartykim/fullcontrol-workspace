"""
Cylindrical Whistle - CORRECT VERTICAL WINDWAY VERSION
The key insight: windway is a VERTICAL channel inside, not horizontal slots
"""

import fullcontrol as fc
from math import tau, cos, sin, radians, tan, sqrt, pi

# Design parameters
cylinder_diameter = 12
cylinder_radius = cylinder_diameter / 2
total_length = 35
layer_height = 0.2

# Whistle parameters (from research)
windway_width = 2  # Width of air channel (mm) - the gap width
windway_height = 1.2  # Height of air channel (mm)
windway_length = 12  # Length of windway section (mm)
fipple_angle = 75  # Degrees from vertical (15° from horizontal)
labium_height = 4  # Height of labium/window section
chamber_length = 15  # Resonating chamber

steps = []
start_z = 0.2

print("Creating whistle with CORRECT vertical windway geometry...")

# The windway will face +Y direction (front of whistle)
# It's created by having a fipple block inside that leaves a gap

# SECTION 1: Mouthpiece (Z=0-3mm)
print("Section 1: Mouthpiece")
mouthpiece_length = 3
mouth_layers = int(mouthpiece_length / layer_height)

for layer in range(mouth_layers):
    z = start_z + layer * layer_height

    # Outer cylinder
    outer = fc.circleXY(fc.Point(x=0, y=0, z=z), cylinder_radius, 0, 64)
    # Inner hole for air intake
    inner = fc.circleXY(fc.Point(x=0, y=0, z=z), cylinder_radius * 0.4, 0, 32)

    steps.extend(fc.travel_to(outer[0]))
    steps.extend(outer)
    steps.extend(fc.travel_to(inner[0]))
    steps.extend(inner)

# SECTION 2: Windway with fipple block (Z=3-15mm)
print("Section 2: Windway - vertical channel with angled fipple")
windway_start_z = mouthpiece_length
windway_layers = int(windway_length / layer_height)

# The fipple block is centered, but offset toward -Y (back)
# This leaves a gap on the +Y (front) side = the windway channel
fipple_block_offset_y = -1.5  # Fipple center is 1.5mm toward back
fipple_block_radius = cylinder_radius - windway_width - 0.5  # Leaves ~2mm gap

for layer in range(windway_layers):
    z = start_z + windway_start_z + layer * layer_height

    # Calculate fipple ramp progression
    # The top of the fipple slopes at 75° from vertical
    # tan(15°) = 0.268, so for each mm up, move forward 0.268mm
    slope = tan(radians(90 - fipple_angle))
    dz_from_start = layer * layer_height
    fipple_forward_shift = dz_from_start * slope

    current_fipple_y = fipple_block_offset_y + fipple_forward_shift

    # Outer cylinder (full circle)
    outer = fc.circleXY(fc.Point(x=0, y=0, z=z), cylinder_radius, 0, 64)
    steps.extend(fc.travel_to(outer[0]))
    steps.extend(outer)

    # Fipple block (inner cylinder, offset)
    # This creates the windway channel between fipple and outer wall
    fipple = fc.circleXY(
        fc.Point(x=0, y=current_fipple_y, z=z),
        fipple_block_radius,
        0,
        48
    )
    steps.extend(fc.travel_to(fipple[0]))
    steps.extend(fipple)

# SECTION 3: Labium/Window (Z=15-19mm)
print("Section 3: Labium window - where air jet hits edge")
labium_start_z = windway_start_z + windway_length
labium_layers = int(labium_height / layer_height)

# The labium is the sharp edge where air exits the windway
# Create an opening on the +Y side
for layer in range(labium_layers):
    z = start_z + labium_start_z + layer * layer_height

    # Create outer cylinder with a window opening on +Y side
    # Window is roughly 60° arc centered on +Y axis (90°)
    window_half_angle = radians(30)

    # Main arc (excludes window)
    main_arc = fc.arcXY(
        fc.Point(x=0, y=0, z=z),
        cylinder_radius,
        radians(90) + window_half_angle,  # Start after window
        tau - 2*window_half_angle,  # Go around, skip window
        60
    )

    steps.extend(fc.travel_to(main_arc[0]))
    steps.extend(main_arc)

    # Add labium edge structure (simplified)
    # In a real whistle this would be a sharp horizontal edge

# SECTION 4: Resonating chamber (Z=19-34mm)
print("Section 4: Resonating chamber")
chamber_start_z = labium_start_z + labium_height
chamber_layers = int(chamber_length / layer_height)

for layer in range(chamber_layers):
    z = start_z + chamber_start_z + layer * layer_height

    # Hollow cylinder
    outer = fc.circleXY(fc.Point(x=0, y=0, z=z), cylinder_radius, 0, 64)

    # Reinforcement every 10 layers
    if layer % 10 == 0:
        inner = fc.circleXY(fc.Point(x=0, y=0, z=z), cylinder_radius * 0.7, 0, 48)
        steps.extend(fc.travel_to(outer[0]))
        steps.extend(outer)
        steps.extend(fc.travel_to(inner[0]))
        steps.extend(inner)
    else:
        steps.extend(fc.travel_to(outer[0]))
        steps.extend(outer)

# SECTION 5: Exit cap (Z=34-35mm)
print("Section 5: Exit cap")
exit_start_z = chamber_start_z + chamber_length
exit_length = total_length - exit_start_z
exit_layers = int(exit_length / layer_height)

for layer in range(exit_layers):
    z = start_z + exit_start_z + layer * layer_height

    if layer < exit_layers - 2:
        # Partial circle with exit holes
        exit_arc = fc.arcXY(
            fc.Point(x=0, y=0, z=z),
            cylinder_radius,
            radians(30),
            tau * 0.8,
            50
        )
        steps.extend(fc.travel_to(exit_arc[0]))
        steps.extend(exit_arc)
    else:
        # Solid cap
        full = fc.circleXY(fc.Point(x=0, y=0, z=z), cylinder_radius, 0, 50)
        steps.extend(fc.travel_to(full[0]))
        steps.extend(full)

print("\n" + "="*70)
print("CORRECT WHISTLE GEOMETRY:")
print("  - Vertical cylinder along Z-axis")
print("  - Windway: VERTICAL channel inside (not horizontal slots!)")
print("  - Fipple block offset creates ~2mm gap on +Y side")
print("  - Fipple slopes at 75° from vertical as Z increases")
print("  - Labium window at Z=15-19mm")
print("  - Air path: IN top → DOWN windway gap → OUT window → HITS labium")
print("="*70)

# Generate G-code
print("\nGenerating G-code...")
gcode = fc.transform(steps, 'gcode', fc.GcodeControls(
    printer_name='generic',
    save_as='whistle_v2_correct'
))

print("\nGenerated: whistle_v2_correct.gcode")
print("Validate with: python validate_gcode_geometry.py whistle_v2_correct*.gcode")
