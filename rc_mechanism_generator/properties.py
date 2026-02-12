from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)


def _poll_any_object(_self, obj):
    return obj is not None


def _poll_empty(_self, obj):
    return obj is not None and obj.type == "EMPTY"


class RCGEN_References(bpy.types.PropertyGroup):
    chassis_obj: PointerProperty(name="Chassis", type=bpy.types.Object, poll=_poll_any_object)
    wheel_l_obj: PointerProperty(name="Wheel L", type=bpy.types.Object, poll=_poll_any_object)
    wheel_r_obj: PointerProperty(name="Wheel R", type=bpy.types.Object, poll=_poll_any_object)
    servo_obj: PointerProperty(name="Servo", type=bpy.types.Object, poll=_poll_any_object)

    tire_l_obj: PointerProperty(name="Tire L", type=bpy.types.Object, poll=_poll_any_object)
    tire_r_obj: PointerProperty(name="Tire R", type=bpy.types.Object, poll=_poll_any_object)
    wheelwell_l_obj: PointerProperty(name="WheelWell L", type=bpy.types.Object, poll=_poll_any_object)
    wheelwell_r_obj: PointerProperty(name="WheelWell R", type=bpy.types.Object, poll=_poll_any_object)
    hub_l_obj: PointerProperty(name="Hub L", type=bpy.types.Object, poll=_poll_any_object)
    hub_r_obj: PointerProperty(name="Hub R", type=bpy.types.Object, poll=_poll_any_object)
    upright_l_obj: PointerProperty(name="Upright L", type=bpy.types.Object, poll=_poll_any_object)
    upright_r_obj: PointerProperty(name="Upright R", type=bpy.types.Object, poll=_poll_any_object)
    servo_horn_obj: PointerProperty(name="Servo Horn", type=bpy.types.Object, poll=_poll_any_object)

    rear_axle_center: PointerProperty(
        name="Rear Axle Center (Optional)",
        type=bpy.types.Object,
        poll=_poll_empty,
        description="Usado para wheelbase automatico no Ackermann",
    )

    lca_in_front_l: PointerProperty(name="LCA In Front L", type=bpy.types.Object, poll=_poll_empty)
    lca_in_rear_l: PointerProperty(name="LCA In Rear L", type=bpy.types.Object, poll=_poll_empty)
    lca_out_l: PointerProperty(name="LCA Out L", type=bpy.types.Object, poll=_poll_empty)
    uca_in_front_l: PointerProperty(name="UCA In Front L", type=bpy.types.Object, poll=_poll_empty)
    uca_in_rear_l: PointerProperty(name="UCA In Rear L", type=bpy.types.Object, poll=_poll_empty)
    uca_out_l: PointerProperty(name="UCA Out L", type=bpy.types.Object, poll=_poll_empty)
    steering_arm_point_l: PointerProperty(name="Steering Arm Point L", type=bpy.types.Object, poll=_poll_empty)

    lca_in_front_r: PointerProperty(name="LCA In Front R", type=bpy.types.Object, poll=_poll_empty)
    lca_in_rear_r: PointerProperty(name="LCA In Rear R", type=bpy.types.Object, poll=_poll_empty)
    lca_out_r: PointerProperty(name="LCA Out R", type=bpy.types.Object, poll=_poll_empty)
    uca_in_front_r: PointerProperty(name="UCA In Front R", type=bpy.types.Object, poll=_poll_empty)
    uca_in_rear_r: PointerProperty(name="UCA In Rear R", type=bpy.types.Object, poll=_poll_empty)
    uca_out_r: PointerProperty(name="UCA Out R", type=bpy.types.Object, poll=_poll_empty)
    steering_arm_point_r: PointerProperty(name="Steering Arm Point R", type=bpy.types.Object, poll=_poll_empty)

    shock_top_l: PointerProperty(name="Shock Top L", type=bpy.types.Object, poll=_poll_empty)
    shock_bottom_l: PointerProperty(name="Shock Bottom L", type=bpy.types.Object, poll=_poll_empty)
    shock_top_r: PointerProperty(name="Shock Top R", type=bpy.types.Object, poll=_poll_empty)
    shock_bottom_r: PointerProperty(name="Shock Bottom R", type=bpy.types.Object, poll=_poll_empty)


class RCGEN_Tolerances(bpy.types.PropertyGroup):
    clearance_sliding_mm: FloatProperty(name="Sliding Clearance (mm)", default=0.25, min=0.0, max=2.0)
    clearance_press_mm: FloatProperty(name="Press Clearance (mm)", default=-0.12, min=-1.0, max=0.5)
    hole_oversize_mm: FloatProperty(name="Hole Oversize (mm)", default=0.2, min=0.0, max=1.0)
    nut_trap_clearance_mm: FloatProperty(name="Nut Trap Clearance (mm)", default=0.2, min=0.0, max=1.0)
    insert_pocket_clearance_mm: FloatProperty(name="Insert Pocket Clearance (mm)", default=0.15, min=0.0, max=1.0)


