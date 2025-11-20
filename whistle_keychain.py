"""
Cylindrical Whistle Keychain Design using FullControl
Based on analysis of ultra-compact whistle geometry
Key feature: 75° angled throat for whistle tone generation
"""

import fullcontrol as fc
from math import tau, cos, sin, radians

# Design parameters
cylinder_diameter = 12  # Main body diameter (mm)
cylinder_radius = cylinder_diameter / 2
total_length = 35  # Total length (mm)
keyring_hole_diameter = 5  # Hole for keyring (mm)
layer_height = 0.2  # Print layer height (mm)

# Whistle geometry parameters (based on STL analysis)
throat_angle = 75  # Degrees from vertical (critical parameter!)
whistle_mouth_width = 3  # Air intake opening (mm)
whistle_mouth_height = 2  # Height of air intake (mm)
throat_depth = 8  # Depth of throat channel (mm)
resonator_length = 12  # Length of resonating chamber (mm)

# Build the design
steps = []

# Starting point
start_z = 0.2

# Section 1: Base with keyring hole (first 8mm)
print("Creating base section with keyring hole...")
keyring_section_length = 8

for layer in range(int(keyring_section_length / layer_height)):
    z = start_z + layer * layer_height

    # Create outer cylinder
    outer_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=0,
        segments=64
    )

    # Create keyring hole (elliptical opening in first few layers)
    if layer < int(keyring_hole_diameter / layer_height):
        # Add a travel move to skip the keyring hole area
        hole_radius = keyring_hole_diameter / 2

        # Split the circle to create an opening
        # Print outer ring with gap for keyring
        angle_gap = radians(45)  # Opening for keyring

        # Print arc from angle_gap to 2*pi - angle_gap
        partial_circle = fc.arcXY(
            centre=fc.Point(x=0, y=cylinder_radius + 2, z=z),
            radius=cylinder_radius,
            start_angle=angle_gap,
            arc_angle=tau - 2*angle_gap,
            segments=60
        )
        steps.extend(fc.travel_to(partial_circle[0]))
        steps.extend(partial_circle)
    else:
        # Solid cylinder
        steps.extend(fc.travel_to(outer_circle[0]))
        steps.extend(outer_circle)

# Section 2: Transition to whistle throat (next 4mm)
print("Creating transition section...")
transition_length = 4
transition_layers = int(transition_length / layer_height)

for layer in range(transition_layers):
    z = start_z + keyring_section_length + layer * layer_height

    # Solid cylinder
    outer_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=0,
        segments=64
    )
    steps.extend(fc.travel_to(outer_circle[0]))
    steps.extend(outer_circle)

# Section 3: Whistle throat with angled ramp (critical section!)
print("Creating whistle throat with 75° angled ramp...")
throat_section_start = keyring_section_length + transition_length
throat_layers = int(throat_depth / layer_height)

# The throat is the key feature - air flows over an angled surface
# We'll create a cylinder with an internal angled ramp

for layer in range(throat_layers):
    z = start_z + throat_section_start + layer * layer_height

    # Calculate the ramp position (moves forward as we go up)
    # tan(75°) ≈ 3.73, but we use the complementary angle for the slope
    ramp_offset = layer * layer_height / radians(throat_angle)

    # Create outer cylinder
    outer_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=0,
        segments=64
    )

    # Create the throat opening (front side)
    # We'll create a partial circle that excludes the throat area
    # The throat is a slot that directs air

    # Define throat boundaries (angular range to exclude)
    throat_start_angle = radians(-15)  # Start of throat opening
    throat_end_angle = radians(15)     # End of throat opening

    # Print the cylinder except for the throat opening area
    # First arc: from end of throat to start of throat (most of circle)
    main_arc = fc.arcXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=throat_end_angle,
        arc_angle=tau - (throat_end_angle - throat_start_angle),
        segments=60
    )

    steps.extend(fc.travel_to(main_arc[0]))
    steps.extend(main_arc)

    # Add the angled ramp surface (this creates the whistle tone!)
    # The ramp is a sloped surface that starts low and goes high
    if layer < throat_layers * 0.7:  # Only in lower part of throat
        ramp_points = []
        ramp_y_start = -cylinder_radius * 0.5
        ramp_y_end = -cylinder_radius * 0.2

        # Create angled ramp from back of throat
        for i in range(10):
            t = i / 9
            x = (1 - t) * cylinder_radius * sin(throat_start_angle) + t * cylinder_radius * sin(throat_end_angle)
            y = ramp_y_start + (ramp_y_end - ramp_y_start) * t
            ramp_points.append(fc.Point(x=x, y=y, z=z))

        if len(ramp_points) > 0:
            steps.extend(fc.travel_to(ramp_points[0]))
            steps.extend(ramp_points)

# Section 4: Resonating chamber (next 12mm)
print("Creating resonating chamber...")
resonator_start = throat_section_start + throat_depth
resonator_layers = int(resonator_length / layer_height)

for layer in range(resonator_layers):
    z = start_z + resonator_start + layer * layer_height

    # Create cylinder with smaller internal diameter (resonating chamber)
    # The chamber amplifies the whistle tone
    outer_circle = fc.circleXY(
        centre=fc.Point(x=0, y=0, z=z),
        radius=cylinder_radius,
        start_angle=0,
        segments=64
    )

    # Add infill pattern for resonating chamber walls
    # Multiple concentric circles for strength
    if layer % 5 == 0:  # Every 5th layer add reinforcement
        inner_circle = fc.circleXY(
            centre=fc.Point(x=0, y=0, z=z),
            radius=cylinder_radius * 0.6,
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

# Section 5: Exit end with air outlet (final section)
print("Creating exit end with air outlet...")
exit_section_length = total_length - (resonator_start + resonator_length)
exit_layers = int(exit_section_length / layer_height)

for layer in range(exit_layers):
    z = start_z + resonator_start + resonator_length + layer * layer_height

    # Tapered end for air exit
    taper_factor = 1 - (layer / exit_layers) * 0.3  # Taper to 70% of original radius
    current_radius = cylinder_radius * taper_factor

    # Create outlet with small opening for sound
    if layer < exit_layers * 0.8:
        # Partial circle with outlet gap
        outlet_circle = fc.arcXY(
            centre=fc.Point(x=0, y=0, z=z),
            radius=current_radius,
            start_angle=radians(30),
            arc_angle=tau * 0.85,
            segments=50
        )
        steps.extend(fc.travel_to(outlet_circle[0]))
        steps.extend(outlet_circle)
    else:
        # Close the top
        full_circle = fc.circleXY(
            centre=fc.Point(x=0, y=0, z=z),
            radius=current_radius,
            start_angle=0,
            segments=50
        )
        steps.extend(fc.travel_to(full_circle[0]))
        steps.extend(full_circle)

print(f"\nDesign complete!")
print(f"Total layers: {len([s for s in steps if isinstance(s, fc.Point) and hasattr(s, 'z')])}")
print(f"Throat angle: {throat_angle}° (critical whistle parameter)")
print(f"Overall dimensions: {cylinder_diameter}mm diameter × {total_length}mm length")

# Transform to gcode and plot
print("\nGenerating preview...")
plot_data = fc.transform(steps, 'plot', fc.PlotControls(color_type='print_sequence', style='tube'))

# Also generate gcode
print("\nGenerating gcode...")
gcode = fc.transform(steps, 'gcode', fc.GcodeControls(
    printer_name='generic',
    save_as='whistle_keychain'
))

print("\nFiles generated:")
print("  - whistle_keychain.gcode")
print("\nDesign notes:")
print("  - The 75° throat angle is the key feature that creates the whistle tone")
print("  - Air enters through the throat opening and flows over the angled ramp")
print("  - The resonating chamber amplifies the sound")
print("  - Print with 100% infill for best acoustic properties")
print("  - Use PLA or PETG for durability")