class RCGEN_Settings(bpy.types.PropertyGroup):
    rcgen_id: StringProperty(name="Set ID", default="RC_SET_01")

    project_scale: FloatProperty(name="Scale", default=1.0, min=0.01, max=10.0)
    wheelbase_mm: FloatProperty(name="Wheelbase (mm)", default=280.0, min=50.0, max=2000.0)
    default_hardware: EnumProperty(
        name="Default Hardware",
        items=(("M2", "M2", ""), ("M3", "M3", ""), ("M4", "M4", "")),
        default="M3",
    )
    print_volume_x_mm: FloatProperty(name="Print Volume X (mm)", default=220.0, min=20.0, max=1000.0)
    print_volume_y_mm: FloatProperty(name="Print Volume Y (mm)", default=220.0, min=20.0, max=1000.0)
    print_volume_z_mm: FloatProperty(name="Print Volume Z (mm)", default=250.0, min=20.0, max=1000.0)
    nozzle_mm: FloatProperty(name="Nozzle (mm)", default=0.4, min=0.1, max=2.0)
    layer_height_mm: FloatProperty(name="Layer Height (mm)", default=0.2, min=0.05, max=1.0)

    wheel_spin_axis: EnumProperty(name="Wheel Spin Axis", items=(("X", "X", ""), ("Y", "Y", ""), ("Z", "Z", "")), default="Y")
    tire_diameter_mm_manual: FloatProperty(name="Tire Diameter Manual (mm)", default=85.0, min=10.0, max=400.0)
    tire_width_mm_manual: FloatProperty(name="Tire Width Manual (mm)", default=30.0, min=5.0, max=200.0)
    servo_axis: EnumProperty(name="Servo Axis", items=(("X", "X", ""), ("Y", "Y", ""), ("Z", "Z", "")), default="Z")
    segments: IntProperty(name="Segments", default=16, min=8, max=64)

    arm_section: EnumProperty(name="Arm Section", items=(("ROUND", "Round", ""), ("RECT", "Rect", ""), ("OVAL", "Oval", "")), default="ROUND")
    arm_rod_diameter_mm: FloatProperty(name="Arm Rod Dia (mm)", default=6.0, min=1.0, max=25.0)
    arm_bushing_diameter_mm: FloatProperty(name="Arm Bushing Dia (mm)", default=8.0, min=1.0, max=30.0)
    min_wall_mm: FloatProperty(name="Min Wall (mm)", default=1.6, min=0.2, max=8.0)
    min_feature_mm: FloatProperty(name="Min Feature (mm)", default=0.5, min=0.05, max=5.0)
    add_ribs: BoolProperty(name="Add Ribs", default=True)
    use_chamfer_radius: BoolProperty(name="Use Chamfer/Radius", default=True)
    generate_knuckle_when_missing: BoolProperty(name="Auto Knuckle", default=True)

    use_boolean_holes: BoolProperty(name="Use Boolean Holes", default=False)
    hole_diameter_mm: FloatProperty(name="Hole Diameter (mm)", default=3.0, min=1.0, max=8.0)

    servo_horn_length_mm: FloatProperty(name="Servo Horn Length (mm)", default=18.0, min=5.0, max=80.0)
    servo_horn_diameter_mm: FloatProperty(name="Servo Horn Hub Dia (mm)", default=8.0, min=2.0, max=30.0)
    tie_rod_diameter_mm: FloatProperty(name="Tie Rod Dia (mm)", default=4.0, min=1.0, max=20.0)
    tie_rod_terminal_diameter_mm: FloatProperty(name="Terminal Dia (mm)", default=6.0, min=2.0, max=20.0)
    ackermann_mode: EnumProperty(name="Ackermann", items=(("MANUAL", "Manual", ""), ("AUTO", "Auto from Rear Axle", "")), default="MANUAL")
    max_steer_angle_deg: FloatProperty(name="Max Steer Angle", default=35.0, min=5.0, max=80.0)
    steering_min_length_mm: FloatProperty(name="Min Tie Rod Length (mm)", default=12.0, min=1.0, max=100.0)

    use_manual_shock_mounts: BoolProperty(name="Use Manual Shock Mounts", default=False)
    bottom_mount_ratio: FloatProperty(name="Bottom Mount Ratio", default=0.45, min=0.2, max=0.8)
    bottom_inboard_offset_mm: FloatProperty(name="Bottom Inboard Offset (mm)", default=3.0, min=-40.0, max=40.0)
    bottom_vertical_offset_mm: FloatProperty(name="Bottom Vertical Offset (mm)", default=2.0, min=-40.0, max=40.0)
    bottom_fore_aft_offset_mm: FloatProperty(name="Bottom Fore/Aft Offset (mm)", default=0.0, min=-40.0, max=40.0)

    top_height_from_wheel_center_mm: FloatProperty(name="Top Height from Wheel Center (mm)", default=55.0, min=-100.0, max=300.0)
    top_fore_aft_offset_mm: FloatProperty(name="Top Fore/Aft Offset (mm)", default=0.0, min=-100.0, max=100.0)
    top_inboard_offset_mm: FloatProperty(name="Top Inboard Offset (mm)", default=20.0, min=-100.0, max=100.0)

    shock_total_length_mm: FloatProperty(name="Shock Length (mm)", default=70.0, min=20.0, max=250.0)
    shock_stroke_mm: FloatProperty(name="Shock Stroke (mm)", default=20.0, min=1.0, max=200.0)
    shock_body_diameter_mm: FloatProperty(name="Shock Body Dia (mm)", default=10.0, min=2.0, max=40.0)
    shock_rod_diameter_mm: FloatProperty(name="Shock Rod Dia (mm)", default=3.0, min=1.0, max=20.0)
    shock_eyelet_diameter_mm: FloatProperty(name="Shock Eyelet Dia (mm)", default=6.0, min=2.0, max=20.0)
    generate_spring: BoolProperty(name="Generate Spring", default=True)
    spring_outer_diameter_mm: FloatProperty(name="Spring OD (mm)", default=14.0, min=4.0, max=60.0)
    spring_wire_diameter_mm: FloatProperty(name="Spring Wire Dia (mm)", default=1.4, min=0.4, max=8.0)
    spring_turns: FloatProperty(name="Spring Turns", default=8.0, min=2.0, max=20.0)
    spring_resolution: IntProperty(name="Spring Resolution", default=8, min=6, max=24)

    overhang_warn_deg: FloatProperty(name="Overhang Warn Deg", default=55.0, min=30.0, max=89.0)
    min_edge_hole_margin_mm: FloatProperty(name="Min Edge-Hole Margin (mm)", default=1.2, min=0.1, max=10.0)
    auto_split_large_parts: BoolProperty(name="Auto Split Oversize", default=True)
    split_key_diameter_mm: FloatProperty(name="Split Key Dia (mm)", default=4.0, min=1.0, max=20.0)
    split_key_profile: EnumProperty(
        name="Split Key Profile",
        items=(("ROUND", "Round", ""), ("HEX", "Hex", ""), ("D", "D-Flat", "")),
        default="HEX",
    )
    split_orientation_bias: EnumProperty(
        name="Split Orientation Bias",
        items=(
            ("AUTO", "Auto", ""),
            ("CHASSIS_FORWARD", "Chassis Forward", ""),
            ("CHASSIS_RIGHT", "Chassis Right", ""),
        ),
        default="AUTO",
    )
    split_clearance_mm: FloatProperty(name="Split Fit Clearance (mm)", default=0.2, min=0.0, max=2.0)
    auto_capture_prefix: StringProperty(name="Auto-Capture Prefix", default="")
    auto_capture_scope: EnumProperty(
        name="Auto-Capture Scope",
        items=(
            ("ALL", "All Objects", ""),
            ("SELECTED", "Selected Collections", ""),
            ("ACTIVE", "Active Collection", ""),
        ),
        default="ALL",
    )

    export_dir: StringProperty(name="Export Dir", subtype="DIR_PATH", default="//rcgen_export")
    export_stl: BoolProperty(name="Export STL", default=True)
    export_3mf: BoolProperty(name="Export 3MF", default=False)

    ui_show_project: BoolProperty(name="Project", default=True)
    ui_show_tolerances: BoolProperty(name="Tolerances", default=True)
    ui_show_refs: BoolProperty(name="Refs", default=True)
    ui_show_hardpoints: BoolProperty(name="Hardpoints", default=True)
    ui_show_suspension: BoolProperty(name="Suspension", default=True)
    ui_show_steering: BoolProperty(name="Steering", default=True)
    ui_show_shocks: BoolProperty(name="Shocks", default=True)
    ui_show_dfm_export: BoolProperty(name="DFM Export", default=True)


classes = (
    RCGEN_References,
    RCGEN_Tolerances,
    RCGEN_Settings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rcgen_refs = PointerProperty(type=RCGEN_References)
    bpy.types.Scene.rcgen_settings = PointerProperty(type=RCGEN_Settings)
    bpy.types.Scene.rcgen_tolerances = PointerProperty(type=RCGEN_Tolerances)


def unregister():
    del bpy.types.Scene.rcgen_tolerances
    del bpy.types.Scene.rcgen_settings
    del bpy.types.Scene.rcgen_refs
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
